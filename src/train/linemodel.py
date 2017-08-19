# -*- coding: utf8 -*-
import collections
import random
from operator import concat

import numpy as np
from keras.engine import Input, Model
from keras.layers import Dense, LSTM, Reshape, concatenate
from keras.layers import Dropout
from keras.optimizers import Nadam
import math
import random

#from model.action import Action
#from train.actioncommandenum import ActionCommandEnum
from model.cmdaction import CmdAction
from model.skillcfginfo import SkillTargetEnum
from train.cmdactionenum import CmdActionEnum
from train.line_input import Line_input
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from model.fwdstateinfo import FwdStateInfo


class LineModel:
    REWARD_GAMMA = 0.9
    REWARD_DELAY_STATE_NUM = 11

    def __init__(self, statesize, actionsize, heros):
        self.state_size = statesize
        self.action_size = actionsize #50=8*mov+10*attack+10*skill1+10*skill2+10*skill3+回城+hold
        self.memory = collections.deque()
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.model = self._build_model
        self.heros = heros

        #todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist=2


    @property
    def _build_model(self):


        #battle_map=Input(shape=())
        #TODO:模型可能需要的地图信息，暂时忽略了
        battle_information=Input(shape=(240,))
        team_information = Input(shape=(64,))
        # 输入的英雄，建筑和小兵的各类属性信息
        # dense_1=Dense(512,activation='relu')(battle_information)
        # dropped_1=Dropout(0.25)(dense_1)
        # dense_2=Dense(256,activation='relu')(dropped_1)
        # dropped_2=Dropout(0.25)(dense_2)
        # reshaped = Reshape((256, 1))(dropped_2)
        # lstm=LSTM(128)(reshaped)
        # dense_3 = Dense(64, activation='relu')(lstm)
        # dropped_3 = Dropout(0.25)(dense_3)
        #
        # predictions = Dense(self.action_size, activation='softmax')(dropped_3)
        # model = Model(inputs=battle_information, outputs=predictions)


        # v2版本
        # dense_1 = Dense(512, activation='relu')(battle_information)
        # dropped_1 = Dropout(0.15)(dense_1)
        # dense_2 = Dense(256, activation='relu')(dropped_1)
        # dropped_2 = Dropout(0.15)(dense_2)
        # dense_3 = Dense(64, activation='tanh')(dropped_2)
        # dropped_3 = Dropout(0.15)(dense_3)

        # 尝试阵容信息单独传入输入
        # 尝试不同类型的选择用不同的模型来计算
        dense_1 = Dense(512, activation='relu')(battle_information)
        dropped_1 = Dropout(0.15)(dense_1)
        dense_2 = Dense(256, activation='relu')(dropped_1)
        dropped_2 = Dropout(0.15)(dense_2)
        dense_3 = Dense(64, activation='tanh')(dropped_2)

        dense_3_move = concatenate([dense_3, team_information])
        dense_4_move = Dense(8, activation='tanh')(dense_3_move)
        dense_4_attack = Dense(10, activation='tanh')(dense_3)
        dense_4_skill = Dense(30, activation='tanh')(dense_3)
        dense_4_others = Dense(2, activation='tanh')(dense_3)

        predictions = concatenate([dense_4_move,dense_4_attack,dense_4_skill,dense_4_others])

        model = Model(inputs=[battle_information, team_information], outputs=predictions)
        model.compile(loss='mse', optimizer=Nadam(lr=0.002, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004))
        return model

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

    def remember(self, state_info):
        # 必须具有指定英雄的action以及reward，还要是有效reward（不为0）
        actions = [a for a in state_info.actions if a.hero_name in self.heros and a.reward is not None and a.reward != 0]
        if len(actions) > 0:
            self.memory.append(state_info)

    def if_replay(self, learning_batch):
        if len(self.memory) > 0 and len(self.memory) % learning_batch == 0:
            return True
        return False

    def get_memory_size(self):
        return len(self.memory)

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        index_range = range(len(self.memory))
        minibatch = random.sample(index_range, batch_size)
        x_1 = np.zeros((batch_size, self.state_size))
        x_2 = np.zeros((batch_size, 64))
        y = np.zeros((batch_size, self.action_size))
        for i in range(batch_size):
            sample_index = minibatch[i]
            state_info = self.memory[sample_index]

            # 随机从指定玩家的行为中进行挑选
            selected_action = None
            actions = [a for a in state_info.actions if a.hero_name in self.heros and a.reward is not None]
            if len(actions) == 0:
                print('skip replay tick %s ' % state_info.tick)
                continue
            rmd = random.randint(0, len(actions) - 1)
            selected_action = actions[rmd]

            hero_name = selected_action.hero_name
            # TODO rival_hero 怎么定义？
            # 暂时将1v1的rival_hero 定义为对面英雄
            for hero in state_info.heros:
                if hero.hero_name != hero_name:
                    rival_hero = hero.hero_name
                    break

            line_input = Line_input(state_info, hero_name, rival_hero)
            state = line_input.gen_line_input()
            state_input = np.array([state])
            team = line_input.gen_team_input()
            team_input = np.array([team])

            # 得到模型预测结果
            actions = self.model.predict([state_input, team_input])

            # 将不合理的选择都置为0
            actions_list = list(actions[0])
            actions_detail = ' '.join(str("%.4f" % float(act)) for act in actions_list)
            # target = actions_list
            target = self.remove_unaval_actions(actions_list, state_info, hero_name, rival_hero)

            # 测试代码，可以在model相同，没有随机的情况下检查模型挑选的action是否和我们记录的相同
            # target_action = self.select_actions(target, state_info, hero_name, rival_hero)
            maxQ = max(target)
            target_action = target.index(maxQ)
            print ('model select action %s, tick %s' % (str(target_action), state_info.tick))

            # 修改其中我们选择的行为
            # TODO 是否应该将超出范围的英雄的结果置成0？
            chosen_action = state_info.get_hero_action(hero_name)
            target[chosen_action.output_index] = chosen_action.reward
            target_detail = ' '.join(str("%.4f" % float(act)) for act in target)

            print("replay detail: selected: %s \n    action array:%s \n    target array:%s\n\n" %
                   (str(chosen_action.output_index),  actions_detail, target_detail))

            x_1[i], x_2[i], y[i] = state, team, target
        self.model.fit([x_1, x_2], y, batch_size=batch_size, epochs=1, verbose=0)
        if self.epsilon > self.e_min:
            self.epsilon *= self.e_decay

    def remove_unaval_actions(self, acts, stateinformation, hero_name, rival_hero, debug=False):
        for i in range(len(acts)):
            hero = stateinformation.get_hero(hero_name)
            selected = i
            if selected < 8:  # move
                if not hero.movelock:
                    # 英雄移动限制
                    acts[selected] = -1
                    if debug: print("移动受限，放弃移动" + str(hero.movelock))
                    continue
            elif selected < 18:  # 对敌英雄，塔，敌小兵1~8使用普攻
                if hero.skills[0].canuse != True and (hero.skills[0].cd == 0 or hero.skills[0].cd == None):
                    # 普通攻击也有冷却，冷却时canuse=false，此时其实我们可以给出攻击指令的
                    # 所以只有当普通攻击冷却完成（cd=0或None）时，canuse仍为false我们才认为英雄被控，不能攻击
                    # 被控制住
                    acts[selected] = -1
                    if debug: print("普攻受限，放弃普攻")
                    continue
                if selected == 8:  # 敌方塔
                    tower = self.get_tower_temp(stateinformation)
                    dist = StateUtil.cal_distance(hero.pos, tower.pos)
                    # if dist > self.att_dist:
                    if dist>StateUtil.ATTACK_UNIT_RADIUS:
                        # 在攻击范围外
                        acts[selected] = -1
                        if debug: print("塔太远，放弃普攻")
                        continue
                elif selected == 9:  # 敌方英雄
                    tgtid = rival_hero
                    rival_info = stateinformation.get_hero(rival_hero)
                    dist = StateUtil.cal_distance(hero.pos, rival_info.pos)
                    # 英雄不可见
                    if not rival_info.is_enemy_visible():
                        acts[selected] = -1
                        if debug: print("英雄不可见")
                        continue
                    # 英雄太远，放弃普攻
                    # if dist > self.att_dist:
                    if dist>StateUtil.ATTACK_HERO_RADIUS:
                        acts[selected] = -1
                        if debug: print("英雄太远，放弃普攻")
                        continue
                    # 对方英雄死亡时候忽略这个目标
                    elif rival_info.hp <= 0:
                        acts[selected] = -1
                        if debug: print("对方英雄死亡")
                        continue
                else:  # 小兵
                    creeps = StateUtil.get_nearby_enemy_units(stateinformation, hero_name)
                    n = selected - 10
                    # 小兵不可见
                    if n >= len(creeps):
                        # 没有这么多小兵
                        acts[selected] = -1
                        if debug: print("没有这么多兵，模型选错了")
                        continue
                    if not creeps[n].is_enemy_visible():
                        acts[selected] = -1
                        if debug: print("小兵不可见")
                        continue
                    dist = StateUtil.cal_distance(hero.pos, creeps[n].pos)
                    # if dist > self.att_dist:
                    if dist > StateUtil.ATTACK_UNIT_RADIUS:
                        acts[selected] = -1
                        if debug: print("小兵太远，放弃普攻")
                        continue
                    print ("英雄%s可以攻击到小兵%s，英雄位置%s，小兵位置%s，距离%s" % (str(hero_name), str(creeps[n].unit_name),
                                        hero.pos.to_string(), creeps[n].pos.to_string(), str(dist)))
            elif selected < 48:  # skill1
                skillid =int( (selected-18)/10+1)
                if hero.skills[skillid].canuse != True:
                    # 被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    acts[selected] = -1
                    if debug: print("技能受限，放弃施法" + str(skillid) + " hero.skills[x].canuse=" + str(hero.skills[skillid].canuse) + " tick=" + str(
                        stateinformation.tick))
                    continue
                if hero.skills[skillid].cost==None or hero.skills[skillid].cost > hero.mp:
                    # mp不足
                    acts[selected] = -1
                    if debug: print("mp不足，放弃施法" + str(skillid))
                    continue
                if hero.skills[skillid].cd > 0:
                    # 技能未冷却
                    acts[selected] = -1
                    if debug: print("技能cd中，放弃施法" + str(skillid))
                    continue
                [tgtid, tgtpos] = self.choose_skill_target(selected - 18 - (skillid-1)*10, stateinformation, skillid, hero_name, hero.pos,
                                                           rival_hero, debug)
                if tgtid == -1:
                    acts[selected] = -1
                    if debug: print("目标不符合施法要求")
                    continue
            elif selected == 48:  # 回城
                #暂时屏蔽回城
                acts[selected] = -1
                continue
                if hero.skills[6].canuse != True:
                    if debug: print("技能受限，放弃回城")
                    acts[selected] = -1
                    continue
                if hero.skills[6].cd > 0:
                    ("技能cd中，放弃回城")
                    acts[selected] = -1
                    continue
        return acts

    def select_actions(self, acts, stateinformation, hero_name, rival_hero):
        #这样传stateinformation太拖慢运行速度了，后面要改
        #atcs是各种行为对应的q-值向量（模型输出），statementinformation包含了这一帧的所有详细信息
        hero = stateinformation.get_hero(hero_name)
        acts = list(acts[0])
        acts = self.remove_unaval_actions(acts, stateinformation, hero_name, rival_hero)
        for i in range(len(acts)):
            maxQ = max(acts)

            if maxQ <= 0:
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                return action
            selected = acts.index(maxQ)
            print ("line model selected action:%s action array:%s" % (str(selected),  ' '.join(str(round(float(act), 4)) for act in acts)))
            # 每次取当前q-value最高的动作执行，若当前动作不可执行则将其q-value置为0，重新取新的最高
            # 调试阶段暂时关闭随机，方便复现所有的问题
            if random.random()<0.1:
                #随机策略，选择跳过当前最优解
                acts[selected]=0
                print("随机跳了一个操作")
                continue
            if selected < 8:  #move
                fwd = StateUtil.mov(selected)
                action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None,selected, None)
                return action
            elif selected<18: #对敌英雄，塔，敌小兵1~8使用普攻
                if selected==8:#敌方塔
                    tower = self.get_tower_temp(stateinformation)
                    tgtid = tower.unit_name
                    action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
                elif selected==9:#敌方英雄
                    tgtid = rival_hero
                    action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
                else:#小兵
                    creeps=StateUtil.get_nearby_enemy_units(stateinformation,hero_name)
                    n=selected-10
                    tgtid=creeps[n].unit_name
                    action=CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, None, None, None, selected, None)
                    return action
            elif selected<48: #skill
                skillid = int((selected - 18) / 10 + 1)
                [tgtid, tgtpos]=self.choose_skill_target(selected-18-(skillid-1)*10,stateinformation,skillid,hero_name,hero.pos,rival_hero)
                if tgtpos is None:
                    fwd = None
                else:
                    fwd = tgtpos.fwd(hero.pos)
                action = CmdAction(hero_name, CmdActionEnum.CAST,skillid,tgtid, tgtpos, fwd, None, selected, None)
                return action
            elif selected==48:#回城
                skillid = 6
                action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, hero_name, None, None, None, selected, None)
                return action
            else:#hold
                print("轮到了49号行为-hold")
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                return action

    def choose_skill_target(self, selected, stateinformation, skill, hero_name, pos, rival_hero, debug=False):
        hero_info = stateinformation.get_hero(hero_name)
        skill_info = SkillUtil.get_skill_info(hero_info.cfg_id, skill)
        if selected==0:
            # 施法目标为自己
            # 首先判断施法目标是不是只限于敌方英雄
            if skill_info.cast_target == SkillTargetEnum.viral:
                return [-1,None]
            tgtid=hero_name
            # TODO 这里有点问题，如果是目标是自己的技能，是不是要区分下目的，否则fwd计算会出现问题
            tgtpos=None
        elif selected==1:
            # 攻击对方英雄
            # 首先判断施法目标是不是只限于自己
            if skill_info.cast_target == SkillTargetEnum.self:
                return [-1, None]
            rival = stateinformation.get_hero(rival_hero)
            if not rival.is_enemy_visible():
                if debug: print ("敌方英雄不可见")
                tgtid = -1
                tgtpos = None
            elif StateUtil.cal_distance(rival.pos, pos) > skill_info.cast_distance:
                if debug: print ("技能攻击不到对方 %s %s %s" % (rival_hero, StateUtil.cal_distance(rival.pos, pos), skill_info.cast_distance))
                tgtid = -1
                tgtpos = None
            # 对方英雄死亡时候忽略这个目标
            elif rival.hp <= 0:
                if debug: print ("技能攻击不了对方，对方已经死亡")
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
                if debug: print ("技能不能攻击，没有指定的小兵")
                return [-1, None]
            elif not creeps[n].is_enemy_visible():
                if debug: print ("敌方小兵不可见")
                tgtid = -1
                tgtpos = None
            elif StateUtil.cal_distance(pos,creeps[n].pos) > skill_info.cast_distance:
                if debug: print ("技能不能攻击，小兵距离过远")
                tgtid=-1
                tgtpos=None
            elif creeps[n].hp <= 0:
                if debug: print ("技能不能攻击，小兵已经死亡")
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
        state_input = line_input.gen_line_input()

        # input_detail = ' '.join(str("%f" % float(act)) for act in state_input)
        # print(input_detail)

        state_input=np.array([state_input])
        team = line_input.gen_team_input()
        team_input = np.array([team])
        actions=self.model.predict([state_input, team_input])
        # action_detail = ' '.join(str("%.4f" % float(act)) for act in list(actions[0]))

        action=self.select_actions(actions,stateinformation,hero_name, rival_hero)

        # print ("replay detail: selected: %s \n    input array:%s \n    action array:%s\n\n" %
        #        (str(action.output_index), input_detail, action_detail))
        return action

    # 当一场战斗结束之后，根据当时的状态信息，计算每一帧的奖励情况
    @staticmethod
    def update_rewards(state_infos, hero_names=None):
        for i in range(len(state_infos) - LineModel.REWARD_DELAY_STATE_NUM):
            state_infos[i] = LineModel.update_state_rewards(state_infos, i, hero_names)
        return state_infos

    @staticmethod
    def update_state_rewards(state_infos, state_index, hero_names=None):
        state_info = state_infos[state_index]
        cal_heros = hero_names
        if hero_names is None:
            cal_heros = [h.hero_name for h in state_info.heros]
        reward_map = LineModel.cal_target_4_line(state_infos, state_index, cal_heros)
        for hero_name in cal_heros:
            reward = reward_map[hero_name]
            state_info.add_rewards(hero_name, reward)
        return state_info

    # 计算对线情况下每次行动的效果反馈
    # 因为有些效果会产生持续的反馈（比如多次伤害，持续伤害，buff状态等），我们评估5s内所有的效果的一个加权值
    # 其中每一帧的效果评估方式为：我方获得金币数量x(我方血量变化比率+我方附近塔血量变化比率) A 和 对方获得金币x(对方血量变化比率+对方附近塔血量变化比率) B 的比例关系
    # A/(A + B)
    # 同时反馈两个值，teama（上路）的反馈值和teamb的反馈值
    @staticmethod
    def cal_target_4_line(state_infos, state_idx, hero_names):

        # 首先计算每个英雄的获得情况
        prev_state = state_infos[state_idx]
        reward_range = []
        for i in range(1, 11):
            reward_map = {}
            cur_state = state_infos[state_idx + i]

            # 计算每一回合每个英雄的获得情况
            hero_reward_map = {}
            for hero_name in hero_names:
                prev_hero = prev_state.get_hero(hero_name)
                cur_hero = cur_state.get_hero(hero_name)

                # 这里考虑血量变化，如果血量提高则会有奖励（所以回城也会有奖励系数)
                # 逻辑上忽略升级带来的一点点变化
                hp_delta = (int(cur_hero.hp) - int(prev_hero.hp)) / float(cur_hero.maxhp)

                # 得到金币变化，如果是消灭了对方小兵，或者英雄，金币上会有个显著的变化
                # 对于死亡，相应的对方会有个金币的提升，暂时不考虑击杀被击杀的额外惩罚了吧
                # 给死亡英雄一个惩罚值
                #TODO 这里需要考虑装备情况
                gold_delta = int(cur_hero.gold) - int(prev_hero.gold)
                if cur_hero.hp <= 0:
                    gold_delta = 0

                # 放大金币变化情况，否则默认每两帧之间只有2-3的变化
                gain = gold_delta * (1 + hp_delta) * 100
                hero_reward_map[hero_name] = gain
            reward_range.append(hero_reward_map)
            prev_state = cur_state

        # 根据衰减系数来得到总的奖励值
        final_reward_map = {}
        for hero_name in hero_names:
            final_reward_map[hero_name] = 0
        for reward_map in reversed(reward_range):
            for hero_name in hero_names:
                final_reward_map[hero_name] = final_reward_map[hero_name] * LineModel.REWARD_GAMMA + reward_map[hero_name]

        # 对比两个阵营的获得情况（可以针对1v1，1v2以及2v2）
        # TODO,1v2需不需要特殊处理
        gain_team_a = 0.0
        gain_team_b = 0.0
        for hero_name in hero_names:
            cur_hero = cur_state.get_hero(hero_name)
            if cur_hero.team == 0:
                gain_team_a += final_reward_map[hero_name]
            else:
                gain_team_b += final_reward_map[hero_name]
        for hero_name in hero_names:
            cur_hero = cur_state.get_hero(hero_name)
            if cur_hero.team == 0:
                final_reward_map[hero_name] = ((gain_team_a / float(gain_team_a + gain_team_b))-0.5)*2 if (gain_team_a + gain_team_b) > 0 else None
            else:
                final_reward_map[hero_name] = ((gain_team_b / float(gain_team_a + gain_team_b))-0.5)*2 if (gain_team_a + gain_team_b) > 0 else None

        # 特殊情况处理


        # 进入模型选择区域后，下1/2帧立刻离开模型选择区域的，这种情况需要避免
        if state_idx > 0:
            prev_state = state_infos[state_idx - 1]
            cur_state = state_infos[state_idx]
            next_state = state_infos[state_idx + 1]
            next_next_state = state_infos[state_idx + 2]

            # 离线太远就进行惩罚
            for hero_name in hero_names:
                line_index = 1
                prev_hero = prev_state.get_hero(hero_name)
                cur_hero = cur_state.get_hero(hero_name)
                prev_in_line = StateUtil.if_in_line(prev_hero, line_index, 4000)
                cur_in_line = StateUtil.if_in_line(cur_hero, line_index, 4000)
                if prev_in_line >= 0 and cur_in_line == -1:
                    final_reward_map[hero_name] = -1

            # 进入模型选择区域后，下1/2帧立刻离开模型选择区域的，这种情况需要避免
            for hero_name in hero_names:
                prev_hero_action = prev_state.get_hero_action(hero_name)
                cur_hero_action = cur_state.get_hero_action(hero_name)
                next_hero_action = next_state.get_hero_action(hero_name)
                next_next_hero_action = next_next_state.get_hero_action(hero_name)

                # 只有当前帧玩家有行动，且是移动，则我们给予一个差评
                # TODO 如果更严谨我们应该首先判断之前是不是在回城状态中，然后被打断了
                if prev_hero_action is None and cur_hero_action is not None and next_hero_action is None:
                    final_reward_map[hero_name] = -1
                elif prev_hero_action is None and cur_hero_action is not None and next_hero_action is not None and next_next_hero_action is None:
                    final_reward_map[hero_name] = -1

        # 回城被打断或者自己中断回城的情况，将target置为0。这是不希望的情况
        for hero_name in hero_names:
            go_town_break = False
            cur_state = state_infos[state_idx]
            cur_hero = cur_state.get_hero(hero_name)
            cur_hero_action = cur_state.get_hero_action(hero_name)
            if cur_hero_action is not None and cur_hero_action.action == CmdActionEnum.CAST and cur_hero_action.skillid == 6:
                # 开始回城，这时候需要检查后面一系列帧有没有进行其它的操作，以及有没有减血（被打断的情况）
                for i in range(1, 8):
                    next_state = state_infos[state_idx + i]
                    next_hero = next_state.get_hero(hero_name)
                    if next_state is None:
                        next_state = None
                    next_hero_action = next_state.get_hero_action(hero_name)
                    if next_hero_action is None or cur_hero_action.action != CmdActionEnum.CAST or cur_hero_action.skillid == 6:
                        go_town_break = True
                        break
                    elif next_hero.hp < cur_hero.hp:
                        go_town_break = True
                        break
            if go_town_break:
                print ("计算reward，英雄%s回城被打断，将reward置为0" % (hero_name))
                final_reward_map[hero_name] = -1

        return final_reward_map

