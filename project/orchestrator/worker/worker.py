# --------------------------------------- IMPORT HERE ---------------------------------------

from sqlite3 import connect
import pika
from kazoo.client import KazooClient
import logging
import csv, string, collections, datetime
import docker
import os
import time

# --------------------------------------- WORKER CODE INIT ---------------------------------------

logging.basicConfig(filename = 'worker.log', format = '%(asctime)s => %(levelname)s : %(message)s', level = logging.DEBUG)

zk = KazooClient(hosts="zoo")
zk.start()
logging.info('Zookeeper connection established')

# --------------------------------------- MISC ---------------------------------------

# A function to connect the program to a sqlite server
def connectDB(db):
	conn = None
	try:
		conn = connect(db)
	except:
		print("Error in connecting to the database")
	return conn

# --------------------------------------- MASTER OR SLAVE CONDITIONAL EXECUTION ---------------------------------------

def exec_logic(MASTER):
    # MASTER LOGIC
    if MASTER == '1':
        print("\n\n-----MASTER CODE RUNNING-----\n\n")
        logging.debug('Master running')

        # --------------------------------------- ADD TO ZOOKEEPER ---------------------------------------

        file = open('pid.txt', 'r')
        pid = file.readlines()
        pid = int(pid[0])
        file.close()
        val = "master"
        data = val.encode('utf-8')
        zk.create('/root/'+str(pid), ephemeral = True, value = data)
        logging.info('Master added to Znode with type as ephemeral and value: {}'.format(data.decode('utf-8')))
        data, stat = zk.get('/root')
        children = zk.get_children('/root')
        print("value at /root: {}".format(data.decode('utf-8')))
        print("children of orchestrator: {}".format(children))

        # --------------------------------------- ZOOKEEPER LOGIC ENDS ---------------------------------------

        def service_request_master(ch, method, properties, body):
            print(" [x] Received %s" % body)
            conn = connectDB('ride_share.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = 1")
            body = body.decode("utf-8")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=0))

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
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=0))
        print("Connection: {}".format(connection))
        channel = connection.channel()
        logging.info('RabbitMQ connection established')

        channel.queue_declare(queue='writeQ', exclusive=True)
        #declare sync queue
        channel.exchange_declare(exchange='syncQ', exchange_type='fanout')

        print(' [*] Waiting for messages. To exit press CTRL+C')

        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='writeQ', auto_ack=True, on_message_callback=service_request_master)

        channel.start_consuming()

    # SLAVE LOGIC
    if MASTER == '0':
        print("\n\n-----SLAVE CODE RUNNING-----\n\n")
        logging.debug('Slave running')

        # --------------------------------------- ADD TO ZOOKEEPER ---------------------------------------

        file = open('pid.txt', 'r')
        pid = file.readlines()
        pid = int(pid[0])
        file.close()
        val = "slave"
        data = val.encode('utf-8')
        zk.create('/root/'+str(pid), ephemeral = True, value = data)
        logging.info('Slave added to Znode with type as ephemeral and value: {}'.format(data.decode('utf-8')))
        data, stat = zk.get('/root')
        children = zk.get_children('/root')
        print("value at /root: {}".format(data.decode('utf-8')))
        print("children of orchestrator: {}".format(children))

        # --------------------------------------- ZOOKEEPER LOGIC ENDS ---------------------------------------

        def sync_callback(ch, method, properties, body):
            conn = connectDB('ride_share.db')
            cursor = conn.cursor()                
            body = body.decode("utf-8")
            cursor.execute(body)
            conn.commit()
            cursor.close()
            conn.close()

        def service_request_slave(ch, method, properties, body):
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
                    print("returning 200 success code")
                    ch.basic_publish(exchange='', routing_key=properties.reply_to, properties=pika.BasicProperties(correlation_id = properties.correlation_id), body=str(rows))
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=0))
        print("Connection (slave): {}".format(connection))
        channel = connection.channel()
        logging.info('RabbitMQ connection established')

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

        channel.basic_consume(queue='readQ', on_message_callback=service_request_slave, auto_ack=True)

        channel.start_consuming()

# --------------------------------------- MAIN FUNCTION ---------------------------------------

if __name__ == '__main__':
    MASTER = os.environ.get('MASTER')
    time.sleep(5)
    exec_logic(MASTER)