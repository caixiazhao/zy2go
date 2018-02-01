#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pickle
import tensorflow as tf
import baselines.common.tf_util as U
from teambattle.teambattle_model_util import TeamBattleModelUtil
from common import cf as C


def tensor_to_list(model):
    # 将张量转成list形式，方便传输
    model_list = []
    for newv in model.pi.get_variables():
        model_list.append(U.get_session().run(newv).tolist())
    return model_list

class LineTrainerManager:
    def __init__(self, run_mode):
        battle_id_num = 1

        self.run_mode = run_mode
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.save_batch = 20
        self.gamma = 0.99
        self.battle_model_util = TeamBattleModelUtil(self.heros, battle_id_num, self.save_batch, self.gamma)

        LineTrainerManager.One = self
        self.train_data_model = {}



    def push_data(self, data):
        o4r = pickle.loads(data)

        if o4r['generation_id'] != C.generation_id:
            print("%s /data %d %d %d skip" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
        else:
            self.train_data_model[o4r['hero_name']][o4r['battle_id']] = o4r
            print("%s /data %d %d %d - %d/%d" % (
                    time.strftime('%H:%M:%S'),
                    o4r['battle_id'], o4r['generation_id'],
                    len(data), len(self.train_data_model[o4r['hero_name']]), C.TRAIN_GAME_BATCH))


    def train(self):
        begin_time = time.time()
        train_data = dict(self.train_data_model)
        self.train_data_model.clear()
        for hero_name in self.heros:
            self.battle_model_util.do_real_train(train_data[hero_name].values(),hero_name)
        C.generation_id += 1
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
        # 把变量转成list类型
        model, _ = self.battle_model_util.model_map["27"]
        for i in model.pi.get_variables():
            print(U.get_session().run(tf.reduce_sum(i)))
        return alllist


    def start(self):
        print('start')

    def get_generation_id(self):
        return C.generation_id

