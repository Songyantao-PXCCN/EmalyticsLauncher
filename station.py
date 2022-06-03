import os
import subprocess
import threading
import time
import setting


class Station(threading.Thread):
    STATION_EXE = setting.CONF.get("platform",'station_exe_path')

    def __init__(self, stationName: str, messageConsumer, quitNotifier, exceptionNotifier):
        super().__init__(name=stationName)
        self._stationName = stationName
        self._proc = None
        self._messageConsumer = messageConsumer
        self._isRunning = False
        self._quitNotifier = quitNotifier
        self._exceptionNotifier = exceptionNotifier
        self._userShutting = False

    def run(self):
        self._isRunning = True
        self._proc = subprocess.Popen(
            fr"{self.STATION_EXE} {self._stationName}",
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8')
        # proc.stdin.write("station T0529\n")
        self._proc.stdin.flush()
        while self._proc.poll() is None:
            line = self._proc.stdout.readline()
            # line = line.strip()
            if line:
                self._messageConsumer(line)
        if not self._userShutting:
            self._exceptionNotifier()
        else:
            self._quitNotifier()
        self._isRunning = False

    def stop(self):
        if self._proc is not None and self._isRunning:
            try:
                self._userShutting = True
                self._proc.stdin.write("quit\n")
                self._proc.stdin.flush()
            except:
                ...

    def kill(self):
        if self._proc is not None and self._isRunning:
            try:
                self._userShutting = True
                self._proc.kill()
            except:
                ...
            finally:
                self._isRunning = False

#
# a = Station("T0529", print)
# b = Station("T0529", print)
#
# a.start()
# b.start()
#
# time.sleep(60)
#
# a.stop()
# b.stop()
