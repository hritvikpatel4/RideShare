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

# --------------------------------------- ORCHESTRATOR CODE INIT ---------------------------------------

logging.basicConfig(filename = 'orchestrator.log', format = '%(asctime)s => %(levelname)s : %(message)s', level = logging.DEBUG)

print("\n\n-----ORCHESTRATOR RUNNING-----\n\n")
logging.info('Orchestrator running')

ip = "http://0.0.0.0:80"
ride_share = Flask(__name__)
port = 80
host = "0.0.0.0"

zk = KazooClient(hosts = "zoo")
zk.start()
logging.info('Zookeeper connection established')

connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'rabbitmq', heartbeat=0))
print("connection:", connection)
channel = connection.channel()
logging.info('RabbitMQ connection established')

# Timer variable for the auto scaling logic
timer = None

# Flag variable to check whether it is the first read db request. This is done so that we can start the timer on the first request
is_first_read_request = True

# Flag variable to check whether the kill was due to scaling down
due_to_scale_down = False

# --------------------------------------- AUTO-SCALING AND SPAWNING OF CONTAINERS ---------------------------------------

# Function to spawn new containers
def spawnContainer():
	client = docker.from_env()
	
	container = client.containers.run('worker', detach = True, network = "orchestrator_default")
	
	time.sleep(10)
	process = container.top()

	cmd1 = "docker cp orchestrator:/orchestrator/comm.txt /tmp/comm.txt"
	os.system(cmd1)
	cmd2 = "docker cp /tmp/comm.txt {}:/worker/comm.txt".format(container.id)
	os.system(cmd2)

	pid = process['Processes'][0][1]
	file = open('pid.txt', 'w')
	file.write(str(pid))
	file.close()
	cmd3 = "docker cp orchestrator:/orchestrator/pid.txt /tmp/pid.txt"
	os.system(cmd3)
	cmd4 = "docker cp /tmp/pid.txt {}:/worker/pid.txt".format(container.id)
	os.system(cmd4)

	print()
	logging.debug('Container spawned with pid: {}'.format(int(process['Processes'][0][1])))
	print("Container spawned with pid: {}".format(int(process['Processes'][0][1])))
	print()
	client.close()

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
	global due_to_scale_down
	while True:
		time.sleep(120)
		count = getHttpCount()
		resetHttpCount()
		
		res = (count // 20) + 1
		print("Need {} slave containers totally".format(res))
		
		client = docker.from_env()
		num = len(client.containers.list()) - 4
		print("We have {} slave containers running currently".format(num))
		
		logging.info('AUTO-SCALING EXECUTION. Thread ran for 2 minutes. Got the count of requests as {}. Reset the requests count. Number of slave containers needed {}. Currently running {}.'.format(count, res, num))

		if num > res:
			logging.debug('Scaling down')
			x = num - res
			while x > 0:
				due_to_scale_down = True
				requests.post(ip + "/api/v1/crash/slave", data={})
				x -= 1
				time.sleep(0.1)
		
		elif num < res:
			logging.debug('Scaling up')
			y = res - num
			while y > 0:
				spawnContainer()
				y -= 1
				time.sleep(0.1)
		
		else:
			pass
		
		due_to_scale_down = False
		client.close()

# Init timer
def fn():
	global timer
	if not timer:
		print("triggered")
		timer = threading.Thread(target=timerfn)
		timer.start()
		logging.info('Timer initialized for auto scaling')

# --------------------------------------- ZOOKEEPER ---------------------------------------

zk.ensure_path('/root')
if zk.exists('/root'):
	zk.delete('/root', recursive = True)
val = "orchestrator"
data = val.encode('utf-8')
zk.create('/root', value = data)
logging.info('Orchestrator added to Znode with value: {}'.format(data.decode('utf-8')))

# --------------------------------------- RABBITMQ ---------------------------------------

# Class which contains methods for the RabbitMQ queues. The initialization and operating the queues
class OrchestratorRpcClient():
	def __init__(self):
		self.connection = pika.BlockingConnection(
			pika.ConnectionParameters(host = 'rabbitmq', heartbeat=0)
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
	logging.debug('Modify DB API invoked')

	data = request.get_json()
	query = construct_query(data)

	f = open('comm.txt', 'a+')   # write the query into the file
	f.write(query + "\n")
	f.close()

	print("write API:", query)

	# Send the query to master
	channel.basic_publish(
		exchange='',
		routing_key = 'writeQ',
		body = query
	)

	logging.debug('Data sent on the writeQ to master. SQL Query sent: {}'.format(query))
	return "", 200

# API 2: API to read values from database
@ride_share.route("/api/v1/db/read", methods = ["POST"])
def readDB():
	logging.debug('Read DB API invoked')
	
	global is_first_read_request
	if is_first_read_request:
		fn()
		is_first_read_request = False
	incrementHttpCount()
	logging.info('Request counter incremented')
	
	data = request.get_json()
	query = construct_query(data)
	logging.debug('SQL Query is: {}'.format(query))
	print("read API:", query)

	# Send the query to slave
	orpc = OrchestratorRpcClient()
	response = orpc.call(query)
	logging.debug('Query sent to slave. Got response: {}'.format(response))
	print("Response_len:", len(response))
	
	if not response:
		return "", 400
	
	return jsonify(response), 200

# API 3: API to clear database
@ride_share.route("/api/v1/db/clear", methods = ["POST"])
def clear():
	logging.debug('Clear DB API invoked')
	
	data_r = {
		"operation": "DELETE",
		"tablename": "ridedetails",
		"where": ["1=1"]
		}
	data_u = {
		"operation": "DELETE",
		"tablename": "userdetails",
		"where": ["1=1"]
	}
	
	try:
		requests.post(ip + "/api/v1/db/write", json = data_r)
		requests.post(ip + "/api/v1/db/write", json = data_u)
		logging.debug('DB cleared')
		return make_response("", 200)
	
	except:
		logging.error('DB clear not performed due to error')
		return make_response("error", 400)

# API 4: API to kill the master
@ride_share.route("/api/v1/crash/master",methods=["POST"])
def kill_master():
	logging.debug('Kill Master API invoked')
	client = docker.from_env()
	containers = client.containers.list()
	
	children = zk.get_children('/root')
	children.sort()
	master_pid = min(children)

	for container in containers:
		process = container.top()
		pid = process['Processes'][0][1]
		if pid == master_pid:
			res = make_response(jsonify(pid), 200)
			container.kill()
			logging.info('Master container killed with pid: {}'.format(pid))
			break
	
	spawnContainer()
	client.close()
	return res

# API 5: API to kill a slave with the highest pid
@ride_share.route("/api/v1/crash/slave",methods=["POST"])
def kill_slave():
	global due_to_scale_down
	logging.debug('Kill Slave API invoked')
	client = docker.from_env()
	containers = client.containers.list()
	
	children = zk.get_children('/root')
	children.sort()
	slave_pid = max(children)
	
	for container in containers:
		process = container.top()
		pid = process['Processes'][0][1]
		if pid == slave_pid:
			res = make_response(jsonify(pid), 200)
			container.kill()
			logging.info('Slave container killed with pid: {}'.format(pid))
			break
	
	if due_to_scale_down == False:
		spawnContainer()
		time.sleep(2)

	client.close()
	return res

# API 6: API to list all the worker containers
@ride_share.route("/api/v1/worker/list",methods=["GET"])
def list_all():
	logging.debug('List Workers API invoked')
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
	logging.info('List Workers API successfully returned')

	res = make_response(jsonify(pids), 200)
	return res

# --------------------------------------- MAIN FUNCTION ---------------------------------------

if __name__ == '__main__':
	spawnContainer() # initial master spawn
	logging.debug('Initial master spawned')
	time.sleep(2)
	spawnContainer() # initial slave spawn
	logging.debug('Initial slave spawned')
	
	logging.info('Flask server running')
	ride_share.run(debug = True, port = port, host = host, use_reloader = False)
