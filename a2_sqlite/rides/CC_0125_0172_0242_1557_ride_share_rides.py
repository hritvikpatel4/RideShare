from flask import Flask, jsonify, request, make_response, redirect
import csv, string, collections, datetime
from sqlite3 import connect
import requests

ride_share = Flask(__name__)
ip = "http://0.0.0.0:80"

def get_area_from_number(a):
    with open('AreaNameEnum.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count==0:
                pass
            else:
                if line_count==a:
                    return row[1]
            line_count+=1
        return -1

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

# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	parameters = request.get_json()

	if "created_by" in parameters.keys() and "timestamp" in parameters.keys() and "source" in parameters.keys() and "destination" in parameters.keys() and parameters["source"] != parameters["destination"]:
		data = {
			"operation": "SELECT",
			"columns": "*",
			"tablename": "userdetails",
			"where": ["username='{}'".format(parameters["created_by"])]
		}
		
		code = requests.get("http://54.210.195.176:8080/api/v1/users")

		rows = []
		if code.text:
			rows = code.json()

		if parameters["created_by"] in rows:
			# Checking if the ride is already created.
			data = {
				"operation": "SELECT",
				"tablename": "ridedetails",
				"columns": ["timestamp"],
				"where": ["source='{}'".format(parameters["source"]), "created_by='{}'".format(parameters["created_by"]), "destination='{}'".format(parameters["destination"])]
			}
			code = requests.post(ip + "/api/v1/db/read", json=data)
			
			rows = []
			if code.text:
				rows = code.json()
				
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)
			
			timestamps = [x[0] for x in rows]
			if timestamp in timestamps:
				return make_response("", 400)

			data = {
				"operation": "INSERT",
				"tablename": "ridedetails",
				"columns": ["created_by", "timestamp", "source", "destination"],
				"values": [parameters["created_by"], timestamp, parameters["source"], parameters["destination"]]
			}
			requests.post(ip + "/api/v1/db/write", json=data)
			answer = make_response("", 201)
		else:
			answer = make_response("", 400)
	
	else:
		answer = make_response("", 400)
	return answer

# API 4: List all the upcoming rides for a given source and destination
@ride_share.route('/api/v1/rides', methods=["GET"])
def listRides():
    source=request.args.get('source')
    destination=request.args.get('destination')
    if source and destination:
        now = datetime.datetime.now()
        cur_time = now.strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "operation": "SELECT",
            "columns": "*",
            "tablename": "ridedetails",
            "where": ["source='{}' AND destination='{}'".format(source, destination)]
        }
        rows = requests.post(ip + "/api/v1/db/read", json=data)
        if len(rows.text):
            rows = rows.json()
        else:
            rows = []

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
            answer = make_response("", 204)

    else:
        answer = make_response("", 400)
    return answer

# API 5: List all the details of a given ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["GET"])
def rideDetails(rideId):
	data = {
		"operation": "SELECT",
		"columns": "*",
		"tablename": "ridedetails",
		"where": ["rideid='{}'".format(rideId)]
	}
	r1 = requests.post(ip + "/api/v1/db/read", json=data)

	if r1.status_code != 400:
		r1 = r1.json()
		data = {
			"operation": "SELECT",
			"columns": ["username"],
			"tablename": "rideusers",
			"where": ["rideid='{}'".format(rideId)]
		}
		r2 = requests.post(ip + "/api/v1/db/read", json=data)
		if r2.text:
			r2 = r2.json()
		else:
			r2 = []

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

		if len(r2):
			d['users'] = [x[0] for x in r2]

		return d
	
	else:
		answer = make_response("", 400)
	return answer

@ride_share.route("/api/v1/rides/")
def RideDetails():
	return make_response("", 400)

# API 6: Join an existing ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["POST"])
def joinRide(rideId):
	parameters = request.get_json()

	if "username" in parameters.keys():
		data = {
				"operation": "SELECT",
				"columns": ["rideid"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		rows_ride = requests.post(ip + "/api/v1/db/read", json=data)

		if rows_ride.status_code == 400:
			return make_response("Given ride doesn't exist.", 400)

		rows_user = requests.get("http://54.210.195.176:8080/api/v1/users")

		if rows_user.text and parameters["username"] not in rows_user.json():
			return make_response("Given user doesn't exist.", 400)
		

		data = {
				"operation": "SELECT",
				"columns": ["created_by"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user1 = requests.post(ip + "/api/v1/db/read", json=data).json()
		if parameters["username"] in verify_user1[0][0]:
			return make_response("", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["username"],
				"tablename": "rideusers",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user2 = requests.post(ip + "/api/v1/db/read", json=data)
		if verify_user2.text:
			verify_user2 = verify_user2.json()
			verify_user2 = [x[0] for x in verify_user2]
		else:
			verify_user2 = []
		print("verify user:", verify_user2)
		if parameters["username"] in verify_user2:
			return make_response("", 400)


		data = {
				"operation": "INSERT",
				"tablename": "rideusers",
				"columns": ["rideid", "username"],
				"values": [rideId, parameters["username"]]
		}
		requests.post(ip + "/api/v1/db/write", json=data)
		
		answer = make_response("", 200)
	
	else:
		answer = make_response("", 400)
	return answer

@ride_share.route("/api/v1/rides/", methods=["POST"])
def random_function():
	return make_response("", 400)

# API 7: Delete a ride
@ride_share.route("/api/v1/rides/<rideId>", methods=["DELETE"])
def deleteRide(rideId):
	data = {
			"operation": "SELECT",
			"columns": ["rideid"],
			"tablename": "ridedetails",
			"where": ["rideid={}".format(rideId)]
	}
	rows_ride = requests.post(ip + "/api/v1/db/read", json=data)

	if rows_ride.status_code != 400:
		data = {
			"operation": "DELETE",
			"tablename": "ridedetails",
			"where": ["rideid='{}'".format(rideId)]
		}
		requests.post(ip + "/api/v1/db/write", json=data)
		answer = make_response("", 200)
	
	else:
		answer = make_response("", 400)
	return answer

# A function to connect the program to a mysql server
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

	conn = connectDB('ride_share_rides.db')
	cursor = conn.cursor()
	cursor.execute("PRAGMA foreign_keys = 1")
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

	conn = connectDB('ride_share_rides.db')
	cursor = conn.cursor()
	SQLQuery = construct_query(data)
	print(SQLQuery)
	
	cursor.execute(SQLQuery)
	rows = cursor.fetchall()
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
			"tablename": "ridedetails",
			"where": ["1=1"]
		}
	try:
		requests.post(ip+"/api/v1/db/write", json=data)
		return make_response("",200)
	except:
		return make_response("bad request",400)

if __name__ == '__main__':
	ride_share.run(debug=True, port=80, host="0.0.0.0")
