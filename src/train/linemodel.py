# -*- coding: utf8 -*-
import collections
import random

import numpy as np
from keras.engine import Input, Model
from keras.layers import Dense, LSTM, Reshape
from keras.layers import Dropout
from keras.optimizers import Nadam
import math

#from model.action import Action
#from train.actioncommandenum import ActionCommandEnum
from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
from train.line_input import Line_input
from util.stateutil import StateUtil
from model.fwdstateinfo import FwdStateInfo


class LineModel:
    REWARD_GAMMA = 0.9


    def __init__(self, statesize, actionsize):
        self.state_size = statesize
        self.action_size = actionsize #50=8*mov+10*attack+10*skill1+10*skill2+10*skill3+回城+hold
        self.memory = collections.deque()
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.model = self._build_model

        #todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist=2
        #todo:以下仅为英雄1技能距离，后续需将这些信息加入到skillinfo中
        self.skilldist=[8,6,5]
        #todo:一下仅为英雄1的技能对自己可用情况，后续应该整合到skillinfo
        self.skill_tag=[0,0,1]


    @property
    def _build_model(self):


        #battle_map=Input(shape=())
        #TODO:模型可能需要的地图信息，暂时忽略了
        battle_information=Input(shape=(240,))
        # 输入的英雄，建筑和小兵的各类属性信息
        dense_1=Dense(512,activation='relu')(battle_information)
        dropped_1=Dropout(0.15)(dense_1)
        dense_2=Dense(256,activation='relu')(dropped_1)
        dropped_2=Dropout(0.15)(dense_2)
        reshaped = Reshape((256, 1))(dropped_2)
        lstm=LSTM(128)(reshaped)
        dense_3 = Dense(64, activation='relu')(lstm)
        dropped_3 = Dropout(0.15)(dense_3)

        predictions = Dense(self.action_size, activation='softmax')(dropped_3)
        model = Model(inputs=battle_information, outputs=predictions)
        model.compile(loss='mse', optimizer=Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004))
        return model

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

    def remember(self, state_info):
        self.memory.append(state_info)

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        index_range = range(len(self.memory))
        minibatch = random.sample(index_range, batch_size)
        x = np.zeros((batch_size, self.state_size))
        y = np.zeros((batch_size, self.action_size))
        for i in range(batch_size):
            sample_index = minibatch[i]
            state_info = self.memory[sample_index]

            # 这里应该是选择reward更大的一方作为训练对象
            # 默认只有两个英雄
            action_index = 0 if state_info.actions[0].reward > state_info.actions[1].reward else 1
            hero_name = state_info.actions[action_index].hero_name
            rival_hero=state_info.actions[1-action_index].hero_name
            line_input = Line_input(state_info, hero_name,rival_hero)
            state = line_input.gen_input()

            # 得到模型预测结果
            target = self.model.predict(state)

            # 修改其中我们选择的行为
            # TODO 是否应该将超出范围的英雄的结果置成0？
            # TODO 以及超过范e围的情况？
            chosen_action = state_info.actions[action_index]
            target[0][chosen_action.output_index] = chosen_action.reward

            x[i], y[i] = state, target
        self.model.fit(x, y, batch_size=batch_size, nb_epoch=1, verbose=0)
        if self.epsilon > self.e_min:
            self.epsilon *= self.e_decay


    def select_actions(self, acts, stateinformation, hero_name, rival_hero):
        #这样传stateinformation太拖慢运行速度了，后面要改
        #atcs是各种行为对应的q-值向量（模型输出），statementinformation包含了这一帧的所有详细信息
        hero = stateinformation.get_hero(hero_name)
        acts=acts[0]
        acts=list(acts)
        for i in range(len(acts)):
            maxQ = max(acts)

            selected = acts.index(maxQ)
            # print "%s %s" % (str(selected),  ' '.join(str(round(float(act), 4)) for act in acts))
            #每次取当前q-value最高的动作执行，若当前动作不可执行则将其q-value置为0，重新取新的最高
            if random.random()<0.15:
                #随机策略，选择跳过当前最优解
                acts[selected]=0
                print("随机跳了一个操作")
                continue
            if selected < 8:  #move
                if hero.movelock == False:
                    #英雄移动限制
                    acts[selected] = 0
                    print("移动受限，放弃移动"+str(hero.movelock))

                    continue
                fwd = StateUtil.mov(selected)

                #生成action所需的参数：CmdAction(hero_name, action, skillid, tgtid, tgtpos, fwd, itemid, output_index, reward)
                action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None,selected, None)
                return action
            elif selected<18: #对敌英雄，塔，敌小兵1~8使用普攻
                if hero.skills[0].canuse!=True and (hero.skills[0].cd==0 or hero.skills[0].cd==None):
                    #普通攻击也有冷却，冷却时canuse=false，此时其实我们可以给出攻击指令的
                    #所以只有当普通攻击冷却完成（cd=0或None）时，canuse仍为false我们才认为英雄被控，不能攻击
                    #被控制住
                    acts[selected]=0
                    print("普攻受限，放弃普攻")
                    continue
                if selected==8:#敌方塔
                    tower=self.get_tower_temp(stateinformation)
                    dist=StateUtil.cal_distance(hero.pos, tower.pos)
                    if dist>self.att_dist:
                    # if dist>StateUtil.ATTACK_UNIT_RADIUS:
                        # 在攻击范围外
                        acts[selected]=0
                        print("塔太远，放弃普攻")
                        continue
                    tgtid=tower.unit_name
                    action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
                elif selected==9:#敌方英雄
                    tgtid = rival_hero
                    rival_info = stateinformation.get_hero(rival_hero)
                    dist=StateUtil.cal_distance(hero.pos,rival_info.pos)
                    if dist>self.att_dist:
                    # if dist>StateUtil.ATTACK_HERO_RADIUS:
                        acts[selected]=0
                        print("英雄太远，放弃普攻")
                        continue
                    # 对方英雄死亡时候忽略这个目标
                    elif rival_info.hp <= 0:
                        acts[selected] = 0
                        continue
                    print('attack rival hero %s %s' % (rival_hero, str(dist)))
                    action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
                else:#小兵
                    creeps=StateUtil.get_nearby_enemy_units(stateinformation,hero_name)
                    n=selected-10
                    if n>=len(creeps):
                        #没有这么多小兵
                        acts[selected]=0
                        print("没有这么多兵，模型选错了")
                        continue
                    dist=StateUtil.cal_distance(hero.pos,creeps[n].pos)
                    if dist > self.att_dist:
                    # if dist > StateUtil.ATTACK_UNIT_RADIUS:
                        acts[selected]=0
                        print("小兵太远，放弃普攻")
                        continue
                    print('attack unit %s %s' % (creeps[n].unit_name, str(dist)))
                    tgtid=creeps[n].unit_name
                    action=CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
            elif selected<28: #skill1
                if hero.skills[1].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    acts[selected]=0
                    print("技能受限，放弃施法1"+" hero.skills[1].canuse="+str(hero.skills[1].canuse)+" tick="+str(stateinformation.tick))
                    continue
                if hero.skills[1].cost>hero.mp:
                    #mp不足
                    acts[selected]=0
                    print("mp不足，放弃施法1")
                    continue
                if hero.skills[1].cd>0:
                    #技能未冷却
                    acts[selected]=0
                    print("技能cd中，放弃施法1")
                    continue
                skillid=1
                [tgtid, tgtpos]=self.choose_skill_target(selected-18,stateinformation,1,hero_name,hero.pos,rival_hero)
                if tgtid==-1:
                    #目标在施法范围外
                    acts[selected]=0
                    print("目标太远，放弃施法1")
                    continue
                # todo: 异常情况处理：
                if tgtpos==None:
                    fwd=None
                else:
                    fwd = tgtpos.fwd(hero.pos)
                action = CmdAction(hero_name, CmdActionEnum.CAST,str(skillid),tgtid, tgtpos, fwd, None, selected, None)
                return action
            elif selected<38: #skill2
                if hero.skills[2].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    print("技能受限，放弃施法2"+" hero.skills[2].canuse="+str(hero.skills[2].canuse)+" tick="+str(stateinformation.tick))
                    acts[selected]=0
                    continue
                if hero.skills[2].cost>hero.mp:
                    #mp不足
                    ("mp不足，放弃施法2")
                    acts[selected]=0
                    continue
                if hero.skills[2].cd>0:
                    #技能未冷却
                    ("技能cd中，放弃施法2")
                    acts[selected]=0
                    continue
                skillid = 2
                [tgtid,tgtpos] = self.choose_skill_target(selected - 28,stateinformation,2,hero_name,hero.pos,rival_hero)
                if tgtid==-1:
                    #目标在施法范围外
                    ("目标太远，放弃施法2")
                    acts[selected]=0
                    continue
                if tgtpos==None:
                    fwd=None
                else:
                    fwd = tgtpos.fwd(hero.pos)
                action = CmdAction(hero_name, CmdActionEnum.CAST, str(skillid), tgtid, tgtpos, fwd, None, selected, None)
                return action
            elif selected<48: #skill3
                if hero.skills[3].canuse!=True:
                    #被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    print("技能受限，放弃大招"+" hero.skills[3].canuse="+str(hero.skills[3].canuse)+" tick="+str(stateinformation.tick))
                    acts[selected]=0
                    continue
                if hero.skills[3].cost>hero.mp:
                    #mp不足
                    ("mp不足，放弃大招")
                    acts[selected]=0
                    continue
                if hero.skills[3].cd>0:
                    #技能未冷却
                    ("技能cd中，放弃大招")
                    acts[selected]=0
                    continue
                skillid = 3
                [tgtid,tgtpos] = self.choose_skill_target(selected - 38,stateinformation,3,hero_name,hero.pos,rival_hero)
                if tgtid==-1:
                    # 目标在施法范围外
                    ("目标太远，放弃大招")
                    acts[selected]=0
                    continue
                if tgtpos==None:
                    fwd=None
                else:
                    fwd = tgtpos.fwd(hero.pos)
                action = CmdAction(hero_name, CmdActionEnum.CAST, str(skillid), tgtid, tgtpos, fwd, None, selected, None)
                return action
            elif selected==48:#回城
                if hero.skills[6].canuse!=True:
                    print("技能受限，放弃回城")
                    #不能回城
                    acts[selected] = 0
                    continue
                if hero.skills[6].cd > 0:
                    #技能未冷却
                    ("技能cd中，放弃回城")
                    acts[selected] = 0
                    continue
                skillid = 6
                action = CmdAction(hero_name, CmdActionEnum.CAST, str(skillid), hero_name, None, None, None, selected, None)
                return action
            else:#hold
                print("轮到了49号行为-hold")
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                return action
        action=CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
        print(str(i)+"跳出了循环，选择了hold")
        return action

    def choose_skill_target(self, selected, stateinformation, skill, hero_name, pos, rival_hero):
        if selected==0:
            if self.skill_tag[skill-1]==0:
                return [-1,None]
            #tgtid =hero_name
            tgtid=hero_name
            # TODO 这里有点问题，如果是目标是自己的技能，是不是要区分下目的，否则fwd计算会出现问题
            #tgtpos=pos
            tgtpos=None
        elif selected==1:
            rival = stateinformation.get_hero(rival_hero)
            if StateUtil.cal_distance(rival.pos, pos) > self.skilldist[skill - 1]:
                # print "技能攻击不到对方 %s %s %s" % (rival_hero, StateUtil.cal_distance(rival.pos, pos), self.skilldist[skill - 1])
                tgtid = -1
                tgtpos = None
            # 对方英雄死亡时候忽略这个目标
            elif rival.hp <= 0:
                tgtid = -1
                tgtpos = None
            else:
                tgtid = rival_hero
                tgtpos = rival.pos
        else:
            creeps=StateUtil.get_nearby_enemy_units(stateinformation, hero_name)
            n=selected-2
            if n >= len(creeps):
                # 没有这么多小兵
                return [-1, None]
            elif StateUtil.cal_distance(pos,creeps[n].pos)>self.skilldist[skill-1]:
                tgtid=-1
                tgtpos=None
            elif creeps[n].hp <= 0:
                tgtid = -1
                tgtpos = None
            else:
                tgtid=creeps[n].unit_name
                tgtpos=creeps[n].pos
        return [tgtid,tgtpos]

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

    def get_action(self,stateinformation,hero_name, rival_hero):
        # 这样传stateinformation太拖慢运行速度了，后面要改
        line_input = Line_input(stateinformation, hero_name, rival_hero)
        state_input = line_input.gen_input()
        state_input=np.array([state_input])
        actions=self.model.predict(state_input)
        action=self.select_actions(actions,stateinformation,hero_name, rival_hero)
        return action

    # 当一场战斗结束之后，根据当时的状态信息，计算每一帧的奖励情况
    @staticmethod
    def update_rewards(state_infos, start_index, end_index):
        result = []
        for i in range(start_index, end_index):
            state_info = state_infos[start_index]
            hero_names = [state_info.heros[0].hero_name, state_info.heros[1].hero_name]
            reward_map = LineModel.cal_target_4_line()
            #todo: 传入参数
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
                fianl_reward_hero = fianl_reward_hero * LineModel.REWARD_GAMMA + reward_map[hero_name]
            final_reward_map[reward_hero] = fianl_reward_hero

        return final_reward_map

