#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pickle
import tensorflow as tf
import baselines.common.tf_util as U
from util.modelprocess import ModelProcess
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
        self.model_process = ModelProcess(1)

        LineTrainerManager.One = self
        self.train_data_model1 = {}
        self.train_data_model2 = {}
        self.generation_id = 0

    def push_data(self, data):
        o4r = pickle.loads(data)

        if o4r['generation_id'] != self.generation_id:
            print("%s /data %d %d %d skip" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
        else:
            if o4r['model_name'] == C.NAME_MODEL_1:
                self.train_data_model1[o4r['battle_id']] = o4r
                print("%s /data %d %d %d - %d/%d" % (
                    time.strftime('%H:%M:%S'),
                    o4r['battle_id'], o4r['generation_id'],
                    len(data), len(self.train_data_model1), C.TRAIN_GAME_BATCH))
            else:
                self.train_data_model2[o4r['battle_id']] = o4r
                print("%s /data %d %d %d - %d/%d" % (
                    time.strftime('%H:%M:%S'),
                    o4r['battle_id'], o4r['generation_id'],
                    len(data), len(self.train_data_model2), C.TRAIN_GAME_BATCH))


    def train(self):
        begin_time = time.time()
        train_data1 = dict(self.train_data_model1)
        train_data2 = dict(self.train_data_model2)
        self.train_data_model1.clear()
        self.train_data_model2.clear()
        self.model_process.do_real_train(train_data1.values(), C.NAME_MODEL_1)
        self.model_process.do_real_train(train_data2.values(), C.NAME_MODEL_2)
        self.generation_id += 1
        self.model_process.dump_model_to_disk(self.generation_id)
        end_time = time.time()
        print('%s /train %d %.2f' % (
            time.strftime('%H:%M:%S'),
            self.generation_id,
            (end_time - begin_time) * 1000
        ))

    def model(self):
        alllist = []
        begin_time = time.time()
        # 把变量转成list类型
        model1_list = tensor_to_list(self.model_process.model_1)
        # 把变量转成list类型
        model2_list = tensor_to_list(self.model_process.model_2)
        alllist.append(model1_list)
        alllist.append(model2_list)
        for i in self.model_process.model_1.pi.get_variables():
            print(U.get_session().run(tf.reduce_sum(i)))
        return alllist


    def start(self):
        print('start')

    def get_generation_id(self):
        return self.generation_id

    def get_batch_num(self):
        return len(self.train_data)