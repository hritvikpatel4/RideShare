from sqlite3 import connect

conn = connect("users/ride_share_user.db")
cursor = conn.cursor()

query = "CREATE TABLE counter (http_requests_count INTEGER)"
cursor.execute(query)

query = "INSERT INTO counter VALUES (0)"
cursor.execute(query)

conn.commit()

conn.close()