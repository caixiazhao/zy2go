#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
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
        #TODO temperay ignore upload data generation.
        o4r['generation_id'] = self.generation_id

        if o4r['generation_id'] != self.generation_id:
            print("/data %d %d %d skip" % (
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
        else:
            self.train_data.append(o4r)
            print("/data %d %d %d - %d/%d" % (
                o4r['battle_id'], o4r['generation_id'],
                len(data), len(self.train_data), C.TRAIN_GAME_BATCH))

    def train(self):
        train_data = list(self.train_data)
        self.train_data.clear()
        self.model_process.do_real_train(train_data)
        self.generation_id += 1
        self.dump_model_to_disk()

    def dump_model_to_disk(self):
        base_path = os.path.join(C.DATA_ROOT_PATH, "trainer", str(self.get_generation_id()))
        shutil.rmtree(base_path)
        os.makedirs(base_path)
        self.model_process.model_1.save(base_path + '/1')
        self.model_process.model_2.save(base_path + '/2')

    def start(self):
        print('start')

    def get_generation_id(self):
        return self.generation_id

    def get_batch_num(self):
        return len(self.train_data)
