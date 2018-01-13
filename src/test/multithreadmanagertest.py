# -*- coding: utf8 -*-
import random
import time
import _thread

from train.game_manager import LineTrainerManager


def read_thread(name, raw_log_path):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    manager = LineTrainerManager()
    for line in lines:
        time.sleep(0.05)
        json_str = line[23:]
        # rnd = random.randint(1, 5)
        # print('name', name, rnd, '请求')
        manager.response(json_str)

if __name__ == "__main__":
    try:
        _thread.start_new_thread(read_thread, ("Thread-1", '/Users/sky4star/Github/zy2go/data/model_2017-10-24184012.506544/raw.log', ))
        _thread.start_new_thread(read_thread, ("Thread-2", '/Users/sky4star/Github/zy2go/data/model_2017-10-24185919.859215/raw.log', ))
        while 1:
            pass
    except Exception as e:
        print(e)