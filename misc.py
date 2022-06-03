import logging
import os
from typing import Iterator

from station import Station

log = logging.getLogger("MISC")


class StationEntry:
    def __init__(self, c, stationName, path):
        self._stationName = stationName
        self._path = path
        self._c = c
        self._bg = ''
        self._is_focusing = False
        self._log = []
        self._process = Station(self.getStationName(), self.append_log, self.onProcQuit, self.onProcExec)

    def onProcQuit(self):
        self.ui_set_bg("")

    def onProcExec(self):
        self.ui_set_bg("red")

    def append_log(self, msg):
        # 大于600行，减去100行
        if len(self._log) > 600:
            self._log = self._log[100:]
        self._log.append(msg)
        if self._is_focusing:
            self._c.append_lop(msg)

    def get_buffered_log(self):
        return self._log

    def __repr__(self):
        return self.getStationName()

    def getStationName(self):
        return self._stationName

    def ui_do_start(self):
        self._log.clear()
        if not self._process.is_alive():
            log.debug(f"开启->{self.getStationName()}")
            self.ui_set_bg("green")
            try:
                self._process.start()
            except:
                self._process = Station(self.getStationName(), self.append_log, self.onProcQuit, self.onProcExec)
                self._process.start()
        else:
            log.error(f"{self.getStationName()} 已经开启")

    def ui_do_stop(self):
        if self._process.is_alive():
            log.debug(f"关闭->{self.getStationName()}")
            self.ui_set_bg("yellow")
            self._process.stop()
        else:
            log.error(f"{self.getStationName()} 未在运行，忽略关闭命令")

    def ui_do_kill(self):
        if self._process.is_alive():
            log.debug(f"杀死->{self.getStationName()}")
            self.ui_set_bg("")
            self._process.stop()
            self._process.kill()
            self._process.kill()
        else:
            log.error(f"{self.getStationName()} 未在运行，忽略杀命令")

    def ui_set_bg(self, colour):
        self._bg = colour
        return self._c.setStationBg(self, colour)

    def _getCurrentBg(self):
        return self._bg

    def ui_select(self, focus: bool):
        self._is_focusing = focus
        if focus:
            log.debug(f"{self.getStationName()} 选中")
        else:
            log.debug(f"{self.getStationName()} 失去焦点")


def getAllStationEntry(c, stationFolderPath: str) -> Iterator[StationEntry]:
    P = stationFolderPath
    for fdn in os.listdir(P):
        _p = os.path.join(P, fdn)
        if os.path.isdir(_p):
            if 'config.bog' in os.listdir(_p):
                yield StationEntry(c, fdn, _p)
