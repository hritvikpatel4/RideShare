#### Important: First create a image of the worker before running the command `docker-compose up --build`

### Done
Remove the master and slave from the docker-compose file and create a worker image and dynamically create the master and slave from the orchestrator.py using the worker image and we have 5 containers running when doing the command `docker-compose up --build`<br/>
autoscaling - count only db read towards the count of the api requests <br/>
kill master <br/>
kill slave <br/>
list workers <br/>
clear db api in the orchestrator <br/>
queues [readQ, writeQ, syncQ, responseQ] <br/>

### TODO
zookeeper and leader election { singly linked list or the one [here](http://zookeeper.apache.org/doc/r3.5.7/recipes.html#sc_leaderElection) } <br/>
sync data to new spawned worker (can be slave or master) using a file/log or a new persistentSyncQ <br/>

### Pending Test
queues [readQ, writeQ, syncQ, responseQ] <br/>
autoscaling - count only db read towards the count of the api requests <br/>

### Tested
Remove the master and slave from the docker-compose file and create a worker image and dynamically create the master and slave from the orchestrator.py using the worker image and we have 5 containers running when doing the command `docker-compose up --build`<br/>
kill master <br/>
kill slave <br/>
list workers <br/>
clear db api in the orchestrator <br/>

### Scripts
Before running any script,<br/>
Run `sudo chmod +x <script_name>.sh` <br/>

Use the below shell scripts in sudo mode as `sudo ./<script_name>.sh` <br/>
Use `docker_clean.sh` to remove all containers, images, volumes. Find the script in the present directory of this README <br/>
Use `docker_list.sh` to list the containers, images, volumes. Find the script in the present directory of this README <br/>
Use `create_image.sh` to create a worker image. This script is in the `orchestrator/worker/` folder <br/>

#### References
https://docker-py.readthedocs.io/en/stable/
https://www.rabbitmq.com/getstarted.html
https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes

