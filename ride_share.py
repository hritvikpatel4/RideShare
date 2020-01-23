from flask import Flask, render_template,\
jsonify, request, abort, make_response # Response can be used to modify the header of the response message

ride_share = Flask(__name__)

#API 1: to add a new user to the database.
@ride_share.route("/add_user/v1/users", methods=["PUT"])
def addUser():
	#extracting the values from the JSON file sent.
	parameters = request.get_json()
	print(parameters["username"])
	#checking if the required values are present in the dictionary.
	if "username" in parameters.keys() and "password" in parameters.keys():
		
		# TODO: Modify this to check if username is present in the database.
		if parameters["username"] == "UserName":
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
@ride_share.route("/remove_user/v1/users/<username>", methods=["DELETE"])
def removeUser(username):
	# TODO: modify the below statement to check if the username is in the database.
	if username == "UserName":
		answer = make_response("", 200)
		# TODO: call the API to delete the username in the database.
	
	#if not present, this is an invalid request.
	else:
		answer = make_response("", 405)
	return answer


if __name__ == '__main__':	
	ride_share.debug=True
	ride_share.run()