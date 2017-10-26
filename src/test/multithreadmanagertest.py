# -*- coding: utf8 -*-
import random
import time
import _thread

from train.linetrainer_manager import LineTrainerManager


def read_thread(name, path):
    # raw_file = open(raw_log_path, "r")
    # lines = raw_file.readlines()
    # for line in lines:
    #     time.sleep(0.5)
    while True:
        time.sleep(0.5)
        rnd = random.randint(1, 5)
        print('name', name, rnd, '请求')
        manager = LineTrainerManager()
        manager.response(rnd)

if __name__ == "__main__":
    try:
        _thread.start_new_thread(read_thread, ("Thread-1", 2, ))
        _thread.start_new_thread(read_thread, ("Thread-2", 4, ))
        _thread.start_new_thread(read_thread, ("Thread-3", 4, ))
        _thread.start_new_thread(read_thread, ("Thread-4", 4, ))
        _thread.start_new_thread(read_thread, ("Thread-5", 4, ))
        _thread.start_new_thread(read_thread, ("Thread-6", 4, ))
        while 1:
            pass
    except Exception as e:
        print(e)