import logging
import os
import threading
from typing import List, Iterator, Set
import misc
import tkinter as tk
import PySimpleGUI as sg

log = logging.getLogger("UI")

HELLO = r"""
使用说明：

0) 必须以管理员权限运行！

1）将本程序放置到stations目录下
例如：C:\Users\pyxx76\Niagara4.10\PhoenixContact\stations

2）左侧列表中选择（多选）要操作的站，并通过底部按钮执行对应操作。

3）运行期选择站，显示实时日志。

4) 慎用Kill
如果因为文件锁问题无法再次开启，请在 资源监视器 中手动删除 station.exe 进程。

5) 关闭程序前，请手动对所有站执行 Stop，原因同上。

6) 背景色含义：
    红色：启动异常
    绿色：正常启动
    黄色：正在关闭
    无色：未运行
                            -- Song Yantao
                            -- Ver 0.3 @ 2022.06.03-12:00
                            
@change log
Ver 0.2 修复 station.exe 路径bug
Ver 0.3 修复 Kill ,及其他自身崩溃问题
"""
import pathlib
import sys
import os

STATION_PATH = os.path.split(sys.argv[0])[0]

print(str(STATION_PATH))
# STATION_PATH = r"C:\Users\pyxx76\Niagara4.10\PhoenixContact\stations"


class Controller:
    def __init__(self):
        self._entityMap = {i.getStationName(): i
                           for i in
                           misc.getAllStationEntry(self, str(STATION_PATH))}

        self._window = self.make_window()
        self._refreshThread = threading.Thread(target=self._refresh, name="视图刷新")
        self._cond = threading.Condition()
        self._stopping = False
        self._log_lock = threading.RLock()

    def notifyUiChange(self):
        with self._cond:
            self._cond.notify_all()

    def _refresh(self):
        A = True
        while True:
            with self._cond:
                self._cond.wait(0.5)
            if self._stopping:
                break
            # if self._window['-LOG-'].TKText
            # if A:
            #     self._window['-STATION LIST-'].TKListbox.itemconfigure(1, bg='green')
            #     A = False
            # else:
            #     self._window['-STATION LIST-'].TKListbox.itemconfigure(1, bg='')
            #     A = True

        log.debug("视图刷新线程结束")

    def do_start_station(self, stationEntrys: Set[misc.StationEntry]):
        self._window['-LOG-'].TKText.delete('1.0', tk.END)
        for entry in stationEntrys:
            entry.ui_do_start()

    def do_stop_station(self, stationEntrys: Set[misc.StationEntry]):
        for entry in stationEntrys:
            entry.ui_do_stop()

    def do_kill_station(self, stationEntrys: Set[misc.StationEntry]):
        for entry in stationEntrys:
            entry.ui_do_kill()

    def setStationBg(self, stationEntry: misc.StationEntry, bg):
        self._window.write_event_value('-THREAD CHANGE BG-', (stationEntry.getStationName(), bg))

    def append_lop(self, msg):
        self._window.write_event_value('-THREAD APPEND-', msg)

    def change_log_page(self, stationEntry: misc.StationEntry):
        log.debug(f"切换日志页到:{stationEntry}")
        tklog = self._window['-LOG-']
        tklog.update("".join(stationEntry.get_buffered_log()))

    def loop(self):
        self._refreshThread.start()
        while True:
            try:
                event, values = self._window.read()
                if event:
                    # self._window['-LOG-'].update(event + "\n", append=True)

                    # print("EVENT:" + event)
                    # print(values['-STATION LIST-'])
                    ...
                if event in (sg.WINDOW_CLOSED, 'Exit'):
                    # 退出
                    break
                if event == "-THREAD APPEND-":
                    tklog = self._window['-LOG-']
                    tklog.update(values["-THREAD APPEND-"], append=True)
                    if tklog.TKText.count('1.0', tk.END, "lines")[0] > 5000:
                        tklog.TKText.delete('1.0', f"1000.0")
                        log.debug("清理1000行日志")
                elif event == '-STATION LIST-':
                    current = values['-STATION LIST-']
                    # 游走在列表中
                    last = None
                    for n, i in self._entityMap.items():
                        i.ui_select(n in current)

                    if len(current) > 0:
                        self.change_log_page(self._entityMap[current[-1]])

                elif event == '-THREAD CHANGE BG-':
                    sn, bg = values['-THREAD CHANGE BG-']
                    for idx, v in enumerate(self._window['-STATION LIST-'].Values):
                        if v == sn:
                            self._window['-STATION LIST-'].TKListbox.itemconfigure(idx, bg=bg)

                elif event == '-FILTER-':
                    # 筛选逻辑
                    new_list = [i for i in self._entityMap.keys() if values['-FILTER-'].lower() in i.lower()]
                    self._window['-STATION LIST-'].update(new_list)
                    for idx, v in enumerate(new_list):
                        e = self._entityMap[v]
                        self._window['-STATION LIST-'].TKListbox.itemconfigure(idx, bg=e._getCurrentBg())

                elif event == 'Start':
                    self.do_start_station(set(map(lambda name: self._entityMap[name], values['-STATION LIST-'])))
                elif event == 'Stop':
                    self.do_stop_station(set(map(lambda name: self._entityMap[name], values['-STATION LIST-'])))
                elif event == 'Kill':
                    self.do_kill_station(set(map(lambda name: self._entityMap[name], values['-STATION LIST-'])))
            except:
                ...
        self._stopping = True
        with self._cond:
            self._cond.notify_all()
        self._window.close()

    def make_window(self):
        sg.theme(sg.OFFICIAL_PYSIMPLEGUI_THEME)
        left_col = sg.Col([
            [sg.Listbox(values=tuple(self._entityMap.keys()),
                        select_mode=sg.SELECT_MODE_EXTENDED,
                        size=(20, 42),
                        key='-STATION LIST-',
                        enable_events=True)],
            [sg.Text('Filter:', size=(5, 1)),
             sg.Input(size=(15, 1), enable_events=True, key='-FILTER-')],
            [sg.Button('Start'), sg.B('Stop'), sg.B('Kill')]
        ], element_justification='l')

        right_col = [
            [sg.Multiline(HELLO, size=(140, 60), write_only=True, key='-LOG-', font='宋体 10')],
        ]
        layout = [[sg.Text('菲尼克斯应用开发团队测试专用！', font='宋体 10')],
                  sg.vtop([sg.Column([[left_col]], element_justification='l'),
                           sg.Col(right_col, element_justification='r')]),
                  # sg.vbottom([sg.Multiline(size=(100, 6), write_only=True, key='-ML-', reroute_stdout=True,
                  #                          echo_stdout_stderr=True)]),
                  ]
        window = sg.Window('Emalytics 快捷启动器', layout, finalize=True)
        # sg.cprint_set_output_destination(window, '-ML-')
        return window


def main():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    c = Controller()
    c.loop()


if __name__ == "__main__":
    main()

    # print(a)
