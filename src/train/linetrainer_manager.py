#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from multiprocessing import Process, Manager, Lock

import sys
import json as JSON
import traceback
import time

from common import cf as C
from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelprocess import ModelProcess
from util.ppocache2 import PPO_CACHE2


class LineTrainerManager:
    def __init__(self, base_bid, battle_id_num):
        self.model_process = ModelProcess(battle_id_num)

        # TODO: Temporarily hold the original variables
        self.lock = None
        self.request_dict = None
        self.result_dict = None

        #model1_hero = '27'
        #model2_hero = '28'

        self.base_bid = base_bid
        self.line_trainers = {}
        for bid in range(1, 1 + battle_id_num):
            self.line_trainers[base_bid + bid] = self.setup_line_trainer(bid)
        #self.line_trainer = self.line_trainers[1]

        LineTrainerManager.One = self
        print('训练器初始化完毕, 训练器数量', battle_id_num)

    def setup_line_trainer(self, battle_id):
        model1_cache = PPO_CACHE2()
        model2_cache = PPO_CACHE2()
        root_dir = self.model_process.save_dir
        save_dir = HttpUtil.get_linetrainer_save_path(root_dir, battle_id)
        model1_hero = '27'
        model2_hero = '28'

        return LineTrainerPPO(battle_id,
            save_dir, self.model_process,
            model1_hero, model1_cache,
            model2_hero, model2_cache,
            real_hero=None, policy_ratio=1, policy_continue_acts=3)


    def read_process_(self, json_str):
        begin_time = time.time()
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid
        response = self.line_trainers[p_battle_id].train_line_model(json_str)
        end_time = time.time()

        if C.LOG['MANAGER__READ_PROCESS']:
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

