#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON
import random
#import queue
import sys
import numpy as np
import traceback

import tensorflow as tf
import time
from time import gmtime, strftime

from common import cf as C

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum
from train.line_input_lite import Line_Input_Lite
from train.linemodel import LineModel
from train.linemodel_ppo1 import LineModel_PPO1
from util.equiputil import EquipUtil
from util.linetrainer_policy import LineTrainerPolicy
from util.modelprocess import ModelProcess
from util.modelthread import ModelThread
from util.replayer import Replayer
from util.stateutil import StateUtil
import baselines.common.tf_util as U
from datetime import datetime
from engine.playengine import PlayEngine

class LineTrainerPPO:
    TOWN_HP_THRESHOLD = 0.3
    HP_RESTORE_GAP = 90

    def __init__(self, battle_id, save_dir, model_process, model1_hero, model1_cache,
                 model2_hero=None, model2_cache=None, real_hero=None,
                 policy_ratio=-1, policy_continue_acts=3, revert_model1=False, revert_model2=False):
        self.battle_id = battle_id
        self.retreat_pos = None
        self.hero_strategy = {}
        self.state_cache = []
        self.model1_hero = model1_hero
        self.model2_hero = model2_hero
        self.model1_just_dead = 0
        self.model2_just_dead = 0
        self.model1_total_death = 0
        self.model2_total_death = 0
        self.model1_hp_restore = time.time()
        self.model2_hp_restore = time.time()
        self.real_hero = real_hero

        # policy_ratio 表示使用策略的概率， policy_continue_acts表示连续多少个使用策略
        self.policy_ratio = policy_ratio
        self.policy_continue_acts = policy_continue_acts

        # 标记当前是采用策略连续执行的第几个行为
        self.cur_policy_act_idx_map = {model1_hero: 0, model2_hero: 0}

        # 缓存模型计算时间，用来计算平均耗时
        self.time_cache = []

        # 创建存储文件路径
        self.raw_log_file = open(save_dir + '/raw_' + str(battle_id) + '.log', 'w')
        self.state_file = open(save_dir + '/state_' + str(battle_id) + '.log', 'w')
        self.state_reward_file = open(save_dir + '/state_reward_' + str(battle_id) + '.log', 'w')

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        self.model_process = model_process

        # 如果需要的话，可以使用model1的模型来计算model2的英雄，或者反之
        self.revert_model1 = revert_model1
        self.revert_model2 = revert_model2

        self.model1_cache = model1_cache
        self.model2_cache = model2_cache

    def if_restart(self, state_infos, state_index):
        # 重开条件：英雄死亡两次或者第一个塔被打掉
        state_info = state_infos[state_index]
        next_state = state_infos[state_index + 1]
        new = 0
        loss_team = -1
        for hero_name in [self.model1_hero, self.model2_hero]:
            hero_info = state_info.get_hero(hero_name)
            if hero_name == self.model1_hero:
                if_hero_dead = StateUtil.if_hero_dead(state_info, next_state, hero_name)
                self.model1_total_death += if_hero_dead
                total_death = self.model1_total_death
                if if_hero_dead == 1:
                    self.model1_just_dead = 1
            else:
                if_hero_dead = StateUtil.if_hero_dead(state_info, next_state, hero_name)
                self.model2_total_death += if_hero_dead
                total_death = self.model2_total_death
                if if_hero_dead == 1:
                    self.model2_just_dead = 1

            tower_destroyed_cur = StateUtil.if_first_tower_destroyed_in_middle_line(state_info)
            tower_destroyed_next = StateUtil.if_first_tower_destroyed_in_middle_line(next_state)
            if total_death >= 2 or (tower_destroyed_cur is None and tower_destroyed_next is not None):
                # 这里是唯一的结束当前局，重开的点
                print('battle_id', state_info.tick, '重开游戏')
                new = 1
                loss_team = hero_info.team if total_death >= 2 else tower_destroyed_next
                self.model1_total_death = 0
                self.model2_total_death = 0
                return new, loss_team
        return new, loss_team

    def remember_replay(self, state_infos, state_index, 
        model_cache, model_process, hero_name, rival_hero,
        new, loss_team, line_idx=1):

        #TODO 这里有个问题，如果prev不是模型选择的，那实际上这时候不是模型的问题
        # 比如英雄在塔边缘被塔打死了，这时候在执行撤退，其实应该算是模型最后一个动作的锅。
        # 或者需要考虑在复活时候清空
        prev_state = state_infos[state_index-1]
        state_info = state_infos[state_index]
        next_state = state_infos[state_index+1]
        hero_info = state_info.get_hero(hero_name)
        hero_act = state_info.get_hero_action(hero_name)

        if hero_act is not None:
            # prev_new 简单计算，可能会有问题
            prev_new = model_cache.get_prev_new()
            o4r, batchsize = model_cache.output4replay(prev_new, hero_act.vpred)
            model_name = C.NAME_MODEL_1 if hero_name == self.model1_hero else C.NAME_MODEL_2
            if o4r is not None:
                # 批量计算的情况下等待结果。但是不清空训练完成信号，防止还有训练器没有收到这个信号。
                # 等到下次训练开始再清空
                # 一直等待，这里需要观察客户端连接超时开始重试后的情况
                # TODO 这里清空缓存是不是不太好
                #model_process.train_queue.put((self.battle_id, model_name, o4r, batchsize))
                model_process.train(self.battle_id, model_name, o4r, batchsize)
                model_cache.clear_cache()
                print('line_trainer', self.battle_id, '添加训练集')

            ob = LineModel_PPO1.gen_input(state_info, hero_name, rival_hero)
            ac = hero_act.output_index
            vpred = hero_act.vpred

            #TODO 这里为什么没有英雄2的reward打印出来，需要debug
            if new == 1:
                # TODO 这个值应该设置成多少
                rew = 10 if loss_team != hero_info.team else -10
            else:
                rew = LineModel_PPO1.cal_target_ppo_2(prev_state, state_info, next_state, hero_name, rival_hero, line_idx)

            state_info.add_rewards(hero_name, rew)
            model_cache.remember(ob, ac, vpred, new, rew, prev_new)

        # 特殊情况为这一帧没有模型决策，但是触发了重开条件，这种情况下我们也开始训练（在新策略下，只有重开才会开始训练）
        # 如果上一个行为会触发游戏结束，那也会启动这里的训练
        if new == 1:
            if model_cache.isempty():
                prev_new = model_cache.get_prev_new()
                print(self.battle_id, '进入第二个训练条件，但是cache为空', prev_new)
                return

            # 即使在当前帧模型没有决策的情况下，也可能触发结束条件和启动训练
            print(self.battle_id, '启动第二个训练条件')
            rew = 10 if loss_team != hero_info.team else -10
            model_cache.change_last(new, rew)
            prev_new = model_cache.get_prev_new()
            o4r, batch_size = model_cache.output4replay(prev_new, -1)
            model_name = C.NAME_MODEL_1 if hero_name == self.model1_hero else C.NAME_MODEL_2
            if o4r is not None:
                model_process.train(self.battle_id, model_name, o4r, batch_size)
                model_cache.clear_cache()
                print('line_trainer', self.battle_id, '添加训练集')

    def train_line_model(self, raw_state_str):
        self.save_raw_log(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)

        # 重开时候会有以下报文  {"wldstatic":{"ID":9051},"wldruntime":{"State":0}}
        if raw_state_info.tick == -1:
            return {"ID": raw_state_info.battleid, "tick": -1}

        if raw_state_info.tick >= 193512:
            debug_i = 1

        # 根据之前帧更新当前帧信息，变成完整的信息
        # 发现偶然的情况下，其实的tick会是66，然后第二条tick是528
        if raw_state_info.tick <= StateUtil.TICK_PER_STATE and (prev_state_info is None or prev_state_info.tick > raw_state_info.tick):
            print("clear")
            prev_state_info = None
            self.state_cache = []
            self.hero_strategy = {}
            self.model1_just_dead = 0
            self.model2_just_dead = 0
        elif prev_state_info is not None and prev_state_info.tick >= raw_state_info.tick:
            print("clear %s %s" % (prev_state_info.tick, raw_state_info.tick))
            self.state_cache = []
        elif prev_state_info is None and raw_state_info.tick > StateUtil.TICK_PER_STATE:
            # 不是开始帧的话直接返回重启游戏
            # 还有偶然情况下首帧没有tick（即-1）的情况，这种情况下只能重启本场战斗
            print(self.battle_id, '不是开始帧的话直接返回重启游戏', raw_state_info.tick)
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]
            rsp_obj = {"ID": raw_state_info.battleid, "tick": raw_state_info.tick, "cmd": action_strs}
            rsp_str = JSON.dumps(rsp_obj)
            return rsp_str
        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)

        # Test
        hero = state_info.get_hero(self.model1_hero)
        if hero is None or hero.hp is None:
            print(self.battle_id, self.model1_hero, state_info.tick, '读取信息为空，异常')
            print(self.battle_id, '不是开始帧的话直接返回重启游戏', raw_state_info.tick)
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]
            rsp_obj = {"ID": raw_state_info.battleid, "tick": raw_state_info.tick, "cmd": action_strs}
            rsp_str = JSON.dumps(rsp_obj)
            return rsp_str

        # 持久化
        self.state_cache.append(state_info)
        # self.save_state_log(state_info)

        # 首先得到模型的选择，同时会将选择action记录到当前帧中
        action_strs = []
        restart = False
        if self.model1_hero is not None and self.real_hero != self.model1_hero:
            actions_model1, restart = self.build_response(self.state_cache, -1, self.model1_hero)
            action_strs.extend(actions_model1)
        if self.model2_hero is not None and not restart and self.real_hero != self.model2_hero:
            actions_model2, restart = self.build_response(self.state_cache, -1, self.model2_hero)
            action_strs.extend(actions_model2)

        # 计算奖励值，如果有真实玩家，因为需要推测行为的原因，则多往前回朔几帧
        reward_state_idx = -2 if self.real_hero is None else -4
        new = 0
        if len(self.state_cache) + reward_state_idx > 0:
            new, loss_team = self.if_restart(self.state_cache, reward_state_idx)
            if self.model1_hero is not None:
                self.remember_replay(
                    self.state_cache, reward_state_idx,
                    self.model1_cache, self.model_process,
                    self.model1_hero, self.model2_hero,
                    new, loss_team)
            if self.model2_hero is not None:
                self.remember_replay(
                    self.state_cache, reward_state_idx,
                    self.model2_cache, self.model_process,
                    self.model2_hero, self.model1_hero,
                    new, loss_team)

        # 这里为了尽量减少重启次数，在训练结束之后，我们只是清空上个模型的行为串
        if restart:
            self.model1_cache.clear_cache()
            self.model2_cache.clear_cache()
            # 当前帧返回空的行为串
            action_strs = {}

        # 如果达到了重开条件，重新开始游戏
        # 当线上第一个塔被摧毁时候重开
        if new == 1:
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]

        # playengine
        play_heros = []
        playinfo1 = None
        playinfo2 = None
        play_actions = []
        for hero_name in [self.model1_hero, self.model2_hero]:
            action_hero = state_info.get_hero_action(hero_name)
            if action_hero is not None:
                play_heros.append(hero_name)
                play_actions.append(action_hero)
        if len(play_actions) > 0:
            playinfo1, playinfo2 = PlayEngine.play_step(self.state_cache, state_info, play_heros, play_actions)

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str, playinfo1, playinfo2

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

    # 双方英雄集中到中路中间区域，进行对线
    # 一方英雄回城之后，负责等他满血后回到对战区
    def build_response(self, state_cache, state_index, hero_name):
        action_strs=[]
        restart = False

        # 对于模型，分析当前帧的行为
        if self.real_hero != hero_name:
            state_info = state_cache[state_index]
            prev_hero = state_cache[state_index-1].get_hero(hero_name) if len(state_cache) >= 2 is not None else None
        # 如果有真实玩家，我们需要一些历史数据，所以分析3帧前的行为
        elif len(state_cache) > 3:
            state_info = state_cache[state_index-3]
            next1_state_info = state_cache[state_index-2]
            next2_state_info = state_cache[state_index-1]
            next3_state_info = state_cache[state_index]
        else:
            return action_strs, False

        # 决定是否购买道具
        buy_action = EquipUtil.buy_equip(state_info, hero_name)
        if buy_action is not None:
            buy_str = StateUtil.build_command(buy_action)
            action_strs.append(buy_str)

        # 如果有可以升级的技能，优先升级技能3
        hero = state_info.get_hero(hero_name)
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            skillid = 3 if 3 in skills else skills[0]
            update_cmd = CmdAction(hero.hero_name, CmdActionEnum.UPDATE, skillid, None, None, None, None, None, None)
            if skillid == 1:
                hero.skill1_level += 1
            elif skillid == 2:
                hero.skill2_level += 1
            else:
                hero.skill3_level += 1
            hero.level += 1
            update_str = StateUtil.build_command(update_cmd)
            action_strs.append(update_str)

        # 回城相关逻辑
        # 如果在回城中且没有被打断则继续回城，什么也不用返回
        if prev_hero is not None:
            if hero.hero_name in self.hero_strategy and self.hero_strategy[hero.hero_name] == ActionEnum.town_ing \
                    and prev_hero.hp <= hero.hp \
                    and not StateUtil.if_hero_at_basement(hero):
                if not hero.skills[6].canuse:
                    print(self.battle_id, hero.hero_name, '回城中，继续回城')
                    return action_strs, False
                else:
                    print(self.battle_id, hero.hero_name, '回城失败')
                    town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None,
                                            None, None)
                    action_str = StateUtil.build_command(town_action)
                    action_strs.append(action_str)
                    return action_strs, False
                if hero.hp <= 0:
                    self.hero_strategy[hero.hero_name] = None
                    return action_strs, False

        # # 补血逻辑
        # if prev_hero is not None and hero.hero_name in self.hero_strategy and self.hero_strategy[
        #     hero.hero_name] == ActionEnum.hp_restore:
        #     if StateUtil.cal_distance2(prev_hero.pos, hero.pos) < 100:
        #         print(self.battle_id, hero_name, '到达补血点', '血量增长', hero.hp - prev_hero.hp)
        #         del self.hero_strategy[hero_name]
        #         if hero == self.model1_hero:
        #             self.model1_hp_restore = time.time()
        #         else:
        #             self.model2_hp_restore = time.time()

        # 撤退逻辑
        # TODO 甚至可以使用移动技能移动
        if prev_hero is not None and hero.hero_name in self.hero_strategy and self.hero_strategy[hero.hero_name] == ActionEnum.retreat_to_town:
            if StateUtil.cal_distance2(prev_hero.pos, hero.pos) < 100:
                print(self.battle_id, hero_name, '开始回城')
                self.hero_strategy[hero.hero_name] = ActionEnum.town_ing
                town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None,
                                        None, None)
                action_str = StateUtil.build_command(town_action)
                action_strs.append(action_str)
            else:
                print(self.battle_id, hero_name, '还在撤退中', StateUtil.cal_distance2(prev_hero.pos, hero.pos))
            return action_strs, False

        # 如果击杀了对方英雄，扫清附近小兵之后则启动撤退回城逻辑
        if prev_hero is not None:
            if hero.hero_name in self.hero_strategy and self.hero_strategy[hero.hero_name] == ActionEnum.town_ing and prev_hero.hp <= hero.hp \
                    and not StateUtil.if_hero_at_basement(hero):
                if not hero.skills[6].canuse:
                    return action_strs, False
                else:
                    town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None,
                                            None, None)
                    action_str = StateUtil.build_command(town_action)
                    action_strs.append(action_str)
        if hero.hp <= 0:
            self.hero_strategy[hero.hero_name] = None
            return action_strs, False

        # 检查周围状况
        near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(state_info, hero.hero_name,
                                                                StateUtil.LINE_MODEL_RADIUS + 3)
        nearest_friend_units = StateUtil.get_nearby_friend_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        line_index = 1
        near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
        nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)

        # 如果击杀对面英雄就回城补血。整体逻辑为，周围没有兵的情况下启动撤退逻辑，到达撤退地点之后启动回城。补满血之后再跟兵出来
        # 处在泉水之中的时候设置策略层为吃线
        if len(near_enemy_units_in_line) == 0 and len(near_enemy_heroes) == 0:
            if (hero_name == self.model1_hero and self.model2_just_dead == 1 and not StateUtil.if_hero_at_basement(hero)) \
                    or (hero_name == self.model2_hero and self.model1_just_dead == 1 and not StateUtil.if_hero_at_basement(hero)):
                if hero.hp / float(hero.maxhp) > 0.8:
                    if hero_name == self.model1_hero:
                        self.model2_just_dead = 0
                    else:
                        self.model1_just_dead = 0
                else:
                    print(self.battle_id, hero_name, '选择撤退')
                    self.hero_strategy[hero_name] = ActionEnum.retreat_to_town
                    retreat_pos = StateUtil.get_retreat_pos(state_info, hero, line_index=1)
                    action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, retreat_pos, None, None, -1, None)
                    action_str = StateUtil.build_command(action)
                    action_strs.append(action_str)
                    if hero_name == self.model1_hero:
                        self.model2_just_dead = 0
                    else:
                        self.model1_just_dead = 0
                    return action_strs, False

            if StateUtil.if_hero_at_basement(hero):
                if hero_name == self.model1_hero:
                    self.model2_just_dead = 0
                else:
                    self.model1_just_dead = 0
                if hero.hp < hero.maxhp:
                    if hero_name in self.hero_strategy:
                        del self.hero_strategy[hero_name]
                    return action_strs, False

            # # 残血并且周围没有敌人的情况下，可以去塔后吃加血
            # if hero.hp / float(hero.maxhp) < 0.9 and hero not in self.hero_strategy:
            #     print('补血条件', self.battle_id, hero_name, time.time(), self.model1_hp_restore, self.model2_hp_restore)
            #     if hero == self.model1_hero and time.time() - self.model1_hp_restore > LineTrainerPPO.HP_RESTORE_GAP:
            #         print(self.battle_id, hero_name, '选择加血')
            #         self.hero_strategy[hero_name] = ActionEnum.hp_restore
            #     elif hero == self.model2_hero and time.time() - self.model2_hp_restore > LineTrainerPPO.HP_RESTORE_GAP:
            #         print(self.battle_id, hero_name, '选择加血')
            #         self.hero_strategy[hero_name] = ActionEnum.hp_restore
            #
            #     if self.hero_strategy[hero_name] == ActionEnum.hp_restore:
            #         restore_pos = StateUtil.get_hp_restore_place(state_info, hero)
            #         action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, restore_pos, None, None, -1, None)
            #         action_str = StateUtil.build_command(action)
            #         action_strs.append(action_str)
            #         return action_strs, False

        # 开始根据策略决定当前的行动
        # 对线情况下，首先拿到兵线，朝最前方的兵线移动
        # 如果周围有危险（敌方单位）则启动对线模型
        # 如果周围有小兵或者塔，需要他们都是在指定线上的小兵或者塔
        if (len(near_enemy_units_in_line) == 0 and len(nearest_enemy_tower_in_line) == 0 and (
                len(near_enemy_heroes) == 0 or
                StateUtil.if_in_line(hero, line_index, 4000) == -1)
            ) or\
            (len(nearest_friend_units) == 0 and len(near_enemy_units_in_line) == 0 and
            len(near_enemy_heroes) == 0 and len(nearest_enemy_tower_in_line) == 1):

            # 跟兵线或者跟塔，优先跟塔
            self.hero_strategy[hero.hero_name] = ActionEnum.line_1
            # print("策略层：因为附近没有指定兵线的敌人所以开始吃线 " + hero.hero_name)
            front_soldier = StateUtil.get_frontest_soldier_in_line(state_info, line_index, hero.team)
            first_tower = StateUtil.get_first_tower(state_info, hero)

            if front_soldier is None or (hero.team == 0 and first_tower.pos.x > front_soldier.pos.x) or (hero.team == 1 and first_tower.pos.x < front_soldier.pos.x):
                # 跟塔，如果塔在前面的话
                follow_tower_pos = StateUtil.get_tower_behind(first_tower, hero, line_index=1)
                move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, follow_tower_pos, None, None,
                                        None, None)
                action_str = StateUtil.build_command(move_action)
                action_strs.append(action_str)
            else:
                # 得到最前方的兵线位置
                move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, front_soldier.pos, None, None,
                                        None, None)
                action_str = StateUtil.build_command(move_action)
                action_strs.append(action_str)
        else:
            if self.real_hero != hero_name:
                # 使用模型进行决策
                # print("使用对线模型决定英雄%s的行动" % hero.hero_name)
                self.hero_strategy[hero.hero_name] = ActionEnum.line_model

                # 目前对线只涉及到两名英雄
                rival_hero = '28' if hero.hero_name == '27' else '27'
                action, explorer_ratio, action_ratios = self.get_action(state_info, hero_name, rival_hero)

                # 考虑使用固定策略
                # 如果决定使用策略，会连续n条行为全都采用策略（比如确保对方残血时候连续攻击的情况）
                # 如果策略返回为空则表示策略中断
                if action_ratios is not None and self.policy_ratio > 0 and (
                        0 < self.cur_policy_act_idx_map[hero_name] < self.policy_continue_acts
                        or random.uniform(0, 1) <= self.policy_ratio
                ):
                    policy_action = LineTrainerPolicy.choose_action(state_info, action_ratios, hero_name, rival_hero,
                                            near_enemy_units, nearest_friend_units)
                    if policy_action is not None:
                        policy_action.vpred = action.vpred
                        action = policy_action
                        self.cur_policy_act_idx_map[hero_name] += 1
                        print("英雄 " + hero_name + " 使用策略，策略行为计数 idx " + str(self.cur_policy_act_idx_map[hero_name]))
                        if self.cur_policy_act_idx_map[hero_name] >= self.policy_continue_acts:
                            self.cur_policy_act_idx_map[hero_name] = 0
                    else:
                        # 策略中断，清零
                        if self.cur_policy_act_idx_map[hero_name] > 0:
                            print("英雄 " + hero_name + " 策略中断，清零")
                            self.cur_policy_act_idx_map[hero_name] = 0

                action_str = StateUtil.build_command(action)
                action_strs.append(action_str)

                # 如果是要求英雄施法回城，更新英雄状态，这里涉及到后续多帧是否等待回城结束
                if action.action == CmdActionEnum.CAST and int(action.skillid) == 6:
                    print("英雄%s释放了回城" % hero_name)
                    self.hero_strategy[hero.hero_name] = ActionEnum.town_ing

                # 如果是选择了撤退，进行特殊标记，会影响到后续的行为
                if action.action == CmdActionEnum.RETREAT:
                    print("英雄%s释放了撤退，撤退点为%s" % (hero_name, action.tgtpos.to_string()))
                    self.hero_strategy[hero.hero_name] = ActionEnum.retreat
                    self.retreat_pos = action.tgtpos

                # 如果批量训练结束了，这时候需要清空未使用的训练集，然后重启游戏
                if action.action == CmdActionEnum.RESTART:
                    restart = True
                else:
                    # 保存action信息到状态帧中
                    state_info.add_action(action)
            else:
                # 还是需要模型来计算出一个vpred
                rival_hero = '28' if hero.hero_name == '27' else '27'
                action, explorer_ratio, action_ratios = self.get_action(state_info, hero_name, rival_hero)

                # 推测玩家的行为
                guess_action = Replayer.guess_player_action(state_info, next1_state_info, next2_state_info,
                                                            next3_state_info, hero_name, rival_hero)
                guess_action.vpred = action.vpred
                action_str = StateUtil.build_command(guess_action)
                action_str['tick'] = state_info.tick
                print('猜测玩家行为为：' + JSON.dumps(action_str))

                # 保存action信息到状态帧中
                state_info.add_action(guess_action)

        return action_strs, restart
        # rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        # rsp_str = JSON.dumps(rsp_obj)
        # return rsp_str

    # 为批量计算准备的，同时计算一批状态的英雄行为
    # 注意，对方的行为使用自己的模型翻转计算。所以需要对线的英雄完全相同。后续我们有足够多英雄的模型之后可以使用对应模型猜测英雄行为
    # 这里同样需要注意的是，需要使用一个新的queue，和单个英雄的queue区分开
    def get_actions(self, state_infos, hero_name, rival_hero):
        model_name = ModelProcess.NAME_MODEL_1 if hero_name == self.model1_hero else ModelProcess.NAME_MODEL_2

        # 对每个状态，都分别计算英雄和反转后的结果，第二个用来预测对方英雄的行动
        line_inputs = []
        for state_info in state_infos:
            # 为己方英雄进行计算
            line_input = Line_Input_Lite(state_info, hero_name, rival_hero)
            state_input = line_input.gen_line_input(revert=False)
            state_input = np.array(state_input)
            line_inputs.append(state_input)

            # 使用自己的模型预测敌方英雄行为
            line_input = Line_Input_Lite(state_info, rival_hero, hero_name)
            state_input = line_input.gen_line_input(revert=True)
            state_input = np.array(state_input)
            line_inputs.append(state_input)

        actions_list, explorer_ratio, vpreds = self.model_process.act(
                self.battle_id, model_name, line_inputs)
        print('line_trainer', self.battle_id, '返回结果', delta_millionseconds)

        # 特殊情况为模型通知我们它已经训练完成
        if isinstance(actions_list, CmdAction):
            return actions_list, vpreds
        else:
            # 返回标注过不可用的
            masked_actions_list = []
            for i in range(len(actions_list)/2):
                actions = actions_list[i*2]
                action_ratios = list(actions)
                masked_actions = LineModel.remove_unaval_actions(action_ratios, state_info, hero_name, rival_hero)
                masked_actions_list.append(masked_actions)

                actions = actions_list[i*2+1]
                action_ratios = list(actions)
                masked_rival_actions = LineModel.remove_unaval_actions(action_ratios, state_info, rival_hero, hero_name)
                masked_actions_list.append(masked_rival_actions)
            return masked_actions_list, vpreds

    def get_action(self, state_info, hero_name, rival_hero):
        # 选择使用哪个模型，如果是反转的话，使用对方的模型
        if (hero_name == self.model1_hero and not self.revert_model1) or \
            (hero_name == self.model2_hero and self.revert_model2):
            model_name = C.NAME_MODEL_1
        else:
            model_name = C.NAME_MODEL_2

        if hero_name == self.model1_hero:
            revert = self.revert_model1
        else:
            revert = self.revert_model2

        # 获得并传入输入信息
        line_input = Line_Input_Lite(state_info, hero_name, rival_hero)
        state_input = line_input.gen_line_input(revert)
        state_input = np.array(state_input)

        actions, explorer_ratio, vpred = self.model_process.act(self.battle_id, model_name, [state_input])
        actions = actions[0]
        vpred = vpred[0]
        action = LineModel.select_actions(actions, state_info, hero_name, rival_hero, revert)
        action.vpred = vpred

        # 需要返回一个已经标注了不可用行为的（逻辑有点冗余）
        action_ratios = list(actions)
        action_ratios_masked = LineModel.remove_unaval_actions(
            action_ratios, state_info, hero_name, rival_hero)
        return action, explorer_ratio, action_ratios_masked
