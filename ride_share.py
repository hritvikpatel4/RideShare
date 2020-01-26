from flask import Flask, jsonify, request, make_response 
import mysql.connector
from mysql.connector import Error

ride_share = Flask(__name__)

#API 1: to add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	#extracting the values from the JSON file sent.
	parameters = request.get_json()
	#checking for a valid json request
	if "username" in parameters.keys() and "password" in parameters.keys():
		
		# Check if username is present in the database.
		query = "SELECT * from UserDetails WHERE username='{}';".format(parameters["username"])
		rows = readDB(query)
		if len(rows):
			answer = make_response("User name already exists", 405)
		
		# All the checks are done and now return a 201 code (record created).
		else:
			query = "INSERT INTO UserDetails VALUES ('{}', '{}');".format(parameters["username"], parameters["password"])
			modifyDB(query)
			answer = make_response("User name inserted into the table", 201)
	
	# if not present, raise a "bad request error". (Error code = 400)
	else:
		answer = make_response("", 400)
	return answer

# API 2: to delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	# Check if username is present in the database.
	query = "SELECT * from UserDetails WHERE username='{}';".format(username)
	rows = readDB(query)
	if len(rows):
		query = "DELETE FROM UserDetails WHERE username='{}';".format(username)
		modifyDB(query)
		answer = make_response("", 200)
		# TODO: call the API to delete the username in the database.
	
	#if not present, this is an invalid request.
	else:
		answer = make_response("", 405)
	return answer

# API 2: to delete an existing user from the database.
@ride_share.route("/api/v1/users/", methods=["DELETE"])
def removeUserFail():
	answer = make_response("", 400)
	return answer

'''
# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	parameters = request.get_json()
	# if "created_by", "timestamp", "source", "destination" in parameters.keys():
	if True:	
		#check db for the username using parameters["created_by"]
		if #exists in db:
			# implement the create ride operation on db
			answer = make_response("", 200)
			return answer

		else:
			# invalid username
			answer = make_response("", 405)
			return answer

	else:
		#wrong api call
		answer = make_response("", 400)
		return answer

# API 4: List all upcoming rides for a given source and destination
@ride_share.route("/api/v1/rides?source=<source>&destination=<destination>", methods=["GET"])
def listRides(source, destination):
	if source and destination:

		if #check in db for valid source and destination:
			# get data from db
			answer = make_response("", 200)
			return answer

		else:
			answer = make_response("", 405)
			return answer

	else:
		answer = make_response("", 400)
		return answer

# API 5: List all the details of a given ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["GET"])
def rideDetails(rideId):
	if rideId:

		if #check rideid in db:
			answer = make_response("", 200)
			return answer

		else:
			answer = make_response("", 405)
			return answer

	else:
		answer = make_response("", 400)
		return answer

# API 6: Join an existing ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["POST"])
def joinRide(rideId):
	parameters = request.get_json()
	if rideId and parameters["username"]:
		
		if #check rideid and the username in the db:
			answer = make_response("", 200)
			return answer

		else:
			answer = make_response("", 405)
			return answer
	
	else:
		answer = make_response("", 400)
		return answer

# API 7: Delete a ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["DELETE"])
def deleteRide(rideId):
	if rideId:

		if #check rideId in db:

			answer = make_response("", 200)
			return answer
		
		else:
			answer = make_response("", 405)
			return answer
	
	else:
		answer = make_response("", 400)
		return answer
'''

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
def modifyDB(SQLQuery):
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	cursor.execute(SQLQuery)
	conn.commit()
	cursor.close()
	conn.close()

#API 9: API to read values from database
@ride_share.route("/api/v1/db/read")
def readDB(SQLQuery):
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	cursor.execute(SQLQuery)
	rows = cursor.fetchall()
	cursor.close()
	conn.close()
	print(rows)
	return rows

if __name__ == '__main__':	
	ride_share.debug=True
	ride_share.run()