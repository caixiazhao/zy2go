#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle

from util.modelprocess import ModelProcess


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
            print("/data %d %d %d skip" % (
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
        else:
            print("/data %d %d %d" % (
                o4r['battle_id'], o4r['generation_id'],
                len(data)))
            self.train_data.append(o4r)

    def train(self):
        train_data = list(self.train_data)
        self.train_data.clear()
        self.model_process.do_real_train(train_data)
        # self.generation_id += 1

    def start(self):
        print('start')

    def get_generation_id(self):
        return self.generation_id

    def get_batch_num(self):
        return len(self.train_data)
