from fabric import Connection
from fabric.runners import Result
from paramiko import SSHException
from invoke import Responder, UnexpectedExit
from configparser import ConfigParser

class Server:
    __config_path = "./conf/server.ini"

    def __init__(self, port: int):
        self.__port = port
        self.__config: ConfigParser = self._load_config()
        self.__username = self.__config["ssh"].get("username")
        self.__password = self.__config["ssh"].get("password")

        self.__sudopass = Responder(pattern=r"\[sudo\] password for {username}:".format(username=self.__username),
                                    response="{psw}\n".format(psw=self.__password),)

        self.__conn: Connection = self._connect()

    def upload_profile(self):
        """
        Upload the profile that edited locally, if the environmental variables are not correct.
        :return: None
        """
        if not self._check_profile():
            profile_path = self.__config["java"].get("profile_path")

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(profile_path, '{pwd}/profile'.format(pwd=pwd))
            self.__conn.run('sudo chown root ~/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('sudo chmod 644 ~/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('sudo mv ~/profile /etc/profile', pty=True, watchers=[self.__sudopass], hide=True)
            self.__conn.run('source /etc/profile')

            # check the profile again
            if not self._check_profile():
                raise ProfileFailure(self.__port)

    def install_java(self):
        """
        If the java is not installed yet, then install it.
        :return: None
        """
        if not self._check_java():
            print("Installing Java on port {}.".format(self.__port))

            java_tar_path = self.__config["java"].get("java_tar_path")
            JAVA_HOME = self.__config["java"].get("JAVA_HOME")
            java_folder_name = self.__config["java"].get("java_folder_name")

            self._ensure_directory("~/Downloads")

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(java_tar_path, "{pwd}/Downloads/jdk8.tar".format(pwd=pwd))
            self.__conn.run('cd ~/Downloads && tar -xf ~/Downloads/jdk8.tar')
            self.__conn.run('sudo mv ~/Downloads/{folder_name} {JAVA_HOME}'.format(folder_name=java_folder_name,
                                                                                   JAVA_HOME=JAVA_HOME),
                            pty=True, watchers=[self.__sudopass], hide=True)

            # check java again
            if not self._check_java():
                raise JavaInstallationFailure(self.__port)

    def install_spark(self):
        """
        If the Spark is not installed yet, then install it.
        :return: None
        """
        if not self._check_spark():
            print("Installing Spark on port {}.".format(self.__port))
            spark_tar_path = self.__config["spark"].get("spark_tar_path")
            SPARK_HOME = self.__config["spark"].get("SPARK_HOME")
            spark_folder_name = self.__config["spark"].get("spark_folder_name")

            self._ensure_directory("~/Downloads")
            self._ensure_directory("~/opt/module")

            pwd = self.__conn.run("pwd", hide=True).stdout.strip()
            self.__conn.put(spark_tar_path, "{pwd}/Downloads/spark.tar".format(pwd=pwd))
            self.__conn.run('cd ~/Downloads && tar -xf ~/Downloads/spark.tar')
            self.__conn.run('sudo mv ~/Downloads/{folder_name} {SPARK_HOME}'.format(folder_name=spark_folder_name,
                                                                                    SPARK_HOME=SPARK_HOME),
                            pty=True, watchers=[self.__sudopass], hide=True)

            # check spark again
            if not self._check_spark():
                raise SparkInstallationFailure(self.__port)

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

    def _check_java(self) -> bool:
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

    def _check_spark(self) -> bool:
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

    def _ensure_directory(self, path: str):
        """
        Universal method to check whether a director exists and if not, create it (recursively).
        :param path: the specific path
        :return: None
        """
        try:
            self.__conn.run("cd {path}".format(path=path), hide=True)
        except UnexpectedExit:
            path = path[:-1] if path[-1] == "/" else path  # remove the possible "/" at tail
            higher_level = path[:-len(path.split("/")[-1])]
            self._ensure_directory(higher_level)  # recursively call itself to ensure the higher level is created
            self.__conn.run("mkdir {path}".format(path=path))
            print("mkdir {path} on port {port}.".format(path=path, port=self.__port))


class JavaInstallationFailure(Exception):
    def __init__(self, port: int):
        super(JavaInstallationFailure, self).__init__("Fail to install Java on port {port}.".format(port=port))


class SparkInstallationFailure(Exception):
    def __init__(self, port: int):
        super(SparkInstallationFailure, self).__init__("Fail to install Spark on port {port}.".format(port=port))


class ProfileFailure(Exception):
    def __init__(self, port: int):
        super(ProfileFailure, self).__init__("The profile does not work on port {port}.".format(port=port))


if __name__ == '__main__':

    slave2 = Server(10003)
    slave2.upload_profile()
    slave2.install_java()
    slave2.install_spark()
