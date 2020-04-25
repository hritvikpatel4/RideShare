from time import sleep
from flask import Flask, jsonify, request, make_response
import csv, string, collections, datetime
from sqlite3 import connect
import requests

ride_share = Flask(__name__)
ip = "http://34.226.142.9:80"
host = "0.0.0.0"
port = 80

# API 1: To add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	requests.post(ip + "/api/v1/_count")
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
		print("code.status_code =", code.status_code)
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
	requests.post(ip + "/api/v1/_count")
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
	requests.post(ip + "/api/v1/_count")
	return make_response("", 405)

# API 2: To delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	requests.post(ip + "/api/v1/_count")
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
	requests.post(ip + "/api/v1/_count")
	return make_response("", 405)

if __name__ == '__main__':
	ride_share.run(debug=True, port=port, host=host)
