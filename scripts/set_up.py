from typing import List
from Class.Server import Server
from Class.Master import Master
import os


def main():
    # os.system("./sbin/stop-port-forward.sh")
    # os.system("./sbin/start-port-forward.sh")

    with open("conf/master-port", "r") as f:
        master = Master(int(f.read()))
        master.upload_profile()
        master.install_python3()
        master.install_java()
        # master.install_scala()
        master.install_spark()
        master.install_monitor(forth=False)
        master.set_slaves()  # set "$SPARK_HOME/conf/slaves" based on local config
        master.set_ssh_config()  # enable master to log in slaves with private key

    with open("conf/slave-ports", "r") as f:
        ports: List[int] = [int(line) for line in f.readlines()]
        slaves: List[Server] = []
        for port in ports:
            print("")
            slave = Server(port)
            slaves.append(slave)
            slave.install_python3()
            slave.upload_profile()
            slave.install_java()
            slave.install_scala()
            slave.install_spark()
            slave.install_python3()
            slave.install_monitor(forth=False)

    # master.broad_cast_config(slaves)


if __name__ == '__main__':
    main()
