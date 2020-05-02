from sqlite3 import connect

# conn = connect("ride_share_rides.db")

conn = connect("rides/ride_share_rides.db")
cursor = conn.cursor()

query = "CREATE TABLE counter (tag VARCHAR(10), count INTEGER)"
cursor.execute(query)

query = "INSERT INTO counter VALUES ('http_requests', 0)"
cursor.execute(query)

query = "INSERT INTO counter VALUES ('rides_count', 0)"
cursor.execute(query)

conn.commit()

conn.close()