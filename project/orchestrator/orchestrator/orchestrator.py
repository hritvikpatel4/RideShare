from flask import Flask, jsonify, request, make_response
import requests
import ast
import pika
import uuid
import docker
from kazoo import KazooClient
import logging
import threading
import time
from sqlite3 import connect

logging.basicConfig()

ip = "http://127.0.0.1"
ride_share = Flask(__name__)
port = 80
host = "0.0.0.0"

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
print("connection:", connection)

channel = connection.channel()

zk_con = KazooClient(hosts="zoo")
zk_con.start()

timer = None

def fn():
    global timer
    if not timer:
        timer = threading.Thread(target=timerfn)
        timer.start()

# reset http count code
@ride_share.route("/api/v1/_count", methods=["DELETE"])
def resetHttpCount():
	conn = connect('counter.db')
	cursor = conn.cursor()
	cursor.execute("UPDATE counter SET count = 0;")
	conn.commit()
	cursor.close()
	conn.close()

# increment http count code
@ride_share.route("/api/v1/_count", methods=["POST"])
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

@ride_share.route("/api/v1/_count")
def getHttpCount():
	conn = connect('counter.db')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM counter;")
	count = cursor.fetchone()[0]
	conn.commit()
	cursor.close()
	conn.close()
	return count

def timerfn():
    while True:
		time.sleep(120)
		count = getHttpCount()
		resetHttpCount()
		res = count // 20
		cl = docker.from_env()
		slaves = cl.containers.list()
		for cont in slaves:
			if cont.name == 'master':
				slaves.remove(cont)
				break
		slaves = sorted(slaves, key=lambda x:int(x.id,16), reverse=True)
		if res > len(slaves):
			x = res - len(slaves)
			while x:
				image = slaves[-1].image
				#image = cl.images.get('slaves:latest')
				cl.containers.run(image, 'sleep 25 && python master_slave.py')
				x -= 1
		else:
			x = slaves - res
			killslaves = slaves[:x]
			for cont in killslaves:
				cont.kill()

class OrchestratorRpcClient():

	def __init__(self):
		self.connection = pika.BlockingConnection(
			pika.ConnectionParameters(host='rabbitmq')
		)

		self.channel = self.connection.channel()

		result = self.channel.queue_declare(queue='', exclusive=True)
		self.callback_queue = result.method.queue

		self.channel.basic_consume(
			queue=self.callback_queue,
			on_message_callback=self.on_response,
			auto_ack=True
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
			exchange='',
			routing_key='readQ',
			properties=pika.BasicProperties(
				reply_to=self.callback_queue,
				correlation_id=self.corr_id,
			),
			body=query
		)
		while self.response is None:
			self.connection.process_data_events()
		return self.response

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

# API 8: API to modify (insert or delete) values from database
@ride_share.route("/api/v1/db/write", methods=["POST"])
def modifyDB():
	# Construct the query based on the json file obtained
	data = request.get_json()
	query = construct_query(data)
	print("write API:", query)

	# Insert the producer code here
	# Send the query to master
	channel.basic_publish(
		exchange='',
		routing_key='writeQ',
		body=query
	)
	return "", 200

#API 9: API to read values from database
@ride_share.route("/api/v1/db/read", methods=["POST"])
def readDB():
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

#API to clear database
@ride_share.route("/api/v1/db/clear",methods=["POST"])
def clear():
	data = {
		"operation": "DELETE",
		"tablename": "ridedetails",
		"where": ["1=1"]
		}
	try:
		requests.post(ip+"/api/v1/db/write", json=data)
		return make_response("",200)
	except:
		return make_response("bad request",400)

# Kill master
@ride_share.route("/api/v1/crash/master",methods=["POST"])
def kill_master():
	client=docker.from_env()
	for container in client.containers.list():
		if(container.name=='master'):
			res = make_response(jsonify(container.id),200)
			container.kill()
	return res

# Kill slave
@ride_share.route("/api/v1/crash/slave",methods=["POST"])
def kill_slave(master_pid):
	client=docker.from_env()
	pids=sorted(client.containers.list(),key=lambda x:int(x.id,16),reverse=True)
	if(len(pids)==0):
		return make_response("no containers open",400)
	
	for pid in pids:
		if(pid.name=='slave'):
			res = make_response(jsonify(pid.id),200)
			pid.kill()
			break
	
	return res

@ride_share.route("/api/v1/worker/list",methods=["POST"])
def list_all():
	client=docker.from_env()
	pids=sorted(client.containers.list(),key=lambda x:int(x.id,16))
	pids=[x.id for x in pids]
	return jsonify(pids)

if __name__ == '__main__':
	ride_share.run(debug=True, port=port, host=host)
