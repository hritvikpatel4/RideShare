Done:
    kill master
    kill slave
    list workers
    all the containers run without errors
    queues [readQ, writeQ, syncQ, responseQ]
    
Todo:
    zookeeper and leader election
    autoscaling - count only db read towards the count of the api requests
    sync data to new spawned worker (can be slave or master) using a file/log
    clear db api in the orchestrator
    
Test:
    kill master
    kill slave
    list workers
    queues [readQ, writeQ, syncQ, responseQ]

references

https://docker-py.readthedocs.io/en/stable/
https://www.rabbitmq.com/getstarted.html
https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes

