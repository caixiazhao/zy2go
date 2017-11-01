# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager, Lock

import json as JSON
import numpy as np
from multiprocessing import Event

from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


def read_process(name, raw_log_path, p_request_dict, p_result_dict, p_request_signal, p_done_signal, lock):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    for line in lines:
        time.sleep(0.05)
        json_str = line[23:]
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid

        with lock:
            print('read_process', p_battle_id, 'send', 'a request')
            p_request_dict[p_battle_id] = json_str
            p_request_signal.set()

        while True:
            p_done_signal.wait(10)
            print('read_process', p_battle_id, 'receive', 'a signal')
            with lock:
                if p_battle_id in p_result_dict.keys():
                    print('read_process', p_battle_id, 'get', 'a result')
                    p_done_signal.clear()
                    result = p_result_dict[p_battle_id]
                    del p_result_dict[p_battle_id]
                    print(result)
                    break


def start_line_trainer_process(p_battle_id, p_model_process, p_request_dict, p_result_dict, p_request_signal, p_done_signal, lock):
    ob = np.zeros(183, dtype=float).tolist()
    model1_cache = PPO_CACHE2(ob, 1)
    model2_cache = PPO_CACHE2(ob, 1)
    # save_dir = model_process.save_dir
    save_dir = HttpUtil.get_save_root_path()
    model1_hero = '27'
    model2_hero = '28'
    line_trainer = LineTrainerPPO(
        p_battle_id, save_dir, p_model_process, model1_hero,
        model1_cache, model2_hero, model2_cache,
        real_hero=None, policy_ratio=-1, policy_continue_acts=3)

    while True:
        p_request_signal.wait()
        print('trainer_process', p_battle_id, 'receive', 'request signal')

        json_str = None
        with lock:
            if p_battle_id in p_request_dict.keys():
                print('trainer_process', p_battle_id, 'get', 'a request')
                p_request_signal.clear()
                json_str = p_request_dict[p_battle_id]
                del p_request_dict[p_battle_id]

        if json_str is not None:
            response = line_trainer.train_line_model(json_str)
            with lock:
                print('trainer_process', p_battle_id, 'put', 'a result')
                p_result_dict[p_battle_id] = response
                p_done_signal.set()

if __name__ == "__main__":
    try:
        manager = Manager()
        request_dict = manager.dict()
        result_dict = manager.dict()
        request_signal = Event()
        done_signal = Event()
        lock = Lock()
        model_process = ModelProcess()
        model_process.start()

        for battle_id in range(3):
            line_trainer_process = Process(target=start_line_trainer_process,
                                           args=(battle_id, model_process, request_dict, result_dict, request_signal, done_signal, lock,))
            line_trainer_process.start()

        print('训练器准备完毕')

        p1 = Process(target=read_process, args=('process_1',
                    '/Users/sky4star/Github/zy2go/data/model_2017-10-24184012.506544/raw.log',
                    request_dict, result_dict, request_signal, done_signal, lock))
        p2 = Process(target=read_process, args=('process_2',
                    '/Users/sky4star/Github/zy2go/data/model_2017-10-24185919.859215/raw.log',
                    request_dict, result_dict, request_signal, done_signal, lock))
        p1.start()
        p2.start()
        print('测试进程启动')
        p1.join()
        p2.join()
    except Exception as e:
        print(e)