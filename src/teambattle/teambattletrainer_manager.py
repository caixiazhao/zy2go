#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process, Manager, Lock

import queue
import sys
import json as JSON
import time

import requests

from model.stateinfo import StateInfo
from teambattle.teambattletrainer import TeamBattleTrainer
import sys, traceback
import time
import pickle
import tensorflow as tf
import baselines.common.tf_util as U
from teambattle.teambattle_model_util import TeamBattleModelUtil
from common import cf as C
from util.httputil import HttpUtil

def sync_generation_id_from_trainer():
    try:
        r = requests.get('http://127.0.0.1:%d/generation_id' % C.GATEWAY_PORT)
        return int(r.text)
    except Exception as ex:
        print(ex)
        return 0

def tensor_to_list(model):
    # 将张量转成list形式，方便传输
    model_list = []
    for newv in model.pi.get_variables():
        model_list.append(U.get_session().run(newv).tolist())
    return model_list


class TeamBattleTrainerManager:
    def __init__(self, base, battle_id_num, run_mode):
        manager = Manager()
        self.run_mode = run_mode
        self.request_dict = manager.dict()
        self.result_dict = manager.dict()
        self.lock = Lock()
        self.battle_trainers = {}
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.save_batch = 20
        self.schedule_timesteps = 200000
        self.model_initial_p = 0
        self.model_final_p = 0
        self.gamma = 0.95
        self.model_path = '/Users/sky4star/Github/zy2go/data/model_20180228/{}_4780/model' if run_mode == C.RUN_MODE_TRAIN else None
        self.save_dir = HttpUtil.get_save_root_path()
        self.ob_size = 890
        self.act_size = 28
        self.enable_policy = True
        self.battle_model_util = TeamBattleModelUtil(self.ob_size, self.act_size, self.heros, battle_id_num, self.save_dir, self.save_batch,
                                                     self.schedule_timesteps, self.model_initial_p, self.model_final_p,
                                                     self.gamma, self.model_path)
        TeamBattleTrainerManager.One = self
        self.train_data_map = {}
        for hero_name in self.heros:
            self.train_data_map[hero_name] = {}

        # 如果是执行模型，创建训练器
        if self.run_mode == C.RUN_MODE_PREDICT:
            for p_battle_id in range(1, battle_id_num + 1):
                real_battpe_id = base + p_battle_id
                battle_trainer = TeamBattleTrainer(self.act_size, self.save_dir, real_battpe_id, self.battle_model_util, self.gamma, self.enable_policy)
                self.battle_trainers[real_battpe_id] = battle_trainer
            C.generation_id = sync_generation_id_from_trainer()
            self.lastCheckGenerationId = time.time()
            print('训练器初始化完毕, 训练器数量', battle_id_num)

    def read_process(self, json_str):
        begin_time = time.time()
        if begin_time - self.lastCheckGenerationId > 1.5:
            C.generation_id = sync_generation_id_from_trainer()
            self.lastCheckGenerationId = begin_time
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

    def push_data(self, data):
        o4r = pickle.loads(data)

        if o4r['generation_id'] != C.generation_id:
            print("%s /data %d %d  skip" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'],
                len(data)))
        else:
            print(o4r['hero_name'], o4r['battle_id'])
            self.train_data_map[o4r['hero_name']][o4r['battle_id']] = o4r

            print("%s /data %d %d %d - %d/%d" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'], o4r['generation_id'],
                len(data), len(self.train_data_map[o4r['hero_name']]), C.TRAIN_GAME_BATCH))

    def train(self):
        C.generation_id += 1
        begin_time = time.time()
        train_data = {}
        for hero_name in self.heros:
            battle_data_map = {}
            train_data[hero_name] = battle_data_map
            train_data[hero_name] = dict(self.train_data_map[hero_name])
            self.train_data_map[hero_name].clear()
        for hero_name in self.heros:
            self.battle_model_util.do_real_train(train_data[hero_name].values(), hero_name)
        end_time = time.time()
        print('%s /train %d %.2f' % (
            time.strftime('%H:%M:%S'),
            C.generation_id,
            (end_time - begin_time) * 1000
        ))

    def model(self):
        alllist = []
        # 把变量转成list类型
        for hero_name in self.heros:
            model, _ = self.battle_model_util.model_map[hero_name]
            model_list = tensor_to_list(model)
            alllist.append(model_list)
        return alllist

    def get_generation_id(self):
        return C.generation_id
