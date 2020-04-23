from sqlite3 import connect

conn = connect("ride_share_rides.db")
cursor = conn.cursor()

create = """CREATE TABLE `ridedetails` (
  `rideid` integer PRIMARY KEY AUTOINCREMENT,
  `created_by` text NOT NULL,
  `timestamp` text NOT NULL,
  `source` text NOT NULL,
  `destination` text NOT NULL
)"""
cursor.execute(create)

create = """CREATE TABLE `rideusers` (
  `rideid` integer NOT NULL,
  `username` text,
  FOREIGN KEY(rideid) REFERENCES ridedetails(rideid) ON DELETE CASCADE
)"""
cursor.execute(create)

conn.commit()

cursor.execute("select * from ridedetails")
print("ridedetails")
print(cursor.fetchall())

cursor.execute("select * from rideusers")
print("rideusers")
print(cursor.fetchall())