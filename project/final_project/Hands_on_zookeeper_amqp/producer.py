#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

for i in range(15):
    message = "Hello World! " + str(i)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))

    print(" [x] Sent %r" % message)
connection.close()