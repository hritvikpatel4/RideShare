from flask import Flask, jsonify, request, make_response, abort
import mysql.connector, csv, requests
from mysql.connector import Error
import string

ride_share = Flask(__name__)

#function to get area num from csv given an index (area with serial number= input_ number+1)
def get_area_from_number(a):
    with open('AreaNameEnum.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count==0:
                pass
            else:
                if line_count==a+1:
                    return row[1]
            line_count+=1
        return "error"

# API 1: To add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	parameters = request.get_json()	
	if "username" in parameters.keys() and "password" in parameters.keys() and len(parameters["password"]) == 40:
		for i in range(len(parameters["password"])):
			if parameters["password"][i] != string.hexdigits:
				answer = make_response("400 Bad Syntax", 400)
		r1 = requests.post("http://127.0.0.1:5000/api/v1/db/read", data={"column":["username"], "table":["UserDetails"], "arg":["username='"+parameters['username']+"'"]})
		if r1.status_code == 200:
			answer = make_response("400 User already exists", 400)
		else:
			r2 = requests.post("http://127.0.0.1:5000/api/v1/db/write", data={"column":["username", "password"], "table":"UserDetails", "arg":[parameters['username'], parameters['password']]})
			print(r2)
			answer = make_response("201 New user added", 201)
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 2: to delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	#query = "SELECT * from UserDetails WHERE username='{}';".format(username)
	r1 = requests.post("http://127.0.0.1:5000/api/v1/db/read", data={"column":["username"], "table":["UserDetails"], "arg":["username='"+username+"'"]})
	if r1.status_code == 200:
		query = "DELETE FROM UserDetails WHERE username='{}';".format(username)
		deleteDB(query)
		answer = make_response("200 User removed", 200)
	else:
		answer = make_response("400 Invalid user", 400)
	
	return answer

# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	# TODO: parse the source and destination enums
	parameters = request.get_json()
	if "created_by" in parameters.keys() and "timestamp" in parameters.keys() and "source" in parameters.keys() and "destination" in parameters.keys():
		query1 = "SELECT * from UserDetails WHERE username='{}';".format(parameters["created_by"])
		rows = readDB(query1)
		if len(rows):
			# implement the create ride operation on db
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)
			query2 = "INSERT INTO RideDetails (created_by, timestamp, source, destination) VALUES ('{}', '{}', '{}', '{}');".format(parameters["created_by"], timestamp, parameters["source"], parameters["destination"])
			modifyDB(query2)
			answer = make_response("200 Ride successfully created", 200)
		else:
			# invalid username
			answer = make_response("400 Cannot create ride as user does not exist. Please create a user before creating ride", 400)
	else:
		#wrong api call
		answer = make_response("400 Bad Syntax", 400)
	
	return answer
'''
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
'''
# API 5: List all the details of a given ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["GET"])
def rideDetails(rideId):
	if rideId:
		query1 = "SELECT * FROM RideDetails WHERE rideid='{}';".format(rideId)
		query2 = "SELECT username FROM RideUsers WHERE rideid='{}';".format(rideId)
		rows = readDB(query1)
		rows2 = readDB(query2)
		if len(rows):
			temp = rows[1]
			rows[1] = list()
			rows[1].append(temp)
			for i in range(len(rows2)):
				rows[1].append(rows2[i])
			answer = make_response("", 200)
			return jsonify(rows)
		else:
			answer = make_response("400 Bad Request", 400)
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 6: Join an existing ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["POST"])
def joinRide(rideId):
	parameters = request.get_json()
	if rideId and parameters["username"]:
		# Check if both the ride id and username are present in the database
		query = "SELECT RideID FROM RideDetails WHERE RideID = '{}'".format(rideId)
		rows_ride = readDB(query)
		# TODO: Check if the user joining to ride is actually the one who created it.
		if not rows_ride:
			return make_response("Invalid ride ID", 405)
		query = "SELECT username FROM UserDetails WHERE username = '{}'".format(parameters["username"])
		rows_user = readDB(query)
		if not rows_user:
			return make_response("Invalid user name", 405)
		
		# Add the details of the user joining the ride to the RideUsers table
		query = "INSERT INTO RideUsers VALUES ({}, '{}')".format(rideId, parameters["username"])
		modifyDB(query)
		answer = make_response("Joined ride successfully", 200)
		return answer
	
	else:
		answer = make_response("", 400)
		return answer


# API 7: Delete a ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["DELETE"])
def deleteRide(rideId):
	if rideId:
		query = "SELECT RideID FROM RideDetails WHERE RideID = '{}'".format(rideId)
		rows_ride = readDB(query)
		if rows_ride:
			query = "DELETE FROM RideDetails WHERE RideID = '{}'".format(rideId)
			deleteDB(query)
			answer = make_response("Ride deleted", 200)
			return answer
		
		else:
			answer = make_response("Ride doesn't exist!", 405)
			return answer
	
	else:
		answer = make_response("Invalid request", 400)
		return answer

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
def writeDB():
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	cols = request.get_json()["column"]
	table = request.get_json()["table"]
	arg = request.get_json()["arg"]

	SQLQuery = "INSERT INTO " + str(table) + "("
	for i in range(len(cols)):
		if i < len(cols)-1:
			SQLQuery += str(cols[i]) + ","
		if i == len(cols)-1:
			SQLQuery += str(cols[i])
	SQLQuery += ") VALUES ("
	for i in range(len(arg)):
		if i < len(arg)-1:
			SQLQuery += str(arg[i]) + ","
		if i == len(arg)-1:
			SQLQuery += str(arg[i])
	SQLQuery += ");"
	print(SQLQuery)
	cursor.execute(SQLQuery)
	conn.commit()
	cursor.close()
	conn.close()
	answer = make_response("", 200)
	return answer

#API 9: API to read values from database
@ride_share.route("/api/v1/db/read")
def readDB():
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	cols = request.get_json()["column"]
	tables = request.get_json()["table"]
	cond = request.get_json()["arg"]

	SQLQuery = "SELECT "
	for i in range(len(cols)):
		if i < len(cols)-1:
			SQLQuery += str(cols[i]) + ","
		if i == len(cols)-1:
			SQLQuery += str(cols[i])
	SQLQuery += " FROM "
	for i in range(len(tables)):
		if i < len(tables)-1:
			SQLQuery += str(tables[i]) + ","
		if i == len(tables)-1:
			SQLQuery += str(tables[i])
	SQLQuery += " WHERE "
	for i in range(len(cond)):
		if i < len(cond)-1:
			SQLQuery += str(cond[i]) + ","
		if i == len(tables)-1:
			SQLQuery += str(cond[i])
	SQLQuery += ";"
	print(SQLQuery)
	cursor.execute(SQLQuery)
	rows = cursor.fetchall()
	cursor.close()
	conn.close()
	answer = make_response(rows, 200)
	return answer

def deleteDB(SQLQuery):
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	cursor.execute(SQLQuery)
	conn.commit()
	cursor.close()
	conn.close()

if __name__ == '__main__':
	ride_share.run(debug=True)
