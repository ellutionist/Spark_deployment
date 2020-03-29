import os
import signal
import datetime
import psutil
import sys


class HardwareMonitor:
    __interval: float = 0.5
    __pid_file_path = "./logs/pid"

    def __init__(self, interval: float = 0.5):
        signal.signal(signal.SIGTERM, self._terminate)
        print(os.getpid())
        self._write_pid()
        self.__logs = []
        self.__terminate = False
        self.__interval = interval

    def start(self):
        while not self.__terminate:
            try:
                cpu_percent: float = psutil.cpu_percent(self.__interval)
            finally:
                memory_percent: float = psutil.virtual_memory().percent
                self.__logs.append(str(datetime.datetime.now().time()) + "," + str(cpu_percent) + "," +
                                   str(memory_percent) + "\n")
        self._write_logs()

    def _write_pid(self):
        with open(self.__pid_file_path, "w") as pf:
            pf.write(str(os.getpid()))

    def _write_logs(self, file_name="log"):
        with open("./logs/{file_name}.csv".format(file_name=file_name), "w") as log:
            log.writelines(self.__logs)

    def _terminate(self, a, b):
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
