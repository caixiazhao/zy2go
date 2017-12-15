# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager, Lock

import json as JSON
import numpy as np
from multiprocessing import Event

from model.stateinfo import StateInfo
from train.linetrainer_manager import LineTrainerManager
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


def read_process(name, raw_log_path, p_request_dict, p_result_dict, lock):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    producer_times = []
    for line in lines:
        time.sleep(random.randint(1,5)/float(1000))
        json_str = line[23:]
        begin_time = time.time()
        response = LineTrainerManager.read_process(json_str, p_request_dict, p_result_dict, lock)
        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        producer_times.append(delta_millionseconds)
        if len(producer_times) >= 100:
            print("model producer_process average calculate time(ms)",
                  sum(producer_times) // float(len(producer_times)))
            producer_times = []

    print(name, 'done')

if __name__ == "__main__":
    try:
        num = 20
        manager = LineTrainerManager(20)
        manager.start()
        print('训练器准备完毕')

        for i in range(num):
            p1 = Process(target=read_process, args=('process_1',
                                                    '/Users/sky4star/Github/zy2go/battle_logs/test/raw_1.log',
                                                    manager.request_dict, manager.result_dict, manager.lock))
            p2 = Process(target=read_process, args=('process_2',
                                                    '/Users/sky4star/Github/zy2go/battle_logs/test/raw_2.log',
                                                    manager.request_dict, manager.result_dict, manager.lock))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        print('测试进程启动')
        while 1:
            pass
    except Exception as e:
        print(e)