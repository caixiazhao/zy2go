# -*- coding: utf8 -*-
import time
import pickle
import hashlib

import requests

from common import cf as C
from util.modelutil import ModelUtil


def push_data(battle_id, model_name, generation_id, data):
    url = 'http://127.0.0.1:8780/data0/%d/%d/%s' % (
        generation_id, battle_id, model_name)
    r = requests.get('http://127.0.0.1:8780/data0/%s/%s',
        data=data)
    return r.text


def if_save_model(model, save_header, save_batch):
    # 训练之后检查是否保存
    replay_time = model.iters_so_far
    if replay_time % save_batch == 0:
        model.save(save_header + str(replay_time) + '/model')


class ModelProcess:
    def __init__(self, battle_id_num):
        self.results = None
        self.save_batch = C.SAVE_BATCH
        self.init_signal = None
        self.lock = None
        self.battle_id_num = battle_id_num
        self.save_dir = ModelUtil.get_save_root_path()

        self.time_cache = []
        self.num_cache = []

        self.model_1, self.model1_save_header, \
        self.model_2, self.model2_save_header = ModelUtil.build_models_ppo(
            self.save_dir,
            model1_path=C.PRELOAD_MODEL1_PATH, model2_path=C.PRELOAD_MODEL2_PATH,
            schedule_timesteps=200000,
            model1_initial_p=0.05, model1_final_p=0.05, model1_gamma=0.95,
            model2_initial_p=0.05, model2_final_p=0.05, model2_gamma=0.95)

        self.train_datas = []

    # 只是将训练数据放入队列, 等长度足够之后，调用_train进行
    # 触发完整训练
    def train(self, battle_id, train_model_name, o4r, batch_size, generation_id):
        o4r['battle_id'] = battle_id
        o4r['generation_id'] = generation_id
        o4r['model_name'] = train_model_name

        print('====train-data====')
        o4rdata = pickle.dumps(o4r)
        print(hashlib.md5(o4rdata).hexdigest())
        r = push_data(battle_id, train_model_name,
            generation_id, o4rdata)
        print(r)
        return

    def do_real_train(self, o4rs):
        o4rs_1 = [ x[2] for x in o4rs if x[1] == C.NAME_MODEL_1]
        o4rs_2 = [ x[2] for x in o4rs if x[1] == C.NAME_MODEL_2]

        begin_time = time.time()
        print ('REAL_TRAIN - model1:%s, model2:%s' % 
            (len(o4rs_1), len(o4rs_2)))
        if len(o4rs_1) > 0:
            self.model_1.replay(o4rs_1, 0)
            if_save_model(self.model_1, self.model1_save_header, self.save_batch)
        if len(o4rs_2) > 0:
            self.model_2.replay(o4rs_2, 0)
            if_save_model(self.model_2, self.model2_save_header, self.save_batch)
        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000

        print('model train time', delta_millionseconds)

    def act(self, battle_id, act_model_name, state_inputs):
        begin_time = time.time()
        if act_model_name == C.NAME_MODEL_1:
            actions_list, explor_value, vpreds = \
                self.model_1.get_actions(state_inputs)
        elif act_model_name == C.NAME_MODEL_2:
            actions_list, explor_value, vpreds = \
                self.model_2.get_actions(state_inputs)

        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        self.time_cache.append(delta_millionseconds)
        self.num_cache.append(len(state_inputs))
        if len(self.time_cache) >= 1000:
            print("model get_action average calculate time(ms)",
                sum(self.time_cache) // float(len(self.time_cache)),
                sum(self.num_cache) / float(len(self.num_cache)))

            self.time_cache.clear()
            self.num_cache.clear()
        return (actions_list, explor_value, vpreds)

    def start(self):
        pass

if __name__ == '__main__':
    model_process = ModelProcess()
    model_process.start()
