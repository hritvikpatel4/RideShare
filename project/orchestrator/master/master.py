from sqlite3 import connect
import pika
import logging

logging.basicConfig()

# A function to connect the program to a mysql server
def connectDB(db):
	conn = None
	try:
		conn = connect(db)
	except:
		print("Error in connecting to the database")
	return conn

def service_request(ch, method, properties, body):
	print(" [x] Received %s" % body)
	conn = connectDB('ride_share.db')
	cursor = conn.cursor()
	cursor.execute("PRAGMA foreign_keys = 1")
	body = body.decode("utf-8")
	connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rabbitmq')
	)

	#sync after read is acknowledge
	channel = connection.channel()

	channel.basic_publish(exchange='syncQ', routing_key='', body=body)

	print(" [x] Sent %r" % body)

	connection.close()

	cursor.execute(body)
	conn.commit()
	cursor.close()
	conn.close()

	return "", 200

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq')
)

print("Connection: {}".format(connection))

channel = connection.channel()

channel.queue_declare(queue='writeQ', exclusive=True)
#declare sync queue
channel.exchange_declare(exchange='syncQ', exchange_type='fanout')

print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
	queue='writeQ', 
	auto_ack=True,
	on_message_callback=service_request
)

channel.start_consuming()
