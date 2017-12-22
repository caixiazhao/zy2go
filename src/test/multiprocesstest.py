# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager, Lock

import json as JSON
import numpy as np
from multiprocessing import Event

from model.stateinfo import StateInfo
from train.linetrainer_manager import LineTrainerManager


def read_process(battle_id, raw_log_path, p_request_dict, p_result_dict, lock):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    producer_times = []
    for line in lines:
        time.sleep(random.randint(1,5)/float(1000))
        json_str = line[23:]
        json_str = json_str.replace('"ID":1', '"ID":'+str(battle_id), 1)
        begin_time = time.time()
        response = LineTrainerManager.read_process(json_str, p_request_dict, p_result_dict, lock)
        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        producer_times.append(delta_millionseconds)
        if len(producer_times) >= 100:
            print("model producer_process average calculate time(ms)",
                  sum(producer_times) // float(len(producer_times)))
            producer_times = []

    print(battle_id, 'done')

if __name__ == "__main__":
    try:
        num = 1
        manager = LineTrainerManager(num)
        manager.start()
        print('训练器准备完毕')

        for i in range(1, num+1):
            p1 = Process(target=read_process, args=(i, '/Users/sky4star/Github/zy2go/battle_logs/test/raw_1.log',
                                                    manager.request_dict, manager.result_dict, manager.lock))

            p1.start()
            print('测试进程启动', i)
        while 1:
            pass
    except Exception as e:
        print(e)