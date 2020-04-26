#!/bin/bash

# Shell script to create a new worker image from the worker dockerfile

sudo docker build -t worker:latest .
