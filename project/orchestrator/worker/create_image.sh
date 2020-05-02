#!/bin/bash

# Shell script to create a new worker image from the worker dockerfile

sudo docker build -t worker:latest .

sudo docker pull zookeeper

sudo docker pull rabbitmq:3.8.3
