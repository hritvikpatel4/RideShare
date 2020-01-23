from flask import Flask, render_template, jsonify, request, abort, make_response # Response can be used to modify the header of the response message


ride_share = Flask(__name__)

#API 1: to add a new user to the database.
@ride_share.route("/api/v1/users", methods=["PUT"])
def addUser():
	#extracting the values from the JSON file sent.
	parameters = request.get_json()
	#checking for a valid json request
	if "username" in parameters.keys() and "password" in parameters.keys():
		
		# TODO: Modify this to check if username is present in the database.
		if #check in db if the new requested user exists:
			answer = make_response("", 405)
		
		# All the checks are done and now return a 201 code (record created).
		else:
			answer = make_response("", 201)
			# TODO: call the API to insert the value.
	
	# if not present, raise a "bad request error". (Error code = 400)
	else:
		answer = make_response("", 400)
	return answer

# API 2: to delete an existing user from the database.
@ride_share.route("/api/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	# TODO: modify the below statement to check if the username is in the database.
	if username == "UserName":
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

# API 3: create a new ride
@ride_share.route("/api/v1/rides", methods=["POST"])
def newRide():
	parameters = request.get_json()
	if "created_by", "timestamp", "source", "destination" in parameters.keys():
		
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

if __name__ == '__main__':	
	ride_share.debug=True
	ride_share.run()