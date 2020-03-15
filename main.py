from typing import List
from Class.Server import Server
from Class.Master import Master


def main():
    with open("conf/master", "r") as f:
        master = Master(int(f.read()))
        master.upload_profile()
        master.install_java()
        master.install_spark()
        master.set_slaves()  # set "$SPARK_HOME/conf/slave-ports" based on local config
        master.set_ssh_config()  # enable master to log in slave-ports with private key

    with open("conf/slave-ports", "r") as f:
        ports: List[int] = [int(line) for line in f.readlines()]

        for port in ports:
            print("")
            slave = Server(port)
            slave.upload_profile()
            slave.install_java()
            slave.install_spark()


if __name__ == '__main__':
    main()
