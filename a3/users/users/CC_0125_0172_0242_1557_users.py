from flask import Flask, jsonify, request, make_response
import csv, string, collections, datetime
from sqlite3 import connect
import requests

ride_share = Flask(__name__)
ip = "http://0.0.0.0:80"
host = "0.0.0.0"
port = 80

# Function to construct the SQL query
def construct_query(data):
	# data is of JSON type
	# operation is INSERT
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
		SQLQuery = "UPDATE {} SET {} = {} + {};".format(data["tablename"], data["column"], data["column"], data["update_value"])

	# RESET operation for HTTP requests
	elif data["operation"] == "RESET":
		SQLQuery = "UPDATE {} SET {} = {};".format(data["tablename"], data["column"], data["val"])

	return SQLQuery

def increment_counter():
	data = {
		"operation": "UPDATE",
		"tablename": "counter",
		"column": "http_requests_count",
		"update_value": "1"
	}
	requests.post(ip + "/api/v1/db/write", json=data)

# Function to count the number of HTTP requests
@ride_share.route("/api/v1/_count")
def counter():
	data = {
		"operation": "SELECT",
		"columns": "*",
		"tablename": "counter",
		"where": ["1=1"]
	}
	code = requests.post(ip + "/api/v1/db/read", json=data)
	return jsonify(code.json()[0]), 200

# Function to reset the HTTP requests
@ride_share.route("/api/v1/_count", methods=["DELETE"])
def resetcount():
	data = {
		"operation": "RESET",
		"tablename": "counter",
		"column": "http_requests_count",
		"val": "0"
    }
	code = requests.post(ip+"/api/v1/db/write", json=data)
	return {}, code.status_code

# API 1: To add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	increment_counter()
	parameters = request.get_json()	

	if "username" in parameters.keys() and "password" in parameters.keys() and len(parameters["password"]) == 40:
		
		for i in range(len(parameters["password"])):
			if parameters["password"][i] != string.hexdigits:
				answer = make_response("", 400)
		
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "userdetails",
			"where": ["username='{}'".format(parameters["username"])]
		}

		code = requests.post(ip + "/api/v1/db/read", json=data)
		if code.status_code != 400:
			answer =  make_response("", 400)
		
		else:
			data = {
				"operation": "INSERT",
				"tablename": "userdetails",
				"columns": ["username", "password"],
				"values": [parameters["username"], parameters["password"]]
			}
			requests.post(ip + "/api/v1/db/write", json=data)
			answer =  make_response("", 201)
	
	else:
		answer = make_response("", 400)
	return answer

@ride_share.route("/api/v1/users",methods=["GET"])
def list_all():
	increment_counter()
	data = {
		"operation": "SELECT",
		"columns": ["username"],
		"tablename": "userdetails",
		"where":["1=1"]
	}
	r1 = requests.post(ip+"/api/v1/db/read", json=data)
	if not r1.text:
		return make_response("",204)
	else:
		r1=[x[0] for x in r1.json()]
		return make_response(jsonify(r1),200)

# Fallback function for the below route
@ride_share.route("/api/v1/users", methods=["POST", "DELETE"])
def fallback_api_v1_users():
	increment_counter()
	return make_response("", 405)

# API 2: To delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	increment_counter()
	data = {
		"operation": "SELECT",
		"columns": "*",
		"tablename": "userdetails",
		"where": ["username='{}'".format(username)]
	}
	code = requests.post(ip + "/api/v1/db/read", json=data)
	
	if code.status_code != 400:
		data = {
			"operation": "DELETE",
			"tablename": "userdetails",
			"where": ["username='{}'".format(username)]
		}
		requests.post(ip + "/api/v1/db/write", json=data)
		answer = make_response("", 200)
	
	else:
		answer = make_response("", 400)
	return answer

# Fallback function for the below route
@ride_share.route("/api/v1/users/<username>", methods=["GET", "PUT", "POST"])
def fallback_api_v1_username():
	increment_counter()
	return make_response("", 405)

# A function to connect the program to a sqlite3 server
def connectDB(db):
	conn = None
	try:
		conn = connect(db)
	except:
		print("Error in connecting to the database")
	return conn

# API 8: API to modify (insert or delete) values from database
@ride_share.route("/api/v1/db/write", methods=["POST"])
def modifyDB():
	data = request.get_json()
	print(data)

	conn = connectDB('ride_share_user.db')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	
	cursor.execute(SQLQuery)
	conn.commit()
	cursor.close()
	conn.close()
	
	return "",200

#API 9: API to read values from database
@ride_share.route("/api/v1/db/read", methods=["POST"])
def readDB():
	data = request.get_json()
	print(data)

	conn = connectDB('ride_share_user.db')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	
	cursor.execute(SQLQuery)
	rows = []
	for i in cursor.fetchall():
		rows.append(i)
	print("rows:", rows)
	cursor.close()
	conn.close()
	
	if not rows:
		return make_response("", 400)
	return jsonify(rows),200

#API to clear database
@ride_share.route("/api/v1/db/clear",methods=["POST"])
def clear():
	data = {
			"operation": "DELETE",
			"tablename": "userdetails",
			"where": ["1=1"]
		}
	try:
		requests.post(ip+"/api/v1/db/write", json=data)
		return make_response("",200)
	except:
		return make_response("bad request",400)

if __name__ == '__main__':
	ride_share.run(debug=True, port=port, host=host)
