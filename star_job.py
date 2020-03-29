from Class.Server import Server
from Class.Master import Master
from typing import List
from datetime import datetime
from os import mkdir


def main(job: str):
    # connect to master
    with open("conf/master-port", "r") as f:
        master = Master(int(f.read()))

    # connect to slaves
    with open("conf/slave-ports", "r") as f:
        ports: List[int] = [int(line) for line in f.readlines()]
        slaves: List[Server] = []
        for port in ports:
            print("")
            slave = Server(port)
            slaves.append(slave)

    # start monitor on each slave
    for slave in slaves:
        slave.start_monitor(interval=0.01)

    # send command to master to start the job
    master.get_connection().run("source /etc/profile && cd $SPARK_HOME && " + job)

    # job is done, stop monitors, the slaves will write data to their own disks
    for slave in slaves:
        slave.stop_monitor()

    # collect data to "./monitor_data/"
    current_time = str(datetime.now())[:-7]
    folder_name = input("Please input the folder name (default: {current_time}):\n".format(current_time=current_time))
    folder_name = folder_name if folder_name else current_time
    folder_path = "./monitor_data/" + folder_name
    mkdir(folder_path)
    i: int = 1
    for slave in slaves:
        slave.get_connection().get(slave.get_log_path(), "{folder_path}/slave{i}.csv".format(folder_path=folder_path,
                                                                                             i=i))
        i += 1


if __name__ == '__main__':
    job: str = "bin/spark-submit --class org.apache.spark.examples.SparkPi --master spark://192.168.0.200:7077 " \
               "--executor-memory 2g ./examples/jars/spark-examples_2.11-2.4.5.jar 10000"
    main(job)
