# -*- coding: utf8 -*-
import random
import collections

import numpy as np
from keras.engine import Input, Model
from keras.layers import Dense, LSTM, Reshape

from keras.models import Sequential
from keras.optimizers import RMSprop, Nadam
from keras.layers import Dropout,Conv1D

from src.model.stateinfo import StateInfo
from src.model.herostateinfo import HeroStateInfo
from src.util.replayer import Replayer as rp
from src.model.line_input import Line_input
import random

from util.stateutil import StateUtil


class linemodel:
    REWARD_GAMMA = 0.9

    def __init__(self, statesize, actionsize, hero_name):
        self.state_size = statesize
        #TODO:need to be settled
        self.action_size = actionsize #48=8*mov+10*attack+10*skill1+10*skill2+10*skill3
        self.memory = collections.deque()
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.model = self._build_model

        self.hero_name = hero_name
        #todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist=2
        #todo:以下仅为英雄1技能距离，后续需将这些信息加入到skillinfo中
        self.skilldist=[8,6,5]


    @property
    def _build_model(self):


        #battle_map=Input(shape=())
        #TODO:for multi-input model, we may use a map as input
        battle_information=Input(shape=(240,))
        #to store the information of buildings,creeps and heroes.
        #现在英雄信息包含2*21个属性，技能2*3*15，塔9~11，小兵16*（9~11），输入应为一个固定长度向量
        #预测长度应该在300左右
        #TODO:input shape need check,
        dense_1=Dense(512,activation='relu')(battle_information)
        dropped_1=Dropout(0.15)(dense_1)
        dense_2=Dense(256,activation='relu')(dropped_1)
        dropped_2=Dropout(0.15)(dense_2)
        reshaped = Reshape((256, 1))(dropped_2)
        lstm=LSTM(128)(reshaped)
        # TODO:check the data form
        dense_3 = Dense(64, activation='relu')(lstm)
        dropped_3 = Dropout(0.15)(dense_3)

        predictions = Dense(self.action_size, activation='softmax')(dropped_3)
        model = Model(inputs=battle_information, outputs=predictions)
        model.compile(loss='mse', optimizer=Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004))
        return model

    def remember(self, state_info):
        self.memory.append(state_info)

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        index_range = range(len(self.memory))
        minibatch = random.sample(index_range, batch_size)
        X = np.zeros((batch_size, self.state_size))
        Y = np.zeros((batch_size, self.action_size))
        for i in range(batch_size):
            sample_index = minibatch[i]
            stateInformation = self.memory[sample_index]

            # 这里应该是选择reward更大的一方作为训练对象
            # 默认只有两个英雄
            action_index = 0 if stateInformation.actions[0].reward > stateInformation.actions[1].reward else 1
            hero_name = stateInformation.actions[action_index].hero_name
            line_input = Line_input(stateInformation, hero_name)
            state = line_input.gen_input()

            # 得到模型预测结果
            target = self.model.predict(state)

            # 修改其中我们选择的行为
            choson_action = stateInformation.actions[action_index]
            target[0][choson_action.output_index] = choson_action.reward

            X[i], Y[i] = state, target
        self.model.fit(X, Y, batch_size=batch_size, nb_epoch=1, verbose=0)
        if self.epsilon > self.e_min:
            self.epsilon *= self.e_decay

    # def select_actions(self, acts, stateinformation):
    #     #这样传stateinformation太拖慢运行速度了，后面要改
    #     # acts is the vector of q-values, hero_information contains the ID,location, and other information we may need
    #     flag = True
    #     while flag:
    #         maxQ = max(acts)
    #         selected = acts.index(maxQ)
    #         if selected < 8:  #move
    #             fwd = self.mov(selected)
    #             action = "MOV"
    #             return [action, fwd]
    #         elif selected < 16:  #闪现
    #             fwd = self.mov(selected - 8)
    #             action = "CAST"
    #             skillid = 64141
    #             hero_pos=stateinformation.get_hero_pos(self.hero_name)
    #             tgtpos = list(np.array(fwd) + np.array(hero_pos))
    #             #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
    #             return [action, skillid, tgtpos]
    #         elif selected ==16:   #放草，烧，加速，三个不用管目标的技能
    #             action = "CAST"
    #             skillid=202
    #             tgtpos=stateinformation.get_hero_pos(self.hero_name)
    #             #get current hero position
    #             #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
    #             return [action,skillid,tgtpos]
    #         elif selected==17:
    #             action="CAST"
    #             skillid=61141
    #             tgtid=self.heroname
    #             #todo：判断该技能是否可用，可用返回，不可用跳过，选可能性排在这个技能之后的选择
    #             return [action,skillid,tgtid]
    #         elif selected==18:
    #             action="CAST"
    #             skillid=64142
    #             tgtid=self.hero_name
    #             #todo: if can use, return, if not ,continue to the next loop
    #             return [action,skillid,tgtid]
    #         elif selected==19:  #对敌英雄使用变形#
    #             action="CAST"
    #             skillid=611041
    #             # 现在是中线1v1，使用不涉及选择对方某一个英雄，只有一个非己方的英雄作为目标，
    #             # 后期可能要加上信息来选择当前作为对手的目标英雄，或者对于对线模型使用对线stateinfo取代全局stateinfo，
    #             # 舍弃掉部分信息在保存在模型中
    #             for hero in stateinformation.heros:
    #                 if hero.hero_name!= self.hero_name:
    #                     tgtid=hero.hero_name
    #             # todo: if can use, return, if not ,continue to the next loop
    #             return [action, skillid, tgtid]
    #         elif selected<30: #对敌英雄，塔，敌小兵1~8使用普攻；对敌我英雄，敌小兵1~8使用技能1~3
    #             action="ATTACK"
    #             if selected==20:
    #                 tgtid=self.get_tower_temp(stateinformation)
    #                 return [action,tgtid]
    #             elif selected==21:
    #                 for hero in stateinformation.heros:
    #                     if hero.hero_name!= self.hero_name:
    #                         tgtid=hero.hero_name
    #                 return  [action,tgtid]
    #             else:
    #                 creeps=rp.get_nearby_enemy_units(stateinformation,self.hero_name)
    #                 n=selected-22
    #                 tgtid=creeps[n].unit_name
    #                 return  [action,tgtid]
    #         elif selected<40: #skill1
    #             action="CAST"
    #             for hero in stateinformation.heros:
    #                 if hero.hero_name==self.hero_name:
    #                     skillid=hero.skills[1].skillid
    #             if selected==30: #use on itself, skill like buff, recover or somthing like that
    #                 tgtid=self.hero_name
    #             elif selected==31:
    #
    #         elif selected<50: #skill2
    #
    #         else:
    #
    #
    #
    #
    #
    #
    #     return ["HOLD"]

    def select_actions(self, acts, stateinformation):
        #这样传stateinformation太拖慢运行速度了，后面要改
        # acts is the vector of q-values, hero_information contains the ID,location, and other information we may need
        for hero in stateinformation.heros:
            if hero.hero_name==self.hero_name:
                self.hero=hero
        acts=acts[0]
        acts=list(acts)
        for i in range(len(acts)):
            maxQ = max(acts)

            selected = acts.index(maxQ)
            #每次取当前q-value最高的动作执行，若当前动作不可执行则将其q-value置为0，重新取新的最高
            if random.random()<0.15:
                #随机策略，选择跳过当前最优解
                acts[selected]=0
                continue
            if selected < 8:  #move
                if self.hero.movelock == True:
                    #英雄可以移动
                    acts[selected] = 0
                    continue
                fwd = self.mov(selected)
                action = "MOV"
                return [action, fwd]
            elif selected<18: #对敌英雄，塔，敌小兵1~8使用普攻；对敌我英雄，敌小兵1~8使用技能1~3
                if self.hero.skills[0].canuse!=True:
                    #被控制住
                    acts[selected]=0
                    continue
                action="ATTACK"
                if selected==8:
                    tower=self.get_tower_temp(stateinformation)
                    dist=StateUtil.cal_distance(self.hero.pos,tower.pos)
                    if dist>self.att_dist:
                        acts[selected]=0
                        continue
                    tgtid=tower.unit_name
                    return [action,tgtid]
                elif selected==9:
                    for hero in stateinformation.heros:
                        if hero.hero_name!= self.hero_name:
                            tgtid=hero.hero_name
                            break
                    dist=StateUtil.cal_distance(self.hero.pos,hero.pos)
                    if dist>self.att_dist:
                        acts[selected]=0
                        continue
                    return  [action,tgtid]
                else:
                    creeps=StateUtil.get_nearby_enemy_units(stateinformation,self.hero_name)
                    n=selected-10
                    if n>=len(creeps):
                        #没有这么多小兵
                        acts[selected]=0
                        continue
                    dist=StateUtil.cal_distance(self.hero.pos,creeps[n].pos)
                    if dist > self.att_dist:
                        acts[selected]=0
                        continue
                    tgtid=creeps[n].unit_name
                    return  [action,tgtid]
            elif selected<28: #skill1
                if self.hero.skills[1].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    acts[selected]=0
                    continue
                if self.hero.skills[1].cost>self.hero.mp:
                    #mp不足
                    acts[selected]=0
                    continue
                if self.hero.skills[1].cd>0:
                    #技能未冷却
                    acts[selected]=0
                    continue
                action="CAST"
                skillid=1
                tgtid=self.choose_skill_target(selected-18,stateinformation,1)
                if tgtid==-1:
                    #目标在施法范围外
                    acts[selected]=0
                    continue
                return [action,skillid,tgtid]
            elif selected<38: #skill2
                if self.hero.skills[2].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    acts[selected]=0
                    continue
                if self.hero.skills[2].cost>self.hero.mp:
                    #mp不足
                    acts[selected]=0
                    continue
                if self.hero.skills[2].cd>0:
                    #技能未冷却
                    acts[selected]=0
                    continue
                action = "CAST"
                skillid = 2
                tgtid = self.choose_skill_target(selected - 28,stateinformation,2)
                if tgtid==-1:
                    #目标在施法范围外
                    acts[selected]=0
                    continue
                return [action, skillid, tgtid]
            else:
                if self.hero.skills[3].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    acts[selected]=0
                    continue
                if self.hero.skills[3].cost>self.hero.mp:
                    #mp不足
                    acts[selected]=0
                    continue
                if self.hero.skills[3].cd>0:
                    #技能未冷却
                    acts[selected]=0
                    continue
                action = "CAST"
                skillid = 3
                tgtid = self.choose_skill_target(selected - 38,stateinformation,3)
                if tgtid==-1:
                    #目标在施法范围外
                    acts[selected]=0
                    continue
                return [action, skillid, tgtid]
        return ["HOLD"]

    def choose_skill_target(self, selected,stateinformation, skill):
        if selected==0:
            tgtid =self.hero_name
        elif selected==1:
            for hero in stateinformation.heros:
                if hero.hero_name != self.hero_name:
                    if StateUtil.cal_distance(hero.pos,self.hero.pos)>self.skilldist[skill-1]:
                        tgtid=-1
                    else:
                        tgtid = hero.hero_name
        else:
            creeps=StateUtil.get_nearby_enemy_units(stateinformation, self.hero_name)
            n=selected-2
            if n >= len(creeps):
                # 没有这么多小兵
                return -1
            elif StateUtil.cal_distance(self.hero.pos,creeps[n].pos)>self.skilldist[skill-1]:
                tgtid=-1
            else:
                tgtid=creeps[n].unit_name
        return tgtid

    def get_tower_temp(self, stateinformation):#一个临时的在中路判断哪个塔可以作为目标的函数
        # 这样传stateinformation太拖慢运行速度了，后面要改
        for unit in stateinformation.units:
            if unit.unit_name=='15' and unit.state=="in":
                return unit
            elif unit.unit_name=='16' and unit.state=="in":
                return unit
            elif unit.unit_name=='17' and unit.state=="in":
                return unit
            elif int(unit.unit_name)>17:
                break
        for unit in stateinformation.units:
            if unit.unit_name=="1" and unit.state=="in":
                return unit
            elif unit.unit_name=="2" and unit.state=="in":
                return unit
            elif unit.unit_name=="7":
                return unit

    def get_action(self,stateinformation):
        # 这样传stateinformation太拖慢运行速度了，后面要改
        line_input = Line_input(stateinformation, self.hero_name)
        state = line_input.gen_input()
        state=np.array([state])
        actions=self.model.predict(state)
        action=self.select_actions(actions,stateinformation)
        return action

    # 当一场战斗结束之后，根据当时的状态信息，计算每一帧的奖励情况
    @staticmethod
    def update_rewards(state_infos, start_index, end_index):
        result = []
        for i in range(start_index, end_index):
            state_info = state_infos[start_index]
            hero_names = [state_info.heros[0].hero_name, state_info.heros[1].hero_name]
            reward_map = linemodel.cal_target_4_line()
        for hero_name in hero_names:
            reward = reward_map[hero_name]
            state_info.add_rewards(hero_name, reward)

    # 计算对线情况下每次行动的效果反馈
    # 因为有些效果会产生持续的反馈（比如多次伤害，持续伤害，buff状态等），我们评估5s内所有的效果的一个加权值
    # 其中每一帧的效果评估方式为：我方获得金币数量x(我方血量变化比率+我方附近塔血量变化比率) A 和 对方获得金币x(对方血量变化比率+对方附近塔血量变化比率) B 的比例关系
    # A/(A + B)
    # 同时反馈两个值，teama（上路）的反馈值和teamb的反馈值
    @staticmethod
    def cal_target_4_line(state_infos, state_idx, hero_names):
        prev_state = state_infos[state_idx]

        reward_range = []
        for i in range(1, 11):
            reward_map = {}
            cur_state = state_infos[state_idx + i]

            # 将传入的英雄分为两个阵容，计算两个阵营之间的奖励比率
            gain_team_a = 0
            gain_team_b = 0
            hero_reward_map = {}
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

                hero_reward_map[hero_name] = gain

            for hero_name in hero_names:
                reward_hero = hero_reward_map[hero_name] / float(gain_team_a + gain_team_b)
                reward_map[hero_name] = reward_hero

            reward_range.append(reward_map)

        # 根据衰减系数来得到总的奖励值
        final_reward_map = {}
        for hero_name in hero_names:
            fianl_reward_hero = 0
            for reward_map in reversed(reward_range):
                fianl_reward_hero = fianl_reward_hero * linemodel.REWARD_GAMMA + reward_map[hero_name]
            final_reward_map[reward_hero] = fianl_reward_hero

        return final_reward_map

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

