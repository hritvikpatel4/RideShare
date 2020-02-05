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
                if line_count==a:
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
		rows = readDB(data)
		
		if len(rows):
			answer =  make_response("", 400)
		
		else:
			data = {
				"operation": "INSERT",
				"tablename": "userdetails",
				"columns": ["username", "password"],
				"values": [parameters["username"], parameters["password"]]
			}
			modifyDB(data)
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
	rows = readDB(data)

	if len(rows):
		data = {
			"operation": "DELETE",
			"tablename": "userdetails",
			"where": ["username='{}'".format(username)]
		}
		modifyDB(data)
		answer = make_response("", 200)
	
	else:
		answer = make_response("", 400)
	return answer

@ride_share.route("/api/v1/users/", methods=["DELETE"])
def removeuser():
	return make_response("", 400)

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
		rows = readDB(data)
		
		if len(rows):

			# Checking if the ride is already created.
			data = {
				"operation": "SELECT",
				"tablename": "ridedetails",
				"columns": ["timestamp"],
				"where": ["source='{}'".format(parameters["source"]), "created_by='{}'".format(rows[0][0]), "destination='{}'".format(parameters["destination"])]
			}
			rows = readDB(data)
		
			date, time = parameters["timestamp"].split(":")
			ss, mm, hh = time.split("-")
			dd, mo, yy = date.split("-")
			timestamp = "{}-{}-{} {}:{}:{}".format(yy, mo, dd, hh, mm, ss)

			timestamps = [x[0] for x in rows]
			if rows and timestamp in timestamps:
				return make_response("", 400)
			data = {
				"operation": "INSERT",
				"tablename": "ridedetails",
				"columns": ["created_by", "timestamp", "source", "destination"],
				"values": [parameters["created_by"], timestamp, parameters["source"], parameters["destination"]]
			}
			modifyDB(data)
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
            "where": ["CAST(timestamp as DATETIME)>'{}' AND source='{}' AND destination='{}'".format(cur_time, source, destination)]
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
	r1 = readDB(data)

	if len(r1):
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
		rows_ride = readDB(data)

		if not rows_ride:
			return make_response("", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["username"],
				"tablename": "userdetails",
				"where": ["username='{}'".format(parameters["username"])]
		}
		rows_user = readDB(data)

		if not rows_user:
			return make_response("", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["created_by"],
				"tablename": "ridedetails",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user1 = readDB(data)
		verify_user1 = [x[0] for x in verify_user1]
		if parameters["username"] in verify_user1:
			return make_response("", 400)
		
		data = {
				"operation": "SELECT",
				"columns": ["username"],
				"tablename": "rideusers",
				"where": ["rideid={}".format(rideId)]
		}
		verify_user2 = readDB(data)
		verify_user2 = [x[0] for x in verify_user2]
		if parameters["username"] in verify_user2:
			return make_response("", 400)

		data = {
				"operation": "INSERT",
				"tablename": "rideusers",
				"columns": ["rideid", "username"],
				"values": [rideId, parameters["username"]]
		}
		modifyDB(data)
		
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
	rows_ride = readDB(data)

	if rows_ride:
		data = {
			"operation": "DELETE",
			"tablename": "ridedetails",
			"where": ["rideid='{}'".format(rideId)]
		}
		modifyDB(data)
		answer = make_response("", 200)
	
	else:
		answer = make_response("", 400)
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
@ride_share.route("/api/v1/db/read", methods=["POST"])
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
