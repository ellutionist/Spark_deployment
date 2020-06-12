from Class.Server import Server
from os import remove
from typing import List


class Master(Server):
    def __init__(self, port: int):
        super(Master, self).__init__(port)

    def broad_cast_config(self, slaves: List[Server] = None):
        """
        Send the $SPARK_HOME/conf/spark-env.sh to all the slaves.
        If a list of Server objects is passed, the method will upload the config file directly,
        otherwise, the method will read the slave-ports and connect to servers.
        :return:
        """

        SPARK_HOME: str = self.get_connection().run("source /etc/profile && echo $SPARK_HOME", hide=True).stdout.strip()
        remote_path = "{SPARK_HOME}/conf/spark-env.sh".format(SPARK_HOME=SPARK_HOME)
        self.get_connection().get(remote_path, "./tmp/spark-env.sh")
        if slaves is None:
            ports: List[int] = self._get_slave_ports()
            slaves: List[Server] = [Server(port) for port in ports]

        for slave in slaves:
            slave.get_connection().put("./tmp/spark-env.sh", remote_path)
        remove("./tmp/spark-env.sh")

    def set_slaves(self):
        """
        Create a file named 'slaves' based on './conf/slave-ports' (ports) and './conf/port-map' and upload it to server.
        The address of spark will be configured correctly.
        """
        if self.check_spark():
            port_map: dict = self._get_port_map()
            slave_ports: List[int] = self._get_slave_ports()

            with open("./slaves", "w") as slaves_tmp:
                lines = [port_map[port] + "\n" for port in slave_ports]
                lines.append("\n")
                slaves_tmp.writelines(lines)

            SPARK_HOME = self.get_config()["spark"].get("SPARK_HOME")
            self.get_connection().run("rm {slaves_path}".format(slaves_path="{SPARK_HOME}/conf/slaves".
                                                                format(SPARK_HOME=SPARK_HOME)
                                                                )
                                      )
            self.get_connection().put("./slaves", "{SPARK_HOME}/conf/slaves".format(SPARK_HOME=SPARK_HOME))
            remove("./slaves")

    def set_ssh_config(self):
        """
        In order to enable master-port to log in slaves with private keys, upload the private key first and then put
        correct '~/.ssh/config' on master-port.
        """
        self.ensure_directory("~/.ssh")
        private_key_path = self.get_config()['ssh'].get("private_key_path")

        pwd = self.get_connection().run("pwd", hide=True).stdout.strip()
        self.get_connection().put(private_key_path, "{pwd}/.ssh/spark".format(pwd=pwd))
        self.get_connection().run("chmod 600 " + "{pwd}/.ssh/spark".format(pwd=pwd))

        port_map = self._get_port_map()
        with open("./config", "w") as conf:
            content = ""
            for addr in port_map.values():
                section = "Host {addr}\n" \
                          "HostName {addr}\n" \
                          "PreferredAuthentications publickey\n" \
                          "IdentityFile ~/.ssh/spark\n" \
                          "User spark\n\n".format(addr=addr)
                content = content + section
            conf.write(content)

        self.get_connection().put("./config", "{pwd}/.ssh/config".format(pwd=pwd))
        remove("./config")

    def _get_port_map(self) -> dict:
        """
        Read the port map from './conf/port-map'
        :return: dict in form of {port: address}.
        """
        port_map: dict = {}
        with open("./conf/port-map", "r") as f:
            for line in f.readlines():
                if line != "\n":
                    parts = line.split(" ")
                    if int(parts[-1]) == 22:
                        addr = parts[2]
                        port = int(parts[0])
                        port_map[port] = addr
        return port_map

    def _get_slave_ports(self) -> List[int]:
        """
        Read the port map from './conf/slave-ports'
        :return: list of ports (integer).
        """
        with open("./conf/slave-ports", "r") as slaves:
            slave_ports = [int(port) for port in slaves.readlines()]
        return slave_ports


if __name__ == '__main__':
    master = Master(10000)
    master.broad_cast_config()

