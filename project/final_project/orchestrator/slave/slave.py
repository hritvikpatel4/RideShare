from sqlite3 import connect
import pika
from flask import Flask, jsonify, request, make_response, redirect
import csv, string, collections, datetime

# A function to connect the program to a mysql server
def connectDB(db):
	conn = None
	try:
		conn = connect(db)
	except:
		print("Error in connecting to the database")
	return conn

def service_request(ch, method, properties, body):
		print(" [x] Received %r" % body)
		conn = connectDB('ride_share.db')
		cursor = conn.cursor()
		
		body = body.decode("utf-8")
		
		cursor.execute(body)
		rows = cursor.fetchall()
		cursor.close()
		conn.close()
		
		if len(rows) == 0:
			print("returning 400 error code")
			ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id = properties.correlation_id),
                     body=""
				)
		else:
			print("returning 200 error code")
			ch.basic_publish(exchange='',
						routing_key=properties.reply_to,
						properties=pika.BasicProperties(correlation_id = properties.correlation_id),
						body=str(rows)
				)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

channel.queue_declare(queue='readQ', exclusive=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
	queue='readQ', 
	on_message_callback=service_request,
	auto_ack=True
)

channel.start_consuming()