# -*- coding: utf8 -*-
import sys
# import queue
import time

import pickle


from common import cf as C
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
    def __init__(self, battle_id_num):
        self.action_queue = None
        self.train_queue = None
        self.results = None
        self.save_batch = C.SAVE_BATCH
        self.init_signal = None
        self.lock = None
        self.battle_id_num = battle_id_num
        self.save_dir = HttpUtil.get_save_root_path()

        self.time_cache = []
        self.num_cache = []

        self.model_1, self.model1_save_header, \
        self.model_2, self.model2_save_header = HttpUtil.build_models_ppo(
            self.save_dir,
            model1_path=C.PRELOAD_MODEL1_PATH, model2_path=C.PRELOAD_MODEL2_PATH,
            schedule_timesteps=200000,
            model1_initial_p=0.05, model1_final_p=0.05, model1_gamma=0.95,
            model2_initial_p=0.05, model2_final_p=0.05, model2_gamma=0.95)

        self.train_datas = []

    # 只是将训练数据放入队列, 等长度足够之后，调用_train进行
    # 触发完整训练
    def train(self, battle_id, train_model_name, o4r, batch_size):
        print('====train-data====')
        print(len(pickle.dumps(o4r)))

        self.train_datas.append((battle_id, train_model_name, o4r, batch_size))
        print('model_process train-queue: %s/%s batchsize:%d -- %s/%s' %(
            battle_id, train_model_name, batch_size, 
            len(self.train_datas), C.TRAIN_GAME_BATCH))

        if len(self.train_datas) >= C.TRAIN_GAME_BATCH:
            self._train()

        #restartCmd = CmdAction(
        #    C.NAME_MODEL_1, CmdActionEnum.RESTART, 0,
        #    None, None, None, None, None, None)
        #return (restartCmd, None, None)


    def _train(self):
        o4rs_1 = [ x[2] for x in self.train_datas if x[1] == C.NAME_MODEL_1]
        o4rs_2 = [ x[2] for x in self.train_datas if x[1] == C.NAME_MODEL_2]
        self.train_datas.clear()

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
