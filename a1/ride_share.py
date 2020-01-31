#APIs 1, 2, 3, 7, 8, 9 completely tested [JUST NEED TO SEE THE ERROR HANDLING RESPONSE CODES]

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

# API 1: To add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	parameters = request.get_json()	

	if "username" in parameters.keys() and "password" in parameters.keys() and len(parameters["password"]) == 40:
		
		for i in range(len(parameters["password"])):
			if parameters["password"][i] != string.hexdigits:
				answer = make_response("400 Bad Syntax", 400)
		
		query = "SELECT * from userdetails WHERE username='{}';".format(parameters["username"])
		rows = readDB(query)
		
		if len(rows):
			answer = make_response("400 User already exists", 400)
		
		else:
			query = "INSERT INTO userdetails VALUES ('{}', '{}');".format(parameters["username"], parameters["password"])
			modifyDB(query)
			answer = make_response("201 New user added", 201)
	
	else:
		answer = make_response("400 Bad Syntax", 400)
	
	return answer

# API 2: To delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	query = "SELECT * from userdetails WHERE username='{}';".format(username)
	rows = readDB(query)

	if len(rows):
		query = "DELETE FROM userdetails WHERE username='{}';".format(username)
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
		query1 = "SELECT * from userdetails WHERE username='{}';".format(parameters["created_by"])
		rows = readDB(query1)
		
		if len(rows):
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)
			query2 = "INSERT INTO ridedetails (created_by, timestamp, source, destination) VALUES ('{}', '{}', '{}', '{}');".format(parameters["created_by"], timestamp, parameters["source"], parameters["destination"])
			modifyDB(query2)
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
		query = "SELECT * FROM ridedetails WHERE CAST(timestamp as DATETIME)>'{}' AND source='{}' AND destination='{}';".format(cur_time, s, d)
		rows = readDB(query)

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
		query1 = "SELECT * FROM ridedetails WHERE rideid='{}';".format(rideId)
		query2 = "SELECT username FROM rideusers WHERE rideid='{}';".format(rideId)
		r1 = readDB(query1)
		r2 = readDB(query2)
		
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
		query = "SELECT rideid FROM ridedetails WHERE rideid = '{}';".format(rideId)
		rows_ride = readDB(query)
		if not rows_ride:
			return make_response("400 Invalid ride ID", 400)
		
		query = "SELECT username FROM userdetails WHERE username = '{}';".format(parameters["username"])
		rows_user = readDB(query)
		if not rows_user:
			return make_response("400 Invalid username", 400)
		
		query = "SELECT created_by FROM ridedetails WHERE rideid = '{}';".format(rideId)
		verify_user1 = readDB(query)
		verify_user1 = [x[0] for x in verify_user1]
		if parameters["username"] in verify_user1:
			return make_response("400 Cannot join a ride created by yourself", 400)
		
		query = "SELECT username FROM rideusers WHERE rideid = '{}';".format(rideId)
		verify_user2 = readDB(query)
		verify_user2 = [x[0] for x in verify_user2]
		if parameters["username"] in verify_user2:
			return make_response("400 You have already joined the ride", 400)

		query = "INSERT INTO rideusers VALUES ('{}', '{}');".format(rideId, parameters["username"])
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
		query = "SELECT rideid FROM ridedetails WHERE rideid = '{}';".format(rideId)
		rows_ride = readDB(query)

		if rows_ride:
			query = "DELETE FROM ridedetails WHERE rideid = '{}';".format(rideId)
			modifyDB(query)
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
