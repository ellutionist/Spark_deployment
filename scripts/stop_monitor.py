from Class.Server import Server
from Class.Master import Master
from typing import List


def main():
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

    master.stop_monitor()
    for slave in slaves:
        slave.stop_monitor()


if __name__ == '__main__':
    main()
