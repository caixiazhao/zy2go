#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process, Manager, Lock

import queue
import sys
import json as JSON
import numpy as np
from multiprocessing import Event
import traceback
import time

from multiprocessing import SimpleQueue

from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


def start_line_trainer_process(p_battle_id, p_model_process, p_request_queue, p_result_queue):
    model1_cache = PPO_CACHE2()
    model2_cache = PPO_CACHE2()
    root_dir = p_model_process.save_dir
    save_dir = HttpUtil.get_linetrainer_save_path(root_dir, p_battle_id)
    model1_hero = '27'
    model2_hero = '28'
    line_trainer = LineTrainerPPO(
        p_battle_id, save_dir, p_model_process, model1_hero,
        model1_cache, model2_hero, model2_cache,
        real_hero=None, policy_ratio=-1, policy_continue_acts=3)

    while True:
        # print('trainer_process', p_battle_id, 'receive', 'request signal', ';'.join((str(k) for k in p_request_dict.keys())))
        if not p_request_queue.empty():
            json_str = p_request_queue.get()

            try:
                response = line_trainer.train_line_model(json_str)
                # print('trainer_process', p_battle_id, 'put a result', time.time())
                p_result_queue.put(response)
            except Exception as e:
                print('linetrainer manager catch exception', traceback.format_exc())
                p_result_queue.put('{}')

class LineTrainerManager:
    def __init__(self, battle_id_num):
        self.request_queues = []
        self.result_queues = []
        for i in range(battle_id_num):
            request_queue = SimpleQueue()
            result_queue = SimpleQueue()
            self.request_queues.append(request_queue)
            self.result_queues.append(result_queue)
        self.model_process = ModelProcess(battle_id_num)
        self.line_trainer_process_list = []

        for battle_id in range(0, battle_id_num):
            request_queue = self.request_queues[battle_id]
            result_queue = self.result_queues[battle_id]
            line_trainer_process = Process(target=start_line_trainer_process,
                                           args=(battle_id, self.model_process, request_queue, result_queue,))
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
    def read_process(json_str, p_request_queues, p_result_queues):
        begin_time = time.time()
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = int(raw_state_info.battleid)
        request_queue = p_request_queues[p_battle_id]
        result_queue = p_result_queues[p_battle_id]
        # if raw_state_info.tick == -1:
        #     print('read_process: need to handle ', p_battle_id, raw_state_info.tick, 'raw log', json_str)
        # else:
        #     print('read_process: need to handle ', p_battle_id, raw_state_info.tick)

        # print('read_process', p_battle_id, 'send a request', raw_state_info.tick)
        request_queue.put(json_str)

        try:
            while True:
                if not result_queue.empty():
                    # print('read_process', p_battle_id, 'get a result', raw_state_info.tick)
                    result = result_queue.get()
                    end_time = time.time()
                    print('read_process', p_battle_id, raw_state_info.tick, (end_time - begin_time) * 1000, '取得结果',
                          result)
                    return result
        except queue.Empty:
            print("LineTrainerManager Exception empty")
            return '{}'
        except Exception:
            print("LineTrainerManager Exception")
            type, value, traceback = sys.exc_info()
            traceback.print_exc()
            return '{}'