# -*- coding: utf8 -*-
import random
import collections

import numpy as np
from keras.engine import Input, Model
from keras.layers import Dense, LSTM, Reshape, concatenate, Concatenate

from keras.models import Sequential
from keras.optimizers import RMSprop, Nadam
from keras.layers import Dropout,Conv1D

from src.model.stateinfo import StateInfo
from src.model.herostateinfo import HeroStateInfo


class linemodel:
    REWARD_GAMMA = 0.9

    def __init__(self, statesize, actionsize, hero_name):
        self.state_size = statesize
        #TODO:need to be settled
        self.action_size = actionsize #24
        self.memory = collections.deque()
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.hero_name=hero_name
        self.model = self._build_model

    @property
    def _build_model(self):


        #battle_map=Input(shape=())
        #TODO:for multi-input model, we may use a map as input
        battle_information=Input(shape=())
        #to store the information of buildings, monsters, creeps and heroes.
        #TODO:input shape need check
        dense_1=Dense(512,activation='relu')(battle_information)
        dropped_1=Dropout(0.15)(dense_1)
        dense_2=Dense(256,activation='relu')(dropped_1)
        dropped_2=Dropout(0.15)(dense_2)
        lstm=LSTM(128)(dropped_2)
        # TODO:check the data form
        dense_3 = Dense(64, activation='relu')(lstm)
        dropped_3 = Dropout(0.15)(dense_3)

        predictions = Dense(self.action_size, activation='softmax')(dropped_3)
        model = Model(inputs=battle_information, outputs=predictions)
        model.compile(loss='mse', optimizer=Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004))
        return model

    def select_actions(self, acts, stateinformation):
        # acts is the vector of q-values, hero_information contains the ID,location, and other information we may need
        flag = True
        while flag:
            maxQ = max(acts)
            selected = acts.index(maxQ)
            if selected < 8:  #move
                fwd = self.mov(selected)
                action = "MOV"
                return action, fwd
            elif selected < 16:  #闪现
                fwd = self.mov(selected - 8)
                action = "CAST"
                skillid = 64141
                hero_pos=stateinformation.get_hero_pos(self.hero_name)
                tgtpos = list(np.array(fwd) + np.array(hero_pos))
                # need to get the hero_pos
                return action, skillid, tgtpos
            elif selected ==16:   #放草，烧，加速，三个不用管目标的技能
                action = "CAST"
                skillid=202
                tgtpos=stateinformation.get_hero_pos(self.hero_name)
                #get current hero position
                #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
                return action,skillid,tgtpos
            elif selected==17:
                action="CAST"
                skillid=61141
                tgtpos=stateinformation.get_hero_pos(self.hero_name)
                #GET CURRENT HERO POS
                return action,skillid,tgtpos
            elif selected==19:
                action="CAST"
                skillid=64142
                tgtpos=stateinformation.get_hero_pos(self.hero_name)
                #get pos
                return action,skillid,tgtpos
            elif selected==


                #TODO ...

        return selected

    # 计算对线情况下每次行动的效果反馈
    # 因为有些效果会产生持续的反馈（比如多次伤害，持续伤害，buff状态等），我们评估5s内所有的效果的一个加权值
    # 其中每一帧的效果评估方式为：我方获得金币数量x(我方血量变化比率+我方附近塔血量变化比率) A 和 对方获得金币x(对方血量变化比率+对方附近塔血量变化比率) B 的比例关系
    # A/(A + B)
    @staticmethod
    def cal_target_4_line(state_infos, state_idx, hero_names, if_team_a):
        prev_state = state_infos[state_idx]

        reward_per_states = []
        for i in range(1, 10):
            cur_state = state_infos[state_idx + i]

            # 将传入的英雄分为两个阵容，计算两个阵营之间的奖励比率，根据if_team_a决定返回哪个阵营的比例
            gain_team_a = 0
            gain_team_b = 0
            for hero_name in hero_names:
                prev_hero = prev_state.get_hero(hero_name)
                cur_hero = cur_state.get_hero(hero_name)

                # 这里考虑血量变化，如果血量提高则会有奖励（所以回城也会有奖励系数)
                # 逻辑上忽略升级带来的一点点变化
                hp_delta = (int(cur_hero.hp) - int(prev_hero.hp)) / float(cur_hero.maxhp)

                # 得到金币变化，如果是消灭了对方小兵，或者英雄，金币上会有个显著的变化
                # 对于死亡，相应的对方会有个金币的提升，暂时不考虑击杀被击杀的额外惩罚了吧
                #TODO 这里需要考虑装备情况
                gold_delta = int(cur_hero.gold) - int(prev_hero.gold)

                gain = gold_delta * (1 + hp_delta)
                if cur_hero.team == 0:
                    gain_team_a += gain
                else:
                    gain_team_b += gain

            reward = gain_team_a / float(gain_team_a + gain_team_b) if if_team_a else gain_team_b / float(gain_team_a + gain_team_b)
            reward_per_states.append(reward)

        # 根据衰减系数来得到总的奖励值
        total_reward = 0
        for reward in reversed(reward_per_states):
            total_reward = total_reward * linemodel.REWARD_GAMMA + reward

        return total_reward

    def mov(self, direction):
        if direction == 0:
            return [1000, 0, 0]
        elif direction == 1:
            return [707, 0, 707]
        elif direction == 2:
            return [0, 0, 1000]
        elif direction == 3:
            return [-707, 0, 707]
        elif direction == 4:
            return [0, 0, -1000]
        elif direction == 5:
            return [-707, 0, -707]
        elif direction == 6:
            return [-1000, 0, 0]
        else:
            return [-707, 0, 707]

        # the input is 0~8 and the output will be a vector that indicate the direction
        return direction

    def attack_cast(self, skill):
        return skill
