# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager

import json as JSON
import numpy as np

from train.linetrainer_manager import LineTrainerManager
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


def read_process(name, raw_log_path):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    manager = LineTrainerManager()
    for line in lines:
        time.sleep(0.05)
        json_str = line[23:]
        manager.response(json_str)



if __name__ == "__main__":
    try:
        manager = Manager()
        line_trainers = manager.dict()
        model_process = ModelProcess()
        # model_process.start()

        for battle_id in range(3):
            ob = np.zeros(183, dtype=float).tolist()
            model1_cache = PPO_CACHE2(ob, 1)
            model2_cache = PPO_CACHE2(ob, 1)
            # save_dir = model_process.save_dir
            save_dir = HttpUtil.get_save_root_path()
            model1_hero = '27'
            model2_hero = '28'
            line_trainers[battle_id] = LineTrainerPPO(
                battle_id, save_dir, None, model1_hero,
                model1_cache, model2_hero, model2_cache,
                real_hero=None, policy_ratio=-1, policy_continue_acts=3)
        print('训练器准备完毕')

        p1 = Process(target=read_process, args=('process_1', '/Users/sky4star/Github/zy2go/data/model_2017-10-24184012.506544/raw.log'))
        p2 = Process(target=read_process, args=('process_2', '/Users/sky4star/Github/zy2go/data/model_2017-10-24185919.859215/raw.log'))
        p1.start()
        p2.start()
        print('测试进程启动')
        p1.join()
        p2.join()
        while 1:
            pass
    except Exception as e:
        print(e)