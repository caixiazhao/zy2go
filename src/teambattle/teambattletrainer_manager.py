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


class TeamBattleTrainerManager:
    def __init__(self, battle_id_num, gamma):
        manager = Manager()
        self.request_dict = manager.dict()
        self.result_dict = manager.dict()
        self.lock = Lock()
        self.battle_trainers = {}
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.save_batch = 20
        self.battle_model_util = TeamBattleModelUtil(self.heros, battle_id_num, self.save_batch, gamma)

        for p_battle_id in range(1, battle_id_num+1):
            battle_trainer = TeamBattleTrainer(p_battle_id, self.battle_model_util, gamma)
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