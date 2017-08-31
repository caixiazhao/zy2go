# -*- coding: utf8 -*-
import collections

import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers

import baselines.common.tf_util as U
from baselines import deepq
from baselines.common.schedules import LinearSchedule
from baselines.deepq import ReplayBuffer
from baselines.deepq.simple import ActWrapper
from train.line_input import Line_input
from train.linemodel import LineModel


def model(inpt, num_actions, scope, reuse=False):
    """This model takes as input an observation and returns values of all actions."""
    with tf.variable_scope(scope, reuse=reuse):
        out = inpt
        out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.tanh)
        out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.tanh)
        out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
        return out


class LineModel_DQN:
    REWARD_GAMMA = 0.9
    REWARD_DELAY_STATE_NUM = 11
    REWARD_RIVAL_DMG = 300

    def __init__(self, statesize, actionsize, heros, update_target_period=100, scope="deepq"):
        self.act = None
        self.train =None
        self.update_target = None
        self.debug = None

        self.state_size = statesize
        self.action_size = actionsize  # 50=8*mov+10*attack+10*skill1+10*skill2+10*skill3+回城+hold
        self.memory = ReplayBuffer(50000)
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.heros = heros
        self.scope = scope
        self.model = self._build_model

        # todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist = 2

        self.act_times = 0
        self.train_times = 0
        self.update_target_period = update_target_period

        self.exploration = LinearSchedule(schedule_timesteps=10000, initial_p=1.0, final_p=0.02)


    @property
    def _build_model(self):
        self.act, self.train, self.update_target, self.debug = deepq.build_train(
            make_obs_ph=lambda name: U.BatchInput(shape=[self.state_size], name=name),
            q_func=model,
            num_actions=self.action_size,
            optimizer=tf.train.AdamOptimizer(learning_rate=5e-4),
            scope=self.scope
        )

    def load(self, name):
        # baseline目前还不支持checkpoint，加载继续训练
        from baselines import deepq
        self.act = deepq.load(name)._act

    def save(self, name):
        aw = ActWrapper(self.act, None)
        aw.save(name)

    def remember(self, cur_state, new_state):
        for hero_name in self.heros:
            action = cur_state.get_hero_action(hero_name)
            if action is not None:
                selected_action_idx = action.output_index
                reward = action.reward

                # 暂时将1v1的rival_hero 定义为对面英雄
                for hero in cur_state.heros:
                    if hero.hero_name != hero_name:
                        rival_hero = hero.hero_name
                        break

                cur_line_input = Line_input(cur_state, hero_name, rival_hero)
                cur_state_input = cur_line_input.gen_line_input()

                new_line_input = Line_input(new_state, hero_name, rival_hero)
                new_state_input = new_line_input.gen_line_input()

                done = 1 if cur_state.get_hero(hero_name).hp <= 0 else 0

                # 构造一个禁用action的数组
                acts = np.ones(50, dtype=float).tolist()
                new_state_action_flags = LineModel.remove_unaval_actions(acts, new_state, hero_name, rival_hero)

                self.memory.add(cur_state_input, selected_action_idx, reward, new_state_input, float(done),
                                new_state_action_flags)

    def if_replay(self, learning_batch):
        if len(self.memory) > 0 and len(self.memory) % learning_batch == 0:
            return True
        return False

    def get_memory_size(self):
        return len(self.memory)

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        obses_t, actions, rewards, obses_tp1, dones, new_avails = self.memory.sample(batch_size)
        self.train(obses_t, actions, rewards, obses_tp1, dones, np.ones_like(rewards), new_avails)

        self.train_times += 1
        if self.train_times % self.update_target_period == 0:
            self.update_target()

    def get_action(self,stateinformation,hero_name, rival_hero):
        self.act_times += 1

        line_input = Line_input(stateinformation, hero_name, rival_hero)
        state_input = line_input.gen_line_input()

        # input_detail = ' '.join(str("%f" % float(act)) for act in state_input)
        # print(input_detail)

        state_input=np.array([state_input])
        actions = self.act(state_input, update_eps=self.exploration.value(self.act_times))
        # action_detail = ' '.join(str("%.4f" % float(act)) for act in list(actions[0]))

        action=LineModel.select_actions(actions,stateinformation,hero_name, rival_hero)

        # print ("replay detail: selected: %s \n    input array:%s \n    action array:%s\n\n" %
        #        (str(action.output_index), input_detail, action_detail))
        return action
