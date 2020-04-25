### Done
kill master <br/>
kill slave <br/>
list workers <br/>
all the containers run without errors <br/>
queues [readQ, writeQ, syncQ, responseQ]
    
### Todo
Remove the master and slave from the docker-compose file and create a worker image and dynamically create the master and slave from the orchestrator.py using the worker image <br/> 
zookeeper and leader election <br/>
singly linked list or the one [here](http://zookeeper.apache.org/doc/r3.5.7/recipes.html#sc_leaderElection)<br/>
autoscaling - count only db read towards the count of the api requests<br/>
sync data to new spawned worker (can be slave or master) using a file/log<br/>
clear db api in the orchestrator
    
### Test
kill master <br/>
kill slave <br/>
list workers <br/>
queues [readQ, writeQ, syncQ, responseQ]

#### references

https://docker-py.readthedocs.io/en/stable/
https://www.rabbitmq.com/getstarted.html
https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes

