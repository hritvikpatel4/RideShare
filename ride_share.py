from flask import Flask, jsonify, request, make_response
import mysql.connector, csv
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
		
		query = "SELECT * from UserDetails WHERE username='{}';".format(parameters["username"])
		rows = readDB(query)
		
		if len(rows):
			answer = make_response("400 User already exists", 400)
		
		else:
			query = "INSERT INTO UserDetails VALUES ('{}', '{}');".format(parameters["username"], parameters["password"])
			modifyDB(query)
			answer = make_response("201 New user added", 201)
	
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 2: To delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	query = "SELECT * from UserDetails WHERE username='{}';".format(username)
	rows = readDB(query)

	if len(rows):
		query = "DELETE FROM UserDetails WHERE username='{}';".format(username)
		modifyDB(query)
		answer = make_response("200 User removed", 200)
	
	else:
		answer = make_response("400 Invalid user", 400)
	
	return answer

# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	parameters = request.get_json()
	if "created_by" in parameters.keys() and "timestamp" in parameters.keys() and "source" in parameters.keys() and "destination" in parameters.keys():
		query1 = "SELECT * from UserDetails WHERE username='{}';".format(parameters["created_by"])
		rows = readDB(query1)
		
		if len(rows):
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)
			query2 = "INSERT INTO RideDetails (created_by, timestamp, source, destination) VALUES ('{}', '{}', '{}', '{}');".format(parameters["created_by"], timestamp, parameters["source"], parameters["destination"])
			modifyDB(query2)
			answer = make_response("200 Ride successfully created", 200)
		
		else:
			answer = make_response("400 Cannot create ride as user does not exist. Please create a user before creating ride", 400)
	
	else:
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
		r1 = readDB(query1)
		r2 = readDB(query2)
		d = {}
		d["rideId"] = str(r1[0])
		d["created_by"] = r1[1]
		d["users"] = []
		d["Timestamp"] = str(r1[2])
		s = get_area_from_number(int(r1[3]))
		d["source"] = str(s)
		d = get_area_from_number(int(r1[4]))
		d["destination"] = str(d)
		
		if len(r1):
			
			if len(r2):
				for i in range(len(r2)):
					d["users"].append(str(r2[i]))
				answer = make_response("", 200)
				return jsonify(d), answer
			
			else:
				answer = make_response("", 200)
				return jsonify(d), answer
		
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
		query = "SELECT rideId FROM RideDetails WHERE RideID = '{}'".format(rideId)
		rows_ride = readDB(query)
		query = "SELECT username FROM UserDetails WHERE username = '{}'".format(parameters["username"])
		rows_user = readDB(query)
		
		# Check if the user joining to ride is actually the one who created it.
		query = "SELECT created_by FROM RideDetails WHERE rideid = '{}';".format(rideId)
		verify_user = readDB(query)
		if parameters["username"] == verify_user:
			return make_response("400 You cannot join a ride which you created", 400)
		
		if not rows_ride:
			return make_response("400 Invalid ride ID", 400)
		
		if not rows_user:
			return make_response("400 Invalid username", 400)
		
		# Add the details of the user joining the ride to the RideUsers table
		query = "INSERT INTO RideUsers VALUES ({}, '{}')".format(rideId, parameters["username"])
		modifyDB(query)
		answer = make_response("200 Joined ride successfully", 200)
		return answer
	
	else:
		answer = make_response("400 Bad Syntax", 400)
		return answer


# API 7: Delete a ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["DELETE"])
def deleteRide(rideId):
	if rideId:
		query = "SELECT RideID FROM RideDetails WHERE RideID = '{}'".format(rideId)
		rows_ride = readDB(query)
		if rows_ride:
			query = "DELETE FROM RideDetails WHERE RideID = '{}'".format(rideId)
			modifyDB(query)
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
	return rows

if __name__ == '__main__':
	ride_share.run(debug=True)
