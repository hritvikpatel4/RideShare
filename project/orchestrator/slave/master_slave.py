from sqlite3 import connect
import pika
from kazoo import KazooClient
import logging
import csv, string, collections, datetime
import docker
import os

logging.basicConfig()

zk_con = KazooClient(hosts="zoo")
zk_con.start()

# A function to connect the program to a sqlite server
def connectDB(db):
	conn = None
	try:
		conn = connect(db)
	except:
		print("Error in connecting to the database")
	return conn

def exec_logic(MASTER):
    # If it is the master container
    if MASTER == '1':
        print("\n\n-----MASTER CODE RUNNING-----\n\n")
        def service_request(ch, method, properties, body):
            print(" [x] Received %s" % body)
            conn = connectDB('ride_share.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = 1")
            body = body.decode("utf-8")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))

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
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))

        print("Connection: {}".format(connection))

        channel = connection.channel()

        channel.queue_declare(queue='writeQ', exclusive=True)
        #declare sync queue
        channel.exchange_declare(exchange='syncQ', exchange_type='fanout')

        print(' [*] Waiting for messages. To exit press CTRL+C')

        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='writeQ', auto_ack=True, on_message_callback=service_request)

        channel.start_consuming()

    # If it is the slave container
    if MASTER == '0':
        print("\n\n-----SLAVE CODE RUNNING-----\n\n")
        def sync_callback(ch, method, properties, body):
            conn = connectDB('ride_share.db')
            cursor = conn.cursor()                
            body = body.decode("utf-8")
            cursor.execute(body)
            conn.commit()
            cursor.close()
            conn.close()

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
                    ch.basic_publish(exchange='', routing_key=properties.reply_to, properties=pika.BasicProperties(correlation_id = properties.correlation_id), body="")
                
                else:
                    print("returning 200 error code")
                    ch.basic_publish(exchange='', routing_key=properties.reply_to, properties=pika.BasicProperties(correlation_id = properties.correlation_id), body=str(rows))
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))

        print("Connection (slave): {}".format(connection))

        channel = connection.channel()

        #sync first
        #declare syn queue
        channel.exchange_declare(exchange='syncQ', exchange_type='fanout')

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange='syncQ', queue=queue_name)

        #read next
        channel.queue_declare(queue='readQ', exclusive=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')

        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue=queue_name, auto_ack=True, on_message_callback=sync_callback)

        channel.basic_consume(queue='readQ', on_message_callback=service_request, auto_ack=True)

        channel.start_consuming()

if __name__ == '__main__':
    MASTER = os.environ.get('MASTER')
    exec_logic(MASTER)