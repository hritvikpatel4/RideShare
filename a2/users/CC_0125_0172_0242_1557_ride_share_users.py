from flask import Flask, jsonify, request, make_response
import mysql.connector, csv, string, collections, datetime
from mysql.connector import Error
import requests

ride_share = Flask(__name__)
ip = "http://127.0.0.1:5000"


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
	return SQLQuery

# API 1: To add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	parameters = request.get_json()	
	print(parameters is None)

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

# API 2: To delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
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

@ride_share.route("/api/v1/users/", methods=["DELETE"])
def removeuser():
	return make_response("", 405)

# A function to connect the program to a mysql server
def connectDB(user, pwd, db):
	conn = None
	try:
		conn = mysql.connector.connect(host='localhost', user=user, database=db, password=pwd)
	except Error as e:
		print(e)
	return conn

# API 8: API to modify (insert or delete) values from database
@ride_share.route("/api/v1/db/write", methods=["POST"])
def modifyDB():
	data = request.get_json()
	print(data)

	conn = connectDB('root', '', 'ride_share')
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

	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	
	cursor.execute(SQLQuery)
	rows = []
	for i in cursor.fetchall():
		rows.append(i)
	cursor.close()
	conn.close()
	
	if not rows:
		return make_response("", 400)
	return jsonify(rows),200

if __name__ == '__main__':
	ride_share.run(debug=True, port=5000)