### How to run the project?
Now since you have been redirected from the root folder to the /project folder which is here, do the following steps:
1. `./docker_clean.sh`
2. `cd orchestrator/worker`
3. `./create_image.sh`
4. `cd ../`
5. `docker-compose up -d`
6. `cd ../`
7. `cd users`
8. `docker-compose up -d`
9. `cd ../`
10. `cd rides`
11. `docker-compose up -d`
12. `cd ../`
If you encounter any issues about the scripts, refer to the scripts section below

### Scripts
Before running any script,<br/>
Run `sudo chmod +x <script_name>.sh` <br/>

Use the below shell scripts in sudo mode as `sudo ./<script_name>.sh` if running it locally. If this is being tested on an EC2 instance then use `./<script_name>.sh`<br/>
Use `docker_clean.sh` to remove all containers, images, volumes. Find the script in the present directory of this README <br/>
Use `docker_list.sh` to list the containers, images, volumes. Find the script in the present directory of this README <br/>
Use `create_image.sh` to create a worker image. This script is in the `orchestrator/worker/` folder <br/>

### Tested
Remove the master and slave from the docker-compose file and create a worker image and dynamically create the master and slave from the orchestrator.py using the worker image and we have 5 containers running when doing the command `docker-compose up --build`<br/>
autoscaling - count only db read towards the count of the api requests <br/>
kill master <br/>
kill slave <br/>
list workers <br/>
clear db api in the orchestrator <br/>
queues [readQ, writeQ, syncQ, responseQ] <br/>
sync data to new spawned worker (can be slave or master) using a file/log or a new persistentSyncQ <br/>

### TODO
<br/>

### To be tested
leader election <br/>
zookeeper high availability <br/>

#### References
https://docker-py.readthedocs.io/en/stable/
https://www.rabbitmq.com/getstarted.html
https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes

