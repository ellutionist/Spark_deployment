# Cluster Manager
Make use of Fabric to deploy and manage the size of a Spark Cluster.

## Preparation

### Port forwarding
We make use of ssh to implement local **port forwarding** to connect to each server in the cluster.
The advantage of doing this is that, when the servers are not reachable from the outside, for example, they are virtual 
machines running in a host machine, and only the host machine can be connected, then the port forwarding will help.

#### Set up port mapping
Edit ./conf/port-map, add port mapping like

    (local port) (remote server address) (the host that is only visable to the remote host) (the port of the aiming host)
  
For example,

    10000 ${remote host} 192.168.122.200 22

As a result, when start port forwarding, the shell script will automatically execute command like

    ssh -Nf -L 10000:192.168.122.200:22 ${remote host}
    
So the port 22 of the aim host will be map to local host's port 10000

It is recommended that you config the way to login in the remote host by editing the file ~/.ssh/config:

    Host $remote_host
    HostName ${the ip address of the remote host or the DNS name of it}
    IdentityFile ${the path to the private key}
    User ${the user name}
    PreferredAuthentications publickey

The port forwarding cannot only be used for SSH connection but also other needs, for example forwarding the Spark web ui:

    8080 $remote_host ${spark master host name} 8080

When the Spark web server is running in the master node, you can access the web page
from **localhost:8080**
    
#### Start port forwarding
Run the shell script

    ./sbin/start-port-forward.sh

#### Stop port forwarding
Run the shell script

    ./sbin/stop-port-forward.sh

### Config

#### server.ini
The following variables should be set correctly:
* ssh
  * private_key_path: path of private key
  * public_key_path: path of public key
  * username: the username of each server (make sure it has sudo privilage)
  * password: the password of username
* java
  * JAVA_HOME: path of Java on server i.e. the environment variable
  * java_folder_name: the folder of java that is extracted from .tar file
  * java_tar_path: the path of .tar file that will be uploaded to server
* spark
  * SPARK_HOME: path of Spark on server i.e. the environment variable
  * spark_folder_name: the folder of Spark that is extracted from .tar file
  * spark_tar_path: the path of .tar file that will be uploaded to server

#### master-port
Write the **port** (not address) of master in it.
For example,

    10000

#### slave-ports
Write the **port** (not address) of slaves in it. 

The address of slaves will be automaticall deployed in master (according to port-map).

For example,

    10001
    10002
    10003

## 1. Setting up or modifying the cluster

### Make sure that
* Ports of master and slaves are set.
* Port mapping is correct.
* Port forwarding is running.
* "server.ini" is configured correctly.
* Install packages i.e. all the tar files are set in ./lib/.

### Then
Run shell script

    sbin/start-setup.sh
    
## 2. Submitting applications to the master

### Make sure that
* The cluster is ready and the Spark Framework is running.
* Ports of master and slaves are set.
* Port mapping is correct.
* Port forwarding is running.

### Then

Submit the application just in the way you do in the master's terminal of Spark 
(but using the special shell script **Spark_deployment/sbin/spark-submit**):

For example

    sbin/spark-submit \
    --master spark://spark-master:7077  \
    --conf spark.cores.max=12  \
    --conf spark.executor.cores=3 \
    --executor-memory 6g  \
    --name kmeans-1gb \
    /home/spark/spark-jars/KMeans.jar  \
    hdfs://spark-master:9000/kmeans/1gb.csv  \
    3 20

The shell script will call the python script to submit the application and monitor the hardware
usage of every node in the cluster.

After the application is completed (or killed), it will collect the monitoring data from nodes and ask you to
name the directory of data files.

For example

    Please input the folder name (default: 2020-06-12 22:13:45):
    {input the directory name or just enter}

The data will be stored in

    Spark_deployment/monitor_data/{directory you named}
