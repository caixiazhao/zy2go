# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager

import json as JSON
import numpy as np
from multiprocessing import Event

from model.stateinfo import StateInfo
from train.linetrainer_manager import LineTrainerManager
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


def read_process(name, raw_log_path, p_request_queue_map):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    for line in lines:
        time.sleep(0.05)
        json_str = line[23:]
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid
        print(p_battle_id)
        p_request_queue = p_request_queue_map[int(p_battle_id)]
        p_request_queue.put(json_str)


def start_line_trainer_process(p_battle_id, p_request_queue, p_result_queue, p_done_signal):
    ob = np.zeros(183, dtype=float).tolist()
    model1_cache = PPO_CACHE2(ob, 1)
    model2_cache = PPO_CACHE2(ob, 1)
    # save_dir = model_process.save_dir
    save_dir = HttpUtil.get_save_root_path()
    model1_hero = '27'
    model2_hero = '28'
    line_trainer = LineTrainerPPO(
        p_battle_id, save_dir, None, model1_hero,
        model1_cache, model2_hero, model2_cache,
        real_hero=None, policy_ratio=-1, policy_continue_acts=3)

    while True:
        json_str = p_request_queue.get()
        response = line_trainer.response(json_str)
        p_result_queue.put(response)
        p_done_signal.set()

if __name__ == "__main__":
    try:
        manager = Manager()
        request_queue_map = manager.dict()
        model_process = ModelProcess()
        # model_process.start()

        for battle_id in range(3):
            request_queue = manager.Queue()
            result_queue = manager.Queue()
            request_queue_map[battle_id] = result_queue
            done_signal = Event()
            line_trainer_process = Process(target=start_line_trainer_process, args=(battle_id, request_queue, result_queue, done_signal,))
            line_trainer_process.start()

        print('训练器准备完毕')

        p1 = Process(target=read_process, args=('process_1', '/Users/sky4star/Github/zy2go/data/model_2017-10-24184012.506544/raw.log', request_queue_map))
        p2 = Process(target=read_process, args=('process_2', '/Users/sky4star/Github/zy2go/data/model_2017-10-24185919.859215/raw.log', request_queue_map))
        p1.start()
        p2.start()
        print('测试进程启动')
        p1.join()
        p2.join()
    except Exception as e:
        print(e)