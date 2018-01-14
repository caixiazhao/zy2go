#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pickle


from util.modelprocess import ModelProcess
from common import cf as C

class LineTrainerManager:
    def __init__(self, run_mode):
        battle_id_num = 1

        self.run_mode = run_mode
        self.model_process = ModelProcess(1)

        LineTrainerManager.One = self
        self.train_data = []
        self.generation_id = 0

    def push_data(self, data):
        o4r = pickle.loads(data)

        if o4r['generation_id'] != self.generation_id:
            print("%s /data %d %d %d skip" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
        else:
            self.train_data.append(o4r)
            print("%s /data %d %d %d - %d/%d" % (
                time.strftime('%H:%M:%S'),
                o4r['battle_id'], o4r['generation_id'],
                len(data), len(self.train_data), C.TRAIN_GAME_BATCH))

    def train(self):
        begin_time = time.time()
        train_data = list(self.train_data)
        self.train_data.clear()
        self.model_process.do_real_train(train_data)
        self.generation_id += 1
        self.model_process.dump_model_to_disk(self.generation_id)
        end_time = time.time()
        print('%s /train %d %.2f' % (
            time.strftime('%H:%M:%S'),
            self.generation_id,
            (end_time - begin_time) * 1000
        ))


    def start(self):
        print('start')

    def get_generation_id(self):
        return self.generation_id

    def get_batch_num(self):
        return len(self.train_data)
