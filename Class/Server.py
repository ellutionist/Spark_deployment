from fabric import Connection
from fabric.runners import Result
from invoke import Responder, UnexpectedExit
from configparser import ConfigParser
import os


class Server:
    __config_path = "./conf/server.ini"
    __profile_path = "./etc/profile"

    def __init__(self, port: int):
        self.__port = port
        self.__config: ConfigParser = self._load_config()
        self.__username: str = self.__config["ssh"].get("username")
        self.__password: str = self.__config["ssh"].get("password")
        self.__monitor_director: str = self.__config["monitor"].get("monitor_directory")

        self.__sudopass = Responder(pattern=r"\[sudo\] password for {username}:".format(username=self.__username),
                                    response="{psw}\n".format(psw=self.__password), )

        self.__conn: Connection = self._connect()

        self._disable_firewall()

        self.__monitor_running: bool = False

    def start_monitor(self, interval: float = 0.5):
        if self.check_monitor():
            self.__conn.run(self.__monitor_director + "/start.sh " + str(interval), hide=True)
            self.__monitor_running = True
            print("Monitor started on port {}.".format(self.__port))

    def stop_monitor(self):
        if self.__monitor_running:
            self.__conn.run(self.__monitor_director + "/stop.sh", hide=True)
            self.__monitor_running = False
            print("Monitor stopped on port {}.".format(self.__port))

    def upload_profile(self):
        """
        Upload the profile that edited locally, if the environmental variables are not correct.
        :return: None
        """
        if not self._check_profile():
            profile_path = self.__profile_path

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(profile_path, '{pwd}/profile'.format(pwd=pwd))
            self.__conn.run('sudo chown root ~/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('sudo chmod 644 ~/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('sudo mv ~/profile /etc/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('source /etc/profile')

            # check the profile again
            if not self._check_profile():
                raise ProfileFailure(self.__port)

    def update_monitor(self):
        if self.check_monitor():
            self.__conn.run("rm -rf " + self.__monitor_director)
            self.install_monitor()

    def install_monitor(self):
        """
        upload the hardware monitor script to server
        :return:
        """
        if not self.check_monitor():
            print("Installing monitor on port {}.".format(self.__port))
            monitor_tar_path = self.__config["monitor"].get("monitor_tar_path")
            self.ensure_directory("~/Downloads")
            self.ensure_directory("~/opt")
            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(monitor_tar_path, "{pwd}/Downloads/monitor.tar".format(pwd=pwd))
            self.__conn.run('cd ~/Downloads && tar -xf ~/Downloads/monitor.tar')
            self.__conn.run('mv ~/Downloads/{folder_name} ~/opt/monitor'
                            .format(folder_name="monitor"), hide=True)

    def install_python3(self):
        """
        If the python3 is not installed yet, then install it.
        :return: None
        :return:
        """
        if not self.check_python3():
            print("Installing python3 on port {port}.".format(port=self.__port))
            try:
                self.__conn.run("sudo -S yum install epel-release -y", watchers=[self.__sudopass], hide=True)
                self.__conn.run("sudo -S yum install https://centos7.iuscommunity.org/ius-release.rpm -y",
                                watchers=[self.__sudopass], hide=True)
            finally:
                self.__conn.run("sudo -S yum install python36u -y", watchers=[self.__sudopass], hide=True)
                self.__conn.run("sudo -S yum install yum install python36u-devel -y", watchers=[self.__sudopass],
                                hide=True)
                self.__conn.run("sudo -S pip3 install psutil", watchers=[self.__sudopass], hide=True)
                if not self.check_python3():
                    raise Python3InstallationFailure(self.__port)

    def install_java(self):
        """
        If the java is not installed yet, then install it.
        :return: None
        """
        if not self.check_java():
            print("Installing Java on port {}.".format(self.__port))

            java_tar_path = self.__config["java"].get("java_tar_path")
            JAVA_HOME = self.__config["java"].get("JAVA_HOME")
            java_folder_name = self.__config["java"].get("java_folder_name")

            self.ensure_directory("~/Downloads")

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(java_tar_path, "{pwd}/Downloads/jdk8.tar".format(pwd=pwd))
            self.__conn.run('cd ~/Downloads && tar -xf ~/Downloads/jdk8.tar')
            self.__conn.run('mv ~/Downloads/{folder_name} {JAVA_HOME}'.format(folder_name=java_folder_name,
                                                                              JAVA_HOME=JAVA_HOME), hide=True)

            # check java again
            if not self.check_java():
                raise JavaInstallationFailure(self.__port)

    def install_spark(self):
        """
        If the Spark is not installed yet, then install it.
        :return: None
        """
        if not self.check_spark():
            print("Installing Spark on port {}.".format(self.__port))
            spark_tar_path = self.__config["spark"].get("spark_tar_path")
            SPARK_HOME = self.__config["spark"].get("SPARK_HOME")
            SPARK_HOME = SPARK_HOME[:-1] if SPARK_HOME[-1] == "/" else SPARK_HOME
            spark_folder_name = self.__config["spark"].get("spark_folder_name")

            self.ensure_directory("~/Downloads")
            install_location = SPARK_HOME[:-len(SPARK_HOME.split("/")[-1])]
            self.ensure_directory(install_location)

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(spark_tar_path, "{pwd}/Downloads/spark.tar".format(pwd=pwd))
            self.__conn.run('cd ~/Downloads && tar -xf ~/Downloads/spark.tar')
            self.__conn.run('mv ~/Downloads/{folder_name} {SPARK_HOME}'.format(folder_name=spark_folder_name,
                                                                               SPARK_HOME=SPARK_HOME), hide=True)

            # check spark again
            if not self.check_spark():
                raise SparkInstallationFailure(self.__port)

    def check_monitor(self) -> bool:
        try:
            self.__conn.run("cd " + self.__monitor_director, hide=True)
            self.__conn.run("cd " + self.__monitor_director + "/logs", hide=True)
            print("Monitor has already been installed on port {}.".format(self.__port))
            return True
        except UnexpectedExit:
            return False

    def check_java(self) -> bool:
        """
        Check whether the java has already been installed
        :return: boolean indicator
        """
        JAVA_HOME = self.__config["java"].get("JAVA_HOME")
        try:
            self.__conn.run("cd {JAVA_HOME}".format(JAVA_HOME=JAVA_HOME), hide=True)  # check the directory of java
            print("Java has already been installed on port {port}.".format(port=self.__port))
            return True
        except UnexpectedExit:
            return False

    def check_spark(self) -> bool:
        """
        Check whether the spark has already been installed
        :return: boolean indicator
        """
        SPARK_HOME = self.__config["spark"].get("SPARK_HOME")
        try:
            self.__conn.run("cd {SPARK_HOME}".format(SPARK_HOME=SPARK_HOME), hide=True)  # check the directory of spark
            print("Spark has already been installed on port {port}.".format(port=self.__port))
            return True
        except UnexpectedExit:
            return False

    def check_python3(self) -> bool:
        """
        Check whether the python3 and psutil library has already been installed
        :return: boolean indicator
        """
        try:
            version = self.__conn.run("python3 --version", hide=True).stdout.strip()
            print("{version} has already been installed.".format(version=version))
            self.__conn.run("pip3 install psutil", hide=True)
            print("psutil has already been installed.")
            return True
        except UnexpectedExit:
            return False

    def ensure_directory(self, path: str):
        """
        Universal method to check whether a director exists and if not, create it (recursively).
        :param path: the specific path
        :return: None
        """
        try:
            self.__conn.run("cd {path}".format(path=path), hide=True)
        except UnexpectedExit:  # alternatively we can simply use "mkdir -p" command.
            path = path[:-1] if path[-1] == "/" else path  # remove the possible "/" at tail
            higher_level = path[:-len(path.split("/")[-1])]
            self.ensure_directory(higher_level)  # recursively call itself to ensure the higher level is created
            self.__conn.run("mkdir {path}".format(path=path))
            print("mkdir {path} on port {port}.".format(path=path, port=self.__port))

    def _connect(self) -> Connection:
        """
        Connect to the server using ssh. Try to log in with public key at first, if fail then set up public key
        authentication.
        :return: fabric.Connection
        """
        private_key_path: str = self.__config["ssh"].get("private_key_path")
        try:  # try to connect with private key first
            conn = Connection(host="localhost", port=self.__port, user=self.__username,
                              connect_kwargs={"key_filename": private_key_path})
            conn.run("pwd", hide=True)
        except Exception:
            conn = Connection(host="localhost", port=self.__port, user=self.__username,
                              connect_kwargs={"password": self.__password})
            conn.run("pwd", hide=True)
            self._set_ssh_authentication(conn)
        print("Connected to port {}.".format(self.__port))

        return conn

    def _set_ssh_authentication(self, conn: Connection):
        """
        Set the ssh to allow public key authentication
        :param conn: ssh connection from fabric
        :return: None
        """
        print("Setting public key authentication on port {port}.".format(port=self.__port))
        public_key_path: str = self.__config["ssh"].get("public_key_path")
        pwd = conn.run("pwd", hide=True).stdout.strip()

        try:
            conn.run("cd ~/.ssh", hide=True)  # check the existence of ~/.ssh/
        except UnexpectedExit:  # if the .ssh does not exist, create it.
            conn.run("mkdir ~/.ssh")
            conn.run("chmod 700 ~/.ssh")
        finally:  # upload the public key and set correct permission
            conn.put(public_key_path, "{pwd}/.ssh/authorized_keys".format(pwd=pwd))
            conn.run("chmod 600 ~/.ssh/authorized_keys")

    def _load_config(self) -> ConfigParser:
        """
        Load the configuration
        :return: configparser.ConfigParser
        """
        config = ConfigParser()
        config.read(self.__config_path)
        return config

    def _check_profile(self) -> bool:
        """
        Check whether the environmental variables are set correctly
        :return: boolean indicator
        """
        JAVA_HOME = self.__config["java"].get("JAVA_HOME")
        SPARK_HOME = self.__config["spark"].get("SPARK_HOME")

        result_java: Result = self.__conn.run("source /etc/profile && echo $JAVA_HOME", hide=True)
        result_spark: Result = self.__conn.run("source /etc/profile && echo $SPARK_HOME", hide=True)

        return result_java.stdout.strip() == JAVA_HOME and result_spark.stdout.strip() == SPARK_HOME

    def _disable_firewall(self):
        self.__conn.run("sudo systemctl disable firewalld", pty=True, watchers=[self.__sudopass], hide=True)
        self.__conn.run("sudo systemctl stop firewalld", pty=True, watchers=[self.__sudopass], hide=True)

    def get_connection(self) -> Connection:
        return self.__conn

    def get_config(self) -> ConfigParser:
        return self.__config


class JavaInstallationFailure(Exception):
    def __init__(self, port: int):
        super(JavaInstallationFailure, self).__init__("Fail to install Java on port {port}.".format(port=port))


class SparkInstallationFailure(Exception):
    def __init__(self, port: int):
        super(SparkInstallationFailure, self).__init__("Fail to install Spark on port {port}.".format(port=port))


class Python3InstallationFailure(Exception):
    def __init__(self, port: int):
        super(Python3InstallationFailure, self).__init__("Fail to install Python3 on port {port}.".format(port=port))


class ProfileFailure(Exception):
    def __init__(self, port: int):
        super(ProfileFailure, self).__init__("The profile does not work on port {port}.".format(port=port))


if __name__ == '__main__':
    slave = Server(10001)
    slave.start_monitor()
    import time
    time.sleep(20)
    slave.stop_monitor()
