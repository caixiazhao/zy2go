# -*- coding: utf8 -*-
import sys
# import queue
import time

from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
from util.httputil import HttpUtil
# from multiprocessing import Process, Manager, Value, Array, Lock, Queue, Event


def if_save_model(model, save_header, save_batch):
    # 训练之后检查是否保存
    replay_time = model.iters_so_far
    if replay_time % save_batch == 0:
        model.save(save_header + str(replay_time) + '/model')


class ModelProcess:
    NAME_MODEL_1 = 'model_1'
    NAME_MODEL_2 = 'model_2'

    def __init__(self, battle_id_num):
        self.action_queue = None
        self.train_queue = None
        self.results = None
        self.save_batch = 10
        self.init_signal = None
        self.lock = None
        self.battle_id_num = battle_id_num
        self.save_dir = HttpUtil.get_save_root_path()

        self.time_cache = []
        self.num_cache = []

        self.model_1, self.model1_save_header, \
        self.model_2, self.model2_save_header = HttpUtil.build_models_ppo(
            self.save_dir,
            model1_path=None, model2_path=None, schedule_timesteps=200000,
            model1_initial_p=0.05, model1_final_p=0.05, model1_gamma=0.95,
            model2_initial_p=0.05, model2_final_p=0.05, model2_gamma=0.95)


    def train(self, battle_id, train_model_name, o4r, batch_size):
        o4r_list_model1 = {}
        o4r_list_model2 = {}

        print('model_process', battle_id, train_model_name,
            'receive train signal, batch size', batch_size)
        if train_model_name == ModelProcess.NAME_MODEL_1:
            o4r_list_model1[battle_id] = o4r
            print('model_process model1 train collection',
                ';'.join((str(k) for k in o4r_list_model1.keys())))
        elif train_model_name == ModelProcess.NAME_MODEL_2:
            o4r_list_model2[battle_id] = o4r
            print('model_process model2 train collection',
                ';'.join((str(k) for k in o4r_list_model2.keys())))

        print('model_process1', train_model_name, 'begin to train')
        begin_time = time.time()
        self.model_1.replay(o4r_list_model1.values(), batch_size)
        o4r_list_model1.clear()

        # 由自己来决定什么时候缓存模型
        if_save_model(
            self.model_1, self.model1_save_header, self.save_batch)
        print('model_process2', train_model_name, 'begin to train')
        self.model_2.replay(o4r_list_model2.values(), batch_size)
        o4r_list_model2.clear()
        end_time = time.time()

        delta_millionseconds = (end_time - begin_time) * 1000
        print('model train time', delta_millionseconds)
        # 由自己来决定什么时候缓存模型
        if_save_model(
            self.model_2, self.model2_save_header, self.save_batch)
        trained = True

        restartCmd = CmdAction(
            ModelProcess.NAME_MODEL_1, CmdActionEnum.RESTART, 0,
            None, None, None, None, None, None)
        return (restartCmd, None, None)

    def act(self, battle_id, act_model_name, state_inputs):
        begin_time = time.time()
        if act_model_name == ModelProcess.NAME_MODEL_1:
            actions_list, explor_value, vpreds = \
                self.model_1.get_actions(state_inputs)
        elif act_model_name == ModelProcess.NAME_MODEL_2:
            actions_list, explor_value, vpreds = \
                self.model_2.get_actions(state_inputs)

        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        self.time_cache.append(delta_millionseconds)
        self.num_cache.append(len(state_inputs))
        if len(self.time_cache) >= 1000:
            print("model get_action average calculate time(ms)",
                sum(self.time_cache) // float(len(self.self.time_cache)),
                sum(self.num_cache) / float(len(self.num_cache)))

            self.time_cache.clear()
            self.num_cache.clear()
        return (actions_list, explor_value, vpreds)

    def start(self):
        pass


if __name__ == '__main__':
    model_process = ModelProcess()
    model_process.start()
