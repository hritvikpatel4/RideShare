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
<br/> If you encounter any issues about the scripts, refer to the scripts section below

### Scripts
Before running any script,<br/>
Run `sudo chmod +x <script_name>.sh` <br/>

Use the below shell scripts in sudo mode as `sudo ./<script_name>.sh` if running it locally. If this is being tested on an EC2 instance then use `./<script_name>.sh`<br/>
Use `docker_clean.sh` to remove all containers, images, volumes. Find the script in the present directory of this README <br/>
Use `docker_list.sh` to list the containers, images, volumes. Find the script in the present directory of this README <br/>
Use `create_image.sh` to create a worker image. This script is in the `orchestrator/worker/` folder <br/>

#### References
https://docker-py.readthedocs.io/en/stable/ <br/>
https://www.rabbitmq.com/getstarted.html <br/>
https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes <br/>
