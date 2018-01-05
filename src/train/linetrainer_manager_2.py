#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from multiprocessing import Process, Manager, Lock

import sys
import json as JSON
import traceback
import time

from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo_2 import LineTrainerPPO
from util.modelprocess_2 import ModelProcess
from util.ppocache2 import PPO_CACHE2


class LineTrainerManager:
    def __init__(self, battle_id_num):
        self.model_process = ModelProcess(battle_id_num)
        
        # TODO: Temporarily hold the original variables
        self.lock = None
        self.request_dict = None
        self.result_dict = None
        p_battle_id = 1
        p_model_process = self.model_process

        model1_cache = PPO_CACHE2()
        model2_cache = PPO_CACHE2()
        root_dir = self.model_process.save_dir
        save_dir = HttpUtil.get_linetrainer_save_path(root_dir, p_battle_id)
        model1_hero = '27'
        model2_hero = '28'

        # TODO: battle_id_num
        self.line_trainer = LineTrainerPPO(
            1, save_dir, self.model_process,
            model1_hero, model1_cache,
            model2_hero, model2_cache,
            real_hero=None, policy_ratio=-1, policy_continue_acts=3)

        LineTrainerManager.One = self
        print('训练器初始化完毕, 训练器数量', battle_id_num)

    def read_process_(self, json_str):
        begin_time = time.time()
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid
        response = self.line_trainer.train_line_model(json_str)
        end_time = time.time()

        print('read_process', 
            p_battle_id, raw_state_info.tick,
            '%.2f' % ((end_time - begin_time) * 1000), 
            'RESPONSE:%s' % response)
            
        return response

    @staticmethod
    def read_process(json_str, p_request_dict, p_result_dict, lock):
        try:
            return LineTrainerManager.One.read_process_(json_str)
        except Exception as ex:
            print("LineTrainerManager Exception")
            traceback.print_exc()
            return '{}'

    def start(self):
        print('训练器启动完毕')

