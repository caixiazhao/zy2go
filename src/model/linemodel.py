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



    def attack_cast(self, skill)
        return skill