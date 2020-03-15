from typing import List
from Server import Server


def main():
    with open("conf/slaves", "r") as f:
        ports: List[int] = [int(line) for line in f.readlines()]

    for port in ports:
        server = Server(port)
        server.upload_profile()
        server.install_java()
        server.install_spark()


if __name__ == '__main__':
    main()
