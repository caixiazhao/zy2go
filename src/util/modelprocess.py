# -*- coding: utf8 -*-
import os
import shutil

import time
import pickle
import hashlib

import requests
import tensorflow as tf
import baselines.common.tf_util as U
from common import cf as C
from util.modelutil import ModelUtil
from train.linemodel_ppo1 import LineModel_PPO1


def push_data(battle_id, model_name, generation_id, data):
    url = 'http://127.0.0.1:8780/data/%d/%d/%s' % (
        generation_id, battle_id, model_name)
    r = requests.get(url, data=data)
    return r.text

def model_data():
    url = 'http://127.0.0.1:%d/data/model' % (C.GATEWAY_PORT)
    r = requests.get(url)
    list = pickle.loads(r.content)

    return list


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

        self.model_1 = None # type: LineModel_PPO1
        self.model_2 = None # type: LineModel_PPO1
        self.model_1, self.model1_save_header, \
        self.model_2, self.model2_save_header = ModelUtil.build_models_ppo(
            self.save_dir,
            model1_path=C.PRELOAD_MODEL1_PATH, model2_path=C.PRELOAD_MODEL2_PATH,
            schedule_timesteps=200000,
            model1_initial_p=0.05, model1_final_p=0.05, model1_gamma=0.95,
            model2_initial_p=0.05, model2_final_p=0.05, model2_gamma=0.95)

        self.generation_id = 0
        self.train_datas = []

    # 只是将训练数据放入队列, 等长度足够之后，调用_train进行
    # 触发完整训练
    def train(self, battle_id, train_model_name, o4r, batch_size, generation_id, server_id):
        o4r['battle_id'] = (server_id -1)*100+battle_id
        o4r['generation_id'] = generation_id
        o4r['model_name'] = train_model_name

        o4rdata = pickle.dumps(o4r)
        digest = hashlib.md5(o4rdata).hexdigest()
        print('%s push-data %d g:%d m:%s - %d %s' % (
            time.strftime('%H:%M:%S'),
            battle_id,
            generation_id,
            train_model_name,
            len(o4rdata), digest))

        r = push_data(battle_id, train_model_name,
            generation_id, o4rdata)

        gateway_generation_id = int(r)
        if self.generation_id == gateway_generation_id:
            return

        if C.LOG['GENERATION_UPDATE']:
            print('%s generation update P3 %d - process %d:%d' % (
                time.strftime('%H:%M:%S'),
                battle_id,
                self.generation_id, gateway_generation_id))
        self.update_model_from_disk(gateway_generation_id)
        C.set_generation_id(gateway_generation_id)

        return

    def do_real_train(self, o4rs, model_name):
        begin_time = time.time()
        print('REAL_TRAIN - model:%s - model_name:%s' %
              (len(o4rs), model_name))
        if model_name == C.NAME_MODEL_1:
            self.model_1.replay(o4rs, 0)
            if_save_model(self.model_1, self.model1_save_header, self.save_batch)
        else:
            self.model_2.replay(o4rs, 0)
            if_save_model(self.model_2, self.model2_save_header, self.save_batch)
        end_time = time.time()
        delta_millisecond = (end_time - begin_time) * 1000
        print('model train time', delta_millisecond)

    def act(self, battle_id, act_model_name, state_inputs):
        begin_time = time.time()
        if act_model_name == C.NAME_MODEL_1:
            actions_list, explor_value, vpreds = \
                self.model_1.get_actions(state_inputs)
        elif act_model_name == C.NAME_MODEL_2:
            actions_list, explor_value, vpreds = \
                self.model_2.get_actions(state_inputs)
        else:
            actions_list, explor_value, vpreds = None, None, None

        end_time = time.time()
        delta_millisecond = (end_time - begin_time) * 1000
        self.time_cache.append(delta_millisecond)
        self.num_cache.append(len(state_inputs))
        if len(self.time_cache) >= 1000:
            print("model get_action average calculate time(ms)",
                sum(self.time_cache) // float(len(self.time_cache)),
                sum(self.num_cache) / float(len(self.num_cache)))

            self.time_cache.clear()
            self.num_cache.clear()
        return actions_list, explor_value, vpreds

    def dump_model_to_disk(self, generation_id):
        self.generation_id = generation_id
        base_path = os.path.join(C.DATA_ROOT_PATH, "trainer", str(generation_id))
        if os.path.isdir(base_path):
            shutil.rmtree(base_path)
        os.makedirs(base_path)
       # self.model_1.save(base_path + '/1/1')
       # self.model_2.save(base_path + '/2/2')

    def update_model_from_disk(self, generation_id):
        self.generation_id = generation_id
        #确保不会因为请求超时 无法获得模型变量，更新模型
        try:
            while True:
                list = model_data()
                if len(list) == 2:
                    model1_var = list[0]
                    model2_var = list[1]
                    for i in range(len(model1_var)):
                        oldv1 = self.model_1.pi.get_variables()[i]
                        newv1 = tf.placeholder(dtype=tf.float32)
                        assign_old_eq_new = U.function([newv1], [], updates=[tf.assign(oldv1, newv1)])
                        assign_old_eq_new(model1_var[i])
                    for i in range(len(model2_var)):
                        oldv1 = self.model_2.pi.get_variables()[i]
                        newv1 = tf.placeholder(dtype=tf.float32)
                        assign_old_eq_new = U.function([newv1], [], updates=[tf.assign(oldv1, newv1)])
                        assign_old_eq_new(model2_var[i])
                    break

        except Exception as ex:
            print(ex)
            return 0


    def start(self):
        pass


if __name__ == '__main__':
    model_process = ModelProcess(1)
    model_process.start()
