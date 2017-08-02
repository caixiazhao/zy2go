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
        #to store the information of buildings,creeps and heroes.
        #现在英雄信息包含2*21个属性，技能2*3*15，塔9~11，小兵16*（9~11），输入应为一个固定长度向量
        #预测长度应该在300左右
        #TODO:input shape need check,
        dense_1=Dense(512,activation='relu')(battle_information)
        dropped_1=Dropout(0.15)(dense_1)
        dense_2=Dense(256,activation='relu')(dropped_1)
        dropped_2=Dropout(0.15)(dense_2)
        lstm=LSTM(128)(dropped_2)
        # TODO:check the data form
        dense_3 = Dense(64, activation='relu')(lstm)
        dropped_3 = Dropout(0.15)(dense_3)

        predictions = Dense(self.action_size, activation='softmax')(dropped_3)
        #输出为一个q-value的向量，代表各个行为的概率，预计长为59
        model = Model(inputs=battle_information, outputs=predictions)
        model.compile(loss='mse', optimizer=Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004))
        return model

    def remember(self, state_info):
        self.memory.append(state_info)

    def replay(self,batch_size):
        batch_size = min(batch_size, len(self.memory))
        #todo: to be continue

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
                #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
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
                #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
                return action,skillid,tgtpos
            elif selected==19:
                action="CAST"
                skillid=64142
                tgtpos=stateinformation.get_hero_pos(self.hero_name)
                #todo: if can use, return, if not ,continue to the next loop
                return action,skillid,tgtpos
            elif selected==20:  #对敌英雄使用变形#
                action="CAST"
                skillid=611041
                # 现在是中线1v1，使用不涉及选择对方某一个英雄，只有一个非己方的英雄作为目标，
                # 后期可能要加上信息来选择当前作为对手的目标英雄，或者对于对线模型使用对线stateinfo取代全局stateinfo，
                # 舍弃掉部分信息在保存在模型中
                for hero in stateinformation.heros:
                    if hero.hero_name!= self.hero_name:
                        tgtid=hero.id
                        #todo:这里的id应该是指 27~36， name是指101,102这种，但是现在的heroinfo当中并没有看到保存id
                # todo: if can use, return, if not ,continue to the next loop
                return action, skillid, tgtid
            elif selected== #对敌英雄，塔，敌小兵1~8使用普攻；对敌我英雄，敌小兵1~8使用技能1~3


                #TODO ...

        return selected

    # 计算对线情况下每次行动的效果反馈
    # 因为有些效果会产生持续的反馈（比如多次伤害，持续伤害，buff状态等），我们评估5s内所有的效果的一个加权值
    # 其中每一帧的效果评估方式为：我方获得金币数量x(我方血量变化比率+我方附近塔血量变化比率) A 和 对方获得金币x(对方血量变化比率+对方附近塔血量变化比率) B 的比例关系
    # A/(A + B)
    @staticmethod
    def cal_target_4_line(state_infos, state_idx, hero_name):
        prev_state = state_infos[state_idx]
        for i in range(1, 10):
            cur_state = state_infos[state_idx + i]
            prev_hero =(state)



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
