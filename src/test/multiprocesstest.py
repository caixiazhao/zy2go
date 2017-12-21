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
    for line in lines:
        time.sleep(0.05)
        json_str = line[23:]
        response = LineTrainerManager.read_process(json_str, p_request_dict, p_result_dict, lock)
    print(name, 'done')

if __name__ == "__main__":
    try:
        manager = LineTrainerManager(2)
        manager.start()
        print('训练器准备完毕')

        p1 = Process(target=read_process, args=('process_1',
                    'C:/Users/Administrator/Documents/GitHub/zy2go/battle_logs/model_2017-12-19143358.532959/1/raw_1.log',
                                           manager.request_dict, manager.result_dict, manager.lock))
        # p2 = Process(target=read_process, args=('process_2',
        #             '/Users/sky4star/Github/zy2go/battle_logs/test/raw_2.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        # p3 = Process(target=read_process, args=('process_3',
        #             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-07110642.104735/3/raw_3.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        # p4 = Process(target=read_process, args=('process_4',
        #             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-03184456.110081/4/raw_4.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        # p5 = Process(target=read_process, args=('process_5',
        #             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-03184456.110081/5/raw_5.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        # p6 = Process(target=read_process, args=('process_6',
        #             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-03184456.110081/6/raw_6.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        # p7 = Process(target=read_process, args=('process_7',
        #             '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-03184456.110081/7/raw_7.log',
        #                                         manager.request_dict, manager.result_dict, manager.request_signal,
        #                                         manager.done_signal, manager.lock))
        p1.start()
        # p2.start()
        # p3.start()
        # p4.start()
        # p5.start()
        # p6.start()
        # p7.start()
        print('测试进程启动')
        p1.join()
        # p2.join()
        while 1:
            pass
    except Exception as e:
        print(e)