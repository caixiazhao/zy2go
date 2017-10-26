import threading

from theano.gradient import np

from model.stateinfo import StateInfo
from util.httputil import HttpUtil
from util.linetrainer_ppo import LineTrainerPPO
from util.modelthread import ModelThread
from util.ppocache2 import PPO_CACHE2
from util.singleton import Singleton
import baselines.common.tf_util as U
import json as JSON
import tensorflow as tf


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

    def __init__(self):
        self.model1 = ModelThread(name='model1')
        self.init_model = False

    def response(self, get_data):
        if not self.init_model:
            self.model1.start()
            self.init_model = True

        # sess = U.make_session(8)
        # sess.__enter__()
        # U.initialize()
        # norm = tf.random_normal([2, 3], mean=-1, stddev=4)
        # sess = U.get_session()
        obj = JSON.loads(get_data)
        self.model1.q.put('input')
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
        return ''