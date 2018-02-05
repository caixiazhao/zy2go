#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process, Manager, Lock

import queue
import sys
import json as JSON
import time

from model.stateinfo import StateInfo
from teambattle.teambattle_model_util import TeamBattleModelUtil
from teambattle.teambattletrainer import TeamBattleTrainer
import sys, traceback

from util.httputil import HttpUtil


class TeamBattleTrainerManager:
    def __init__(self, battle_id_num):
        manager = Manager()
        self.request_dict = manager.dict()
        self.result_dict = manager.dict()
        self.lock = Lock()
        self.battle_trainers = {}
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.save_batch = 200
        self.schedule_timesteps = 200000
        self.model_initial_p = 0.5
        self.model_final_p = 0.1
        self.gamma = 0.95
        self.model_path = '/Users/sky4star/Downloads/model_20180202/{}_2700/model'
        self.save_dir = HttpUtil.get_save_root_path()
        self.battle_model_util = TeamBattleModelUtil(self.heros, battle_id_num, self.save_dir, self.save_batch,
                                                     self.schedule_timesteps, self.model_initial_p, self.model_final_p,
                                                     self.gamma, self.model_path)

        for p_battle_id in range(1, battle_id_num+1):
            battle_trainer = TeamBattleTrainer(self.save_dir, p_battle_id, self.battle_model_util, self.gamma)
            self.battle_trainers[p_battle_id] = battle_trainer

        TeamBattleTrainerManager.One = self
        print('训练器初始化完毕, 训练器数量', battle_id_num)

    def read_process(self, json_str):
        begin_time = time.time()
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid

        try:
            response = self.battle_trainers[p_battle_id].build_response(json_str)
            return response
        except queue.Empty:
            print("LineTrainerManager Exception empty")
            return '{}'
        except Exception:
            print("LineTrainerManager Exception")
            traceback.print_exc(file=sys.stdout)
            return '{}'