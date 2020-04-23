from sqlite3 import connect

conn = connect("ride_share_rides.db")
cursor = conn.cursor()
cursor.execute("select * from rideusers")

print("Checking:")
print(cursor.fetchall())