import os
import signal
import datetime
import psutil
import sys


class HardwareMonitor:
    __interval: float = 0.5
    __pid_file_path = "./logs/pid"

    def __init__(self, interval: float = 0.5):
        signal.signal(signal.SIGTERM, self._terminate)  # connect the signal to the slot "terminate"
        print(os.getpid())
        self._write_pid()
        self.__logs = []  # the array containing monitor data "time, cpu usage, memory usage"
        self.__terminate = False  # boolean indicator to decide if the monitor should keep running
        self.__interval = interval  # the time interval of monitoring

    def start(self):
        """
        start the monitor and keep running until it receives the SIGTERM signal.
        :return: None
        """
        while not self.__terminate:
            try:
                cpu_percent: float = psutil.cpu_percent(self.__interval)
            finally:
                memory_percent: float = psutil.virtual_memory().percent
                self.__logs.append(str(datetime.datetime.now().time()) + "," + str(cpu_percent) + "," +
                                   str(memory_percent) + "\n")
        self._write_logs()

    def _write_pid(self):
        """
        write the pid to logs/pid so that when terminating the system knows which process to send the signal
        :return:
        """
        with open(self.__pid_file_path, "w") as pf:
            pf.write(str(os.getpid()))

    def _write_logs(self, file_name="log"):
        """
        write the data to local disk
        :param file_name:
        :return:
        """
        with open("./logs/{file_name}.csv".format(file_name=file_name), "w") as log:
            log.writelines(self.__logs)

    def _terminate(self, a, b):
        """
        once receive the signal, change the boolean indicator to false so that the process will stop
        :param a: no use
        :param b: no use
        :return:
        """
        self.__terminate = True


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        print(args[1])
        interval = float(args[1])
        hardware_monitor = HardwareMonitor(interval)
    else:
        hardware_monitor = HardwareMonitor()

    hardware_monitor.start()
