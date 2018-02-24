# -*- coding: utf8 -*-
import collections

import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers

import baselines.common.tf_util as U
from baselines import deepq
from baselines.common.schedules import LinearSchedule
from baselines.deepq import PrioritizedReplayBuffer
from baselines.deepq import ReplayBuffer
from train.cmdactionenum import CmdActionEnum
from train.line_input import Line_input
from train.linemodel import LineModel
from util.rewardutil import RewardUtil
from util.stateutil import StateUtil

# 通过模型预测英雄当前状态胜率
# 输入保持和行动模型一致
# 暂时不破坏input的生成逻辑，也就是第一个用户是不包含后续英雄行为信息的
class TeamBattle_WinRate:
    def __init__(self, statesize, actionsize, heros, update_target_period=100, scope="deepq", schedule_timestep=200000, initial_p=1.0, final_p=0.02):
        self.act = None
        self.train = None
        self.update_target = None
        self.debug = None

        self.state_size = statesize
        self.action_size = actionsize
        self.memory = PrioritizedReplayBuffer(500000, alpha=0.6)
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.heros = heros
        self.scope = scope
        self.model = self._build_model

        self.act_times = 0
        self.train_times = 0
        self.update_target_period = update_target_period

        self.exploration = LinearSchedule(schedule_timesteps=schedule_timestep, initial_p=initial_p, final_p=final_p)

        self.battle_rewards = []
        self.loss = []

    def model(self, inpt, scope, reuse=False):
        """This model takes as input an observation and returns values of all actions."""
        with tf.variable_scope(scope, reuse=reuse):
            out = inpt

            out = layers.fully_connected(out, num_outputs=256, activation_fn=None, weights_initializer=U.normc_initializer(1.0))
            axes1 = list(range(len(out.get_shape()) - 1))
            mean1, variance1 = tf.nn.moments(out, axes1)
            out = tf.nn.batch_normalization(out, mean1, variance1, offset=None, scale=None, variance_epsilon=0.001)
            out = tf.nn.relu(out)

            out = layers.fully_connected(out, num_outputs=128, activation_fn=None, weights_initializer=U.normc_initializer(1.0))
            axes2 = list(range(len(out.get_shape()) - 1))
            mean2, variance2 = tf.nn.moments(out, axes2)
            out = tf.nn.batch_normalization(out, mean2, variance2, offset=None, scale=None, variance_epsilon=0.001)
            out = tf.nn.relu(out)

            out = layers.fully_connected(out, num_outputs=128, activation_fn=None, weights_initializer=U.normc_initializer(1.0))
            axes3 = list(range(len(out.get_shape()) - 1))
            mean3, variance3 = tf.nn.moments(out, axes3)
            out = tf.nn.batch_normalization(out, mean3, variance3, offset=None, scale=None, variance_epsilon=0.001)
            out = tf.nn.relu(out)

            # 输出就是一个胜率
            out = layers.fully_connected(out, num_outputs=1, activation_fn=None)
            out = tf.nn.l2_normalize(out, 1)
            return out

    @property
    def _build_model(self):
        sess = U.get_session()
        if sess is None:
            sess = U.make_session(8)
            sess.__enter__()
        self.act, self.train, self.update_target, self.debug = deepq.build_train(
            make_obs_ph=lambda name: U.BatchInput(shape=[2, self.state_size], name=name),
            q_func=self.model,
            num_actions=self.action_size,
            optimizer=tf.train.AdamOptimizer(learning_rate=5e-4),
            scope=self.scope,
            double_q=True,
            param_noise=True
        )

        # 初始化tf环境
        U.initialize()
        self.update_target()

    def load(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.restore(sess, name)

    def save(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.save(sess, name)

    def remember(self, cur_state_input, next_state_input, cur_reward, done):
        self.memory.add(cur_state_input, 0, cur_reward, next_state_input, float(done))
        self.act_times += 1

    def if_replay(self, learning_batch):
        if self.act_times > learning_batch:
            return True
        return False

    def get_memory_size(self):
        return self.act_times

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        obses_t, actions, rewards, obses_tp1, dones, weights, idxes = self.memory.sample(batch_size, beta=0.4)
        td_error, rew_t_ph, q_t_selected_target, q_t_selected = self.train(obses_t, actions, rewards, obses_tp1, dones, weights)
        self.loss.append(np.mean(td_error))
        new_priorities = np.abs(td_error) + 1e-6
        self.memory.update_priorities(idxes, new_priorities)

        self.train_times += 1
        if self.train_times % self.update_target_period == 0:
            print('model', self.scope, 'td_loss', td_error, "rew_t_ph", rew_t_ph, "q_t_selected_target", q_t_selected_target, "q_t_selected",
                  q_t_selected)
            print('model', self.scope, 'loss_mean', np.mean(self.loss))
            self.update_target()

    def get_winrate(self, state_input):
        explor_value = self.exploration.value(self.act_times)
        actions = self.act(state_input, update_eps=explor_value)
        action_detail = ' '.join(str("%.4f" % float(act)) for act in list(actions[0]))
        winrate = actions[0][0]
        print ("win rate: " + action_detail)
        return winrate

