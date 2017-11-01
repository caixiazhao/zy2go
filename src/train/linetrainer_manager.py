#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process, Manager, Lock

import json as JSON
import numpy as np
from multiprocessing import Event

from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


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


class LineTrainerManager:
    def __init__(self, battle_id_num):
        manager = Manager()
        self.request_dict = manager.dict()
        self.result_dict = manager.dict()
        self.request_signal = Event()
        self.done_signal = Event()
        self.lock = Lock()
        self.model_process = ModelProcess()
        self.line_trainer_process_list = []

        for battle_id in range(1, battle_id_num+1):
            line_trainer_process = Process(target=start_line_trainer_process,
                                           args=(battle_id, self.model_process, self.request_dict, self.result_dict,
                                                 self.request_signal, self.done_signal, self.lock,))
            self.line_trainer_process_list.append(line_trainer_process)
        print('训练器初始化完毕, 训练器数量', battle_id_num)

    def start(self):
        self.model_process.start()
        for line_trainer_process in self.line_trainer_process_list:
            line_trainer_process.start()

        self.model_process.init_signal.wait(600)
        self.model_process.init_signal.clear()
        print('训练器启动完毕')

    @staticmethod
    def read_process(json_str, p_request_dict, p_result_dict, p_request_signal, p_done_signal, lock):
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
                    return result
