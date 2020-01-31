#APIs 1, 2, 3, 5, 6, 7, 8, 9 completely tested [JUST NEED TO SEE THE ERROR HANDLING RESPONSE CODES]

from flask import Flask, jsonify, request, make_response
import mysql.connector, csv, string, collections, datetime
from mysql.connector import Error

ride_share = Flask(__name__)

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
		SQLQuery += " FROM {} WHERE ".format(data["tablename"])
		for condition in data["where"]:
			SQLQuery += condition
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

	if "username" in parameters.keys() and "password" in parameters.keys() and len(parameters["password"]) == 40:
		
		for i in range(len(parameters["password"])):
			if parameters["password"][i] != string.hexdigits:
				answer = make_response("400 Bad Syntax", 400)
		
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "userdetails",
			"where": ["username='{}'".format(parameters["username"])]
		}
		rows = readDB(data)
		
		if len(rows):
			answer = make_response("400 User already exists", 400)
		
		else:
			data = {
				"operation": "INSERT",
				"tablename": "userdetails",
				"columns": ["username", "password"],
				"values": [parameters["username"], parameters["password"]]
			}
			modifyDB(data)
			answer = make_response("201 New user added", 201)
	
	else:
		answer = make_response("400 Bad Syntax", 400)
	
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
	rows = readDB(data)

	if len(rows):
		data = {
			"operation": "DELETE",
			"tablename": "userdetails",
			"where": ["username='{}'".format(username)]
		}
		modifyDB(data)
		answer = make_response("200 User removed", 200)
	
	else:
		answer = make_response("400 Invalid user", 400)
	
	return answer

# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	parameters = request.get_json()

	if "created_by" in parameters.keys() and "timestamp" in parameters.keys() and "source" in parameters.keys() and "destination" in parameters.keys():
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "userdetails",
			"where": ["username='{}'".format(parameters["created_by"])]
		}
		rows = readDB(data)
		
		if len(rows):
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)
			data = {
				"operation": "INSERT",
				"tablename": "ridedetails",
				"columns": ["created_by", "timestamp", "source", "destination"],
				"values": [parameters["created_by"], timestamp, parameters["source"], parameters["destination"]]
			}
			modifyDB(data)
			answer = make_response("200 Ride successfully created", 200)
		
		else:
			answer = make_response("400 Cannot create ride as user does not exist. Please create a user before creating ride", 400)
	
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 4: List all upcoming rides for a given source and destination
@ride_share.route("/api/v1/rides?source=<source>&destination=<destination>", methods=["GET"])
def listRides(source, destination):

	if source and destination:
		s = get_area_from_number(source)
		d = get_area_from_number(destination)
		now = datetime.datetime.now()
		cur_time = now.strftime('%Y-%m-%d %H:%M:%S')
		#query = "SELECT * FROM ridedetails WHERE CAST(timestamp as DATETIME)>'{}' AND source='{}' AND destination='{}';".format(cur_time, s, d)
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "ridedetails",
			"where": ["CAST(timestamp as DATETIME)>'{}' AND source='{}' AND destination='{}'".format(cur_time, s, d)]
		}
		rows = readDB(data)

		if len(rows):
			final=[]
			for row in rows:
				row_dict={}
				row_dict["rideId"]=row[0]
				row_dict["username"]=row[1]
				nts=datetime.datetime.strptime(row[2],"%Y-%m-%d %H:%M:%S")
				nts=nts.strftime("%d-%m-%Y:%S-%M-%H")
				row_dict["timestamp"]=nts
				final.append(row_dict)
			return jsonify(final)

		else:
			answer = make_response("204 No upcoming rides available for given source and destination", 204)

	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 5: List all the details of a given ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["GET"])
def rideDetails(rideId):
	if rideId:
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "ridedetails",
			"where": ["rideid='{}'".format(rideId)]
		}
		r1 = readDB(data)
		data = {
			"operation": "SELECT",
			"columns": ["username"],
			"tablename": "rideusers",
			"where": ["rideid='{}'".format(rideId)]
		}
		r2 = readDB(data)
		
		d = {}
		d["rideId"] = str(r1[0][0])
		d["created_by"] = r1[0][1]
		d["users"] = []
		date, time = str(r1[0][2]).split(" ")
		hh, mm, ss = time.split(":")
		yy, mo, dd = date.split("-")
		d["timestamp"] = "{}-{}-{}:{}-{}-{}".format(dd, mo, yy, ss, mm, hh)
		d["source"] = str(get_area_from_number(int(r1[0][3])))
		d["destination"] = str(get_area_from_number(int(r1[0][4])))
		
		if len(r1):
			
			if len(r2):
				d['users'] = [x[0] for x in r2]
		
			return d
		
		else:
			answer = make_response("400 Bad Request", 400)
	
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 6: Join an existing ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["POST"])
def joinRide(rideId):
	parameters = request.get_json()

	if rideId and parameters["username"] and "username" in parameters.keys():
		data = {
				"operation": "SELECT",
				"columns": ["rideid"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		rows_ride = readDB(data)
		
		if not rows_ride:
			return make_response("Invalid ride ID", 405)
		
		data = {
				"operation": "SELECT",
				"columns": ["username"],
				"tablename": "userdetails",
				"where": ["username='{}'".format(parameters["username"])]
		}
		rows_user = readDB(data)
		if not rows_user:
			return make_response("400 Invalid username", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["created_by"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user1 = readDB(data)
		verify_user1 = [x[0] for x in verify_user1]
		if parameters["username"] in verify_user1:
			return make_response("400 Cannot join a ride created by yourself", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["username"],
				"tablename": "rideusers",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user2 = readDB(data)
		verify_user2 = [x[0] for x in verify_user2]
		if parameters["username"] in verify_user2:
			return make_response("400 You have already joined the ride", 400)

		data = {
				"operation": "INSERT",
				"tablename": "rideusers",
				"columns": ["rideid", "username"],
				"values": [rideId, parameters["username"]]
		}
		modifyDB(data)
		
		answer = make_response("200 Joined ride successfully", 200)
		return answer
	
	else:
		answer = make_response("400 Bad Syntax", 400)
		return answer

# API 7: Delete a ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["DELETE"])
def deleteRide(rideId):
	if rideId:
		data = {
				"operation": "SELECT",
				"columns": ["rideid"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		rows_ride = readDB(data)

		if rows_ride:
			data = {
				"operation": "DELETE",
				"tablename": "ridedetails",
				"where": ["rideid='{}'".format(rideId)]
			}
			modifyDB(data)
			answer = make_response("200 Ride deleted", 200)
			return answer
		
		else:
			answer = make_response("400 Ride doesn't exist!", 400)
			return answer
	
	else:
		answer = make_response("400 Invalid request", 400)
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
def modifyDB(data):
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	cursor.execute(SQLQuery)
	conn.commit()
	cursor.close()
	conn.close()

#API 9: API to read values from database
@ride_share.route("/api/v1/db/read")
def readDB(data):
	conn = connectDB('root', '', 'ride_share')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	cursor.execute(SQLQuery)
	rows = cursor.fetchall()
	cursor.close()
	conn.close()
	return rows

if __name__ == '__main__':
	ride_share.run(debug=True)
