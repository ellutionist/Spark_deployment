# Spark Deployment
Make use of Fabric to deploy Spark Cluster

## Preparation

### Port forwarding
We make use of ssh to implement local port forwarding to connect to each server in the cluster.

#### Set up port mapping
Edit ./conf/port-map, add port mapping like

    (local port) (server address)
  
For example,

    10000 192.168.0.200

As a result, when start port forwarding, the shell script will automatically execute command like

    ssh -Nf -L 10000:localhost:22 -i ./keys/spark spark@192.168.0.200
    
#### Start port forwarding
Run the shell script

    ./sbin/start-port-forward.sh

#### Stop port forwarding
Run the shell script

    ./sbin/stop-port-forward.sh

### Config

#### server.ini
The variables that should be set correctly:
* ssh
  * private_key_path: path of private key
  * public_key_path: path of public key
  * username: the username of each server (make sure it has sudo authentication)
  * password: the password of username
* java
  * JAVA_HOME: path of Java on server i.e. the environment variable
  * java_folder_name: the folder of java that is extracted from .tar file
  * java_tar_path: the path of .tar file that will be uploaded to server
* spark
  * SPARK_HOME: path of Spark on server i.e. the environment variable
  * spark_folder_name: the folder of Spark that is extracted from .tar file
  * spark_tar_path: the path of .tar file that will be uploaded to server

#### master
Write the **port** (not address) of master in it.
For example,

    10000

#### slaves
Write the **port** (not address) of slaves in it. 

The address of slaves will be automaticall deployed in master (according to port-map).

For example,

    10001
    10002
    10003

## Start Deployment

### Make sure that
* Ports of master and slaves are set.
* Port mapping is correct.
* Port forwarding is running.
* "server.ini" is configured correctly.
* Install packages i.e. two .jar files are set.

### Then

Run the Python script as

    python ./main.py
