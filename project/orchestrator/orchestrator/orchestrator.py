# --------------------------------------- IMPORT HERE ---------------------------------------

from flask import Flask, jsonify, request, make_response
import requests
import ast
import pika
import uuid
import docker
from kazoo.client import KazooClient
import logging
import threading
import time
import os
from sqlite3 import connect

logging.basicConfig()

# --------------------------------------- ORCHESTRATOR CODE INIT ---------------------------------------

print("\n\n-----ORCHESTRATOR RUNNING-----\n\n")

ip = "http://0.0.0.0:80"
ride_share = Flask(__name__)
port = 80
host = "0.0.0.0"

zk = KazooClient(hosts = "zoo")
zk.start()

zk.ensure_path('/root')
zk.create('/root')

connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'rabbitmq'))
print("connection:", connection)

channel = connection.channel()

timer = None

# --------------------------------------- AUTO SCALING AND SPAWNING OF CONTAINERS ---------------------------------------

# Function to spawn new containers
# TODO: ADD THE CODE TO COPY UPDATED DATA TO THE SLAVE CONTAINER'S DB
def spawn(run_type):
	client = docker.from_env()
	
	if run_type == 1:
		container = client.containers.run('worker', detach = True, environment = ["MASTER="+str(run_type)], name = "master", ports = {'8001':None}, network = "orchestrator_default")
	
	else:
		container = client.containers.run('worker', detach = True, environment = ["MASTER="+str(run_type)], ports = {'8001':None}, network = "orchestrator_default")
	
	time.sleep(10)
	process = container.top()
	print()
	if run_type == 1:
		print("Container spawned is a MASTER")
	else:
		print("Container spawned is a SLAVE")
	print("New container spawned with pid:", int(process['Processes'][0][1]))
	print()
	
	client.close()

# Init timer
def fn():
    global timer
    if not timer:
        timer = threading.Thread(target=timerfn)
        timer.start()

# Function to reset the requests count
def resetHttpCount():
	conn = connect('counter.db')
	cursor = conn.cursor()
	cursor.execute("UPDATE counter SET count = 0;")
	conn.commit()
	cursor.close()
	conn.close()

# Function to increment the requests count
def incrementHttpCount():
	global timer
	if not timer:
		print("trigger")
		fn()
		conn = connect('counter.db')
		cursor = conn.cursor()
		cursor.execute("UPDATE counter SET count = count + 1;")
		conn.commit()
		cursor.close()
		conn.close()

# Function to return the requests count
def getHttpCount():
	conn = connect('counter.db')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM counter;")
	count = cursor.fetchone()[0]
	conn.commit()
	cursor.close()
	conn.close()
	return count

# Timer function which runs as a thread. It also has the implementation of the auto-scaling
def timerfn():
	while True:
		time.sleep(120)
		count = getHttpCount()
		resetHttpCount()
		
		res = (count // 20) + 1
		print("Need {} slave containers now".format(res))
		
		client = docker.from_env()
		num = len(client.containers.list()) - 4
		print("We have {} slave containers now".format(num))
		
		if num > res:
			x = num - res
			while x > 0:
				res = requests.post(ip + "/api/v1/crash/slave", data={})
				x -= 1
				time.sleep(0.25)
		
		else:
			y = res - num
			while y > 0:
				spawn(0)
				y -= 1
		
		client.close()

# --------------------------------------- RABBITMQ ---------------------------------------

# Class which contains methods for the RabbitMQ queues. The initialization and operating the queues
class OrchestratorRpcClient():
	def __init__(self):
		self.connection = pika.BlockingConnection(
			pika.ConnectionParameters(host = 'rabbitmq')
		)

		self.channel = self.connection.channel()

		result = self.channel.queue_declare(queue = '', exclusive = True)
		self.callback_queue = result.method.queue

		self.channel.basic_consume(
			queue = self.callback_queue,
			on_message_callback = self.on_response,
			auto_ack = True
		)

	def on_response(self, ch, method, props, body):
		if self.corr_id == props.correlation_id:
			print("body:", body)
			body = body.decode('utf-8')
			if body:
				self.response = ast.literal_eval(body)
			else:
				self.response = body
			print(self.response)

	def call(self, query):
		self.response = None
		self.corr_id = str(uuid.uuid4())
		self.channel.basic_publish(
			exchange = '',
			routing_key = 'readQ',
			properties=pika.BasicProperties(
				reply_to = self.callback_queue,
				correlation_id = self.corr_id,
			),
			body = query
		)
		while self.response is None:
			self.connection.process_data_events()
		
		return self.response

# --------------------------------------- MISC ---------------------------------------

# Function to construct the SQL query
def construct_query(data):
	# data is of JSON type
	# INSERT operation
	if data["operation"] == "INSERT":
		SQLQuery = "INSERT INTO {} ({}".format(data["tablename"], data["columns"][0])
		for value in range(1, len(data["columns"])):
			SQLQuery += ",{}".format(data["columns"][value])
		SQLQuery += ") VALUES ('{}'".format(data["values"][0])
		for value in range(1, len(data["values"])):
			SQLQuery += ",'{}'".format(data["values"][value])
		SQLQuery += ");"
	
	# SELECT operation
	elif data["operation"] == "SELECT":
		if data["columns"] == "*":
			SQLQuery = "SELECT *"
		else: 
			SQLQuery = "SELECT {}".format(data["columns"][0])
			for value in range(1, len(data["columns"])):
				SQLQuery += ",{}".format(data["columns"][value])
		SQLQuery += " FROM {} WHERE {}".format(data["tablename"], data["where"][0])
		for value in range(1, len(data["where"])):
			SQLQuery += "AND {}".format(data["where"][value])
		SQLQuery += ";"

	# DELETE operation
	elif data["operation"] == "DELETE":
		SQLQuery = "DELETE FROM {}".format(data["tablename"])
		if "where" in data.keys():
			SQLQuery += " WHERE "
			for condition in data["where"]:
				SQLQuery += condition
		SQLQuery += ";"

	# UPDATE operation
	elif data["operation"] == "UPDATE":
		SQLQuery = "UPDATE {} SET {} = {} + {}".format(data["tablename"], data["column"], data["column"], data["update_value"])
		if "where" in data.keys():
			SQLQuery += " WHERE {}".format(data["where"])
		SQLQuery += ";"

	# RESET operation for HTTP requests
	elif data["operation"] == "RESET":
		SQLQuery = "UPDATE {} SET {} = {}".format(data["tablename"], data["column"], data["val"])
		if "where" in data.keys():
			SQLQuery += " WHERE {}".format(data["where"])
		SQLQuery += ";"

	return SQLQuery

# --------------------------------------- API ENDPOINTS ---------------------------------------

# API 1: API to modify (insert or delete) values from database
@ride_share.route("/api/v1/db/write", methods = ["POST"])
def modifyDB():
	# Construct the query based on the json file obtained
	data = request.get_json()
	query = construct_query(data)
	print("write API:", query)

	# Insert the producer code here
	# Send the query to master
	channel.basic_publish(
		exchange='',
		routing_key = 'writeQ',
		body = query
	)
	return "", 200

# API 2: API to read values from database
@ride_share.route("/api/v1/db/read", methods = ["POST"])
def readDB():
	incrementHttpCount()
	data = request.get_json()
	query = construct_query(data)
	print("read API:", query)

	# Send the query to slave
	orpc = OrchestratorRpcClient()
	response = orpc.call(query)
	print("Response_len:", len(response))
	
	if not response:
		return "", 400
	
	return jsonify(response), 200

# API 3: API to clear database
@ride_share.route("/api/v1/db/clear", methods = ["POST"])
def clear():
	data = {
		"operation": "DELETE",
		"tablename": "ridedetails",
		"where": ["1=1"]
		}
	try:
		requests.post(ip + "/api/v1/db/write", json = data)
		return make_response("", 200)
	
	except:
		return make_response("error", 400)

# API 4: API to kill the master
@ride_share.route("/api/v1/crash/master",methods=["POST"])
def kill_master():
	client = docker.from_env()
	containers = client.containers.list()
	
	allowed = ['master']

	for container in containers:
		if container.name in allowed:
			process = container.top()
			pid = process['Processes'][0][1]
			res = make_response(jsonify(pid),200)
			container.kill()
	
	client.close()
	return res

# API 5: API to kill a slave with the highest pid
@ride_share.route("/api/v1/crash/slave",methods=["POST"])
def kill_slave():
	client = docker.from_env()
	containers = client.containers.list()
	
	pids = []
	rejected = ['zoo', 'rabbitmq', 'orchestrator', 'master']
	
	for container in containers:
		if container.name not in rejected:
			process = container.top()
			pids.append(int(process['Processes'][0][1]))
	
	pids.sort()
	
	if len(pids) == 0:
		res = make_response("no slave left to kill", 400)
	
	else:
		for container in containers:
			if container.name not in rejected:
				process = container.top()
				pid = process['Processes'][0][1]
				
				if int(pid) == pids[-1]:
					res = make_response(jsonify(pid),200)
					container.kill()
					break
	
	client.close()
	return res

# API 6: API to list all the worker containers
@ride_share.route("/api/v1/worker/list",methods=["POST"])
def list_all():
	client = docker.from_env()
	containers = client.containers.list()
	
	pids = []
	rejected = ['zoo', 'rabbitmq', 'orchestrator']
	
	for container in containers:
		if container.name not in rejected:
			process = container.top()
			pids.append(int(process['Processes'][0][1]))
	
	pids.sort()
	client.close()

	res = make_response(jsonify(pids), 200)
	return res

# --------------------------------------- MAIN FUNCTION ---------------------------------------

if __name__ == '__main__':
	spawn(1) # initial master spawn
	time.sleep(5)
	spawn(0) # initial slave spawn
	
	ride_share.run(debug = True, port = port, host = host)
