#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON
import os
from time import gmtime, strftime
from datetime import datetime

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum
from train.linemodel import LineModel
from util.replayer import Replayer
from util.stateutil import StateUtil
# import sys
#
# import imp
# imp.reload(sys)
# #python 3 version
# #reload(sys)
# sys.setdefaultencoding('utf8')


class LineTrainer:
    TOWN_HP_THRESHOLD = 0.3

    def __init__(self, model1_heros, model2_heros=None, real_heros=None, model1_path=None, model2_path=None):
        self.hero_strategy = {}
        self.state_cache = []
        self.model1_heros = model1_heros
        self.model2_heros = model2_heros
        self.real_heros = real_heros

        self.all_heros = []
        self.all_heros.extend(model1_heros)
        if model2_heros is not None:
            self.all_heros.extend(model2_heros)
        if real_heros is not None:
            self.all_heros.extend(real_heros)

        # 创建存储文件路径
        save_dir = '/Users/sky4star/Github/zy2go/battle_logs/model_' + str(datetime.now()).replace(' ', '').replace(':', '')
        os.makedirs(save_dir)
        self.raw_log_file = open(save_dir + '/raw.log', 'w')
        self.state_file = open(save_dir + '/state.log', 'w')
        self.state_reward_file = open(save_dir + '/state_reward.log', 'w')

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        heros = list(model1_heros)
        if real_heros is not None:
            heros.extend(real_heros)
        self.model1 = LineModel(240, 50, heros)
        if model1_path is not None:
            self.model1.load(model1_path)
        self.model1_save_header = save_dir + '/line_model_1_v'
        self.model1.save(self.model1_save_header + '0')

        if model2_heros is not None:
            heros = list(model2_heros)
            if real_heros is not None:
                heros.extend(real_heros)
            self.model2 = LineModel(240, 50, heros)
            if model2_path is not None:
                self.model2.load(model2_path)
            self.model2_save_header = save_dir + '/line_model_2_v'
            self.model2.save(self.model2_save_header + '0')
        else:
            self.model2 = None

    # 负责整个对线模型的训练
    # 包括：模型选择动作，猜测玩家行为（如果有玩家），得到行为奖励值，训练行为，保存结果
    def train_line_model(self, raw_state_str):
        self.save_raw_log(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)

        if raw_state_info.tick >= 127512:
            debug_i = 1

        # 根据之前帧更新当前帧信息，变成完整的信息
        if raw_state_info.tick <= StateUtil.TICK_PER_STATE:
            print("clear")
            self.state_cache = []
        elif prev_state_info is not None and prev_state_info.tick >= raw_state_info.tick:
            print ("clear %s %s" % (prev_state_info.tick, raw_state_info.tick))
            self.state_cache = []
        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)

        # 首先得到模型的选择，同时会将选择action记录到当前帧中
        action_strs = self.build_response(state_info, prev_state_info, self.model1, self.model1_heros)
        if self.model2_heros is not None:
            actions_model2 = self.build_response(state_info, prev_state_info, self.model2, self.model2_heros)
            action_strs.extend(actions_model2)

        # 缓存
        self.state_cache.append(state_info)
        self.save_state_log(state_info)

        # 更新玩家行为以及奖励值，有一段时间延迟
        reward_state_idx = len(self.state_cache) - LineModel.REWARD_DELAY_STATE_NUM
        print ('reward_state_idx: ' + str(reward_state_idx))
        if reward_state_idx == 299:
            bd = 1
        state_with_reward = self.update_state(self.all_heros, reward_state_idx, self.real_heros)
        if state_with_reward is not None:
            self.save_reward_log(state_with_reward)
            self.model1.remember(state_with_reward)

            # 学习
            if self.model1.if_replay(50):
                print ('开始模型训练')
                self.model1.replay(50)
                self.model1.save(self.model1_save_header + str(self.model1.get_memory_size()))
                print ('结束模型训练')

            if self.model2 is not None:
                # TODO 过滤之后放入相应的模型
                self.model2.remember(state_with_reward)

                # 学习
                if self.model2.if_replay(50):
                    print ('开始模型训练')
                    self.model2.replay(50)
                    self.model2.save(self.model2_save_header + str(self.model2.get_memory_size()))
                    print ('结束模型训练')

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

    def save_raw_log(self, raw_log_str):
        self.raw_log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + raw_log_str + "\n")
        self.raw_log_file.flush()

    def save_reward_log(self, state_with_reward):
        state_encode = state_with_reward.encode()
        state_json = JSON.dumps(state_encode)
        self.state_reward_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + state_json + "\n")
        self.state_reward_file.flush()

    def save_state_log(self, state_info):
        state_encode = state_info.encode()
        state_json = JSON.dumps(state_encode)
        self.state_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + state_json + "\n")
        self.state_file.flush()

    # 根据缓存帧计算奖励值然后保存当前帧
    # 注意：model_heros应该是所有需要模型学习的英雄，real_heros为其中真人的英雄
    def update_state(self, model_heros, state_index, real_heros=None):
        if state_index > 0:
            prev_state = self.state_cache[state_index - 1]
            cur_state = self.state_cache[state_index]
            next_state = self.state_cache[state_index + 1]

            # 如果有必要的话，更新这一帧中真人玩家的行为信息
            if real_heros is not None:
                for hero_name in real_heros:
                    hero_action = Replayer.guess_player_action(prev_state, cur_state, next_state, hero_name, '28')
                    cur_state.add_action(hero_action)
                    action_str = StateUtil.build_command(hero_action)
                    print('玩家行为分析：' + str(action_str) + ' tick:' + str(cur_state.tick))

            # 更新开头一帧的奖励值
            state_with_reward = LineModel.update_state_rewards(self.state_cache, state_index, model_heros)

            # 将中间结果写入文件
            self.save_reward_log(state_with_reward)
            return state_with_reward
        return None

    # 双方英雄集中到中路中间区域，进行对线
    # 一方英雄回城之后，负责等他满血后回到对战区
    def build_response(self, state_info, prev_state_info, line_model, hero_names=None):

        battle_id = state_info.battleid
        tick = state_info.tick
        action_strs=[]

        if hero_names is None:
            hero_names = [hero.hero_name for hero in state_info.heros]
        for hero_name in hero_names:
            hero = state_info.get_hero(hero_name)

            # 如果有可以升级的技能，直接选择第一个升级
            skills = StateUtil.get_skills_can_upgrade(hero)
            if len(skills) > 0:
                update_str = StateUtil.build_action_command(hero.hero_name, 'UPDATE', {'skillid': str(skills[0])})
                action_strs.append(update_str)

            # 检查周围状况
            near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
            near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
            nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)

            # 回城相关逻辑
            # 如果在回城中且没有被打断则继续回城，什么也不用返回
            if prev_state_info is not None:
                prev_hero = prev_state_info.get_hero(hero.hero_name)
                if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing and prev_hero.hp <= hero.hp \
                        and not StateUtil.if_hero_at_basement(hero):
                    print('回城中，继续回城')
                    continue

            if hero.hp <= 0:
                continue

            # 处在少血状态是，且周围没有地方单位的情况下选择回城
            if len(near_enemy_heroes) == 0 and len(near_enemy_units) == 0 and nearest_enemy_tower is None:
                if hero.hp/float(hero.maxhp) < LineTrainer.TOWN_HP_THRESHOLD:
                    print('策略层：回城')
                    # 检查英雄当前状态，如果在回城但是上一帧中受到了伤害，则将状态设置为正在回城，开始回城
                    if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing:
                        if prev_hero.hp > hero.hp:
                            town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None, None, None)
                            action_str = StateUtil.build_command(town_action)
                            action_strs.append(action_str)
                    # 检查英雄当前状态，如果不在回城，则将状态设置为正在回城，开始回城
                    elif self.hero_strategy[hero.hero_name] != ActionEnum.town_ing:
                        self.hero_strategy[hero.hero_name] = ActionEnum.town_ing
                        town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None, None, None)
                        action_str = StateUtil.build_command(town_action)
                        action_strs.append(action_str)

                    # 无论上面怎么操作，玩家下面的动作应该都是在回城中，所以跳过其它的操作
                    continue

            # 处在泉水之中的时候设置策略层为吃线
            if StateUtil.if_hero_at_basement(hero):
                if hero.hp < hero.maxhp:
                    continue

            # 开始根据策略决定当前的行动
            # 对线情况下，首先拿到兵线，朝最前方的兵线移动
            # 如果周围有危险（敌方单位）则启动对线模型
            # 如果周围有小兵或者塔，需要他们都是在指定线上的小兵或者塔
            line_index = 1
            near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
            nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)
            if len(near_enemy_units_in_line) == 0 and len(nearest_enemy_tower_in_line) == 0 and (len(near_enemy_heroes) == 0 or
                    StateUtil.if_in_line(hero, line_index, 4000) == -1):
                self.hero_strategy[hero.hero_name] = ActionEnum.line_1
                print("策略层：因为附近没有指定兵线的敌人所以开始吃线 " + hero.hero_name)
                # 跟兵线
                front_soldier = StateUtil.get_frontest_soldier_in_line(state_info, line_index, hero.team)
                if front_soldier is None:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'HOLD', {})
                    action_strs.append(action_str)
                else:
                    # 得到最前方的兵线位置
                    move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, front_soldier.pos, None, None, None, None)
                    action_str = StateUtil.build_command(move_action)
                    action_strs.append(action_str)
            else:
                # 使用模型进行决策
                print("使用对线模型决定英雄%s的行动" % hero.hero_name)
                self.hero_strategy[hero.hero_name] = ActionEnum.line_model
                enemies = []
                enemies.extend((hero.hero_name for hero in near_enemy_heroes))
                enemies.extend((unit.unit_name for unit in near_enemy_units))
                if nearest_enemy_tower is not None:
                    enemies.append(nearest_enemy_tower.unit_name)
                # print('对线模型决策，因为周围有敌人 ' + ' ,'.join(enemies))

                # 目前对线只涉及到两名英雄
                rival_hero = '28' if hero.hero_name == '27' else '27'
                action = line_model.get_action(state_info, hero.hero_name, rival_hero)
                action_str = StateUtil.build_command(action)
                action_strs.append(action_str)

                # 如果是要求英雄施法回城，更新英雄状态，这里涉及到后续多帧是否等待回城结束
                if action.action == CmdActionEnum.CAST and action.skillid == 6:
                    print("英雄%s释放了回城" % hero_name)
                    self.hero_strategy[hero.hero_name] = ActionEnum.town_ing

                # 保存action信息到状态帧中
                state_info.add_action(action)
        return action_strs
        # rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        # rsp_str = JSON.dumps(rsp_obj)
        # return rsp_str

