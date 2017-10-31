import threading

import time
import json as JSON
import numpy as np

from model.stateinfo import StateInfo
from util.linetrainer_ppo import LineTrainerPPO
from util.modelthread import ModelThread
from util.ppocache2 import PPO_CACHE2
from util.singleton import Singleton


class LineTrainerManager(metaclass=Singleton):
    # sess = U.make_session(8)
    # sess.__enter__()
    # U.initialize()
    # line_trainers = {}
    # norm = tf.random_normal([2, 3], mean=-1, stddev=4)

    # save_dir, model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(
    #     model1_path=None,
    #     model2_path=None,
    #     schedule_timesteps=200000,
    #     model1_initial_p=0.05,
    #     model1_final_p=0.05,
    #     model2_initial_p=0.05,
    #     model2_final_p=0.05,
    #     )
    model_thread = ModelThread(name='model1')
    init_model = False
    line_trainers = {}
    using_line_trainers = []
    lock = threading.Lock()

    def response(self, get_data):
        # 首先启动模型线程，注意这里需要等待模型加载完毕之后再开始服务
        # 不知道为什么后续模型线程的初始化和启动必须在这里进行，否则会出现线程其实没有启动起来的情况
        with self.lock:
            if not self.init_model:
                self.init_model = True
                print("model start")
                self.model_thread.start()
                self.model_thread.init_signal.wait(200)

        obj = JSON.loads(get_data)
        raw_state_info = StateInfo.decode(obj)
        battle_id = raw_state_info.battleid

        with self.lock:
            if battle_id not in self.line_trainers.keys():
                print(battle_id, '开始创建')
                ob = np.zeros(183, dtype=float).tolist()
                model1_cache = PPO_CACHE2(ob, 1)
                model2_cache = PPO_CACHE2(ob, 1)
                save_dir = self.model_thread.save_dir
                model1_hero = '27'
                model2_hero = '28'
                self.line_trainers[battle_id] = LineTrainerPPO(
                                battle_id, save_dir, self.model_thread, model1_hero,
                                model1_cache, model2_hero, model2_cache,
                                real_hero=None, policy_ratio=-1, policy_continue_acts=3)
        # 取得训练器
        line_trainer = None
        with self.lock:
            if battle_id not in self.using_line_trainers:
                line_trainer = self.line_trainers[battle_id]
                self.using_line_trainers.append(battle_id)

        if line_trainer is not None:
            rsp_str = line_trainer.train_line_model(get_data)
            print(rsp_str)
            rsp_str = rsp_str.encode(encoding="utf-8")
            #TODO 这里有个问题，如果处理请求时候出现异常，会跳过这里的删除using标志的逻辑，导致这场战斗的训练器持续的被占用
            with self.lock:
                self.using_line_trainers.remove(battle_id)
            return rsp_str
        else:
            # 如果当前训练器正在被使用，直接返回空，本次请求超时，这样客户端会继续重试，直到训练器返回为止
            # 以为客户端会立即发送重试请求，为了减少负载，这里首先休眠一段时间
            time.sleep(0.5)
            print(battle_id, '被占用，直接返回')
            return ''

        # if battle_id not in self.using_line_trainers:
        #     line_trainer = self.line_trainers[get_data]
        #     self.using_line_trainers.append(get_data)
        #     # 这里假装处理一段时间
        #     print(get_data, '正在处理')
        #     self.model1.action_queue.put(get_data)
        #     while True:
        #         self.model1.done_signal.wait(1)
        #         # check package
        #         if get_data in self.model1.results:
        #             result = self.model1.results.pop(get_data)
        #             break
        #     print(get_data, result)
        #     self.using_line_trainers.remove(get_data)
        #     return line_trainer
        # else:
        #     # 如果当前训练器正在被使用，直接返回空，本次请求超时，这样客户端会继续重试，直到训练器返回为止
        #     print(get_data, '被占用，直接返回')
        #     return None

        # sess = U.make_session(8)
        # sess.__enter__()
        # U.initialize()
        # norm = tf.random_normal([2, 3], mean=-1, stddev=4)
        # sess = U.get_session()
        # obj = JSON.loads(get_data)
        # self.model1.q.put('input')
        # rsp_str = sess.run(norm)
        # raw_state_info = StateInfo.decode(obj)
        # if raw_state_info.battleid not in self.line_trainers:
        #     # PPO
        #     ob = np.zeros(183, dtype=float).tolist()
        #     model1_cache = PPO_CACHE2(ob, 1, horizon=self.model_1.optim_batchsize)
        #     model2_cache = PPO_CACHE2(ob, 1, horizon=self.model_2.optim_batchsize)
        #     self.line_trainers[raw_state_info.battleid] = LineTrainerPPO(self.save_dir, '27', self.model_1,
        #                                                                  self.model1_save_header, model1_cache,
        #                                                                  '28', self.model_2, self.model2_save_header,
        #                                                                  model2_cache, real_hero=None,
        #                                                                  policy_ratio=-1, policy_continue_acts=3)
        # # 交给对线训练器来进行训练
        # rsp_str = self.line_trainers[raw_state_info.battleid].train_line_model(get_data)
