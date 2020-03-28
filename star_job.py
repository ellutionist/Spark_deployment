from Class.Server import Server
from Class.Master import Master
from typing import List


def main():
    job: str = "bin/spark-submit --class org.apache.spark.examples.SparkPi --master spark://192.168.0.200:7077 " \
              "--executor-memory 2g ./examples/jars/spark-examples_2.11-2.4.5.jar 50000"

    with open("conf/master-port", "r") as f:
        master = Master(int(f.read()))

    with open("conf/slave-ports", "r") as f:
        ports: List[int] = [int(line) for line in f.readlines()]
        slaves: List[Server] = []
        for port in ports:
            print("")
            slave = Server(port)
            slaves.append(slave)

    for slave in slaves:
        slave.start_monitor(0.1)

    master.get_connection().run("source /etc/profile && cd $SPARK_HOME && " + job)

    for slave in slaves:
        slave.stop_monitor()


if __name__ == '__main__':
    main()
