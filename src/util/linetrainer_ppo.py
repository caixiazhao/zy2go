#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON
import os
import tensorflow as tf
from time import gmtime, strftime
from datetime import datetime

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum
from train.linemodel import LineModel
from train.linemodel_dpn import LineModel_DQN
from util.replayer import Replayer
from util.stateutil import StateUtil
import baselines.common.tf_util as U
# import sys
#
# import imp
# imp.reload(sys)
# #python 3 version
# #reload(sys)
# sys.setdefaultencoding('utf8')


class LineTrainerPPO:
    TOWN_HP_THRESHOLD = 0.3

    def __init__(self, save_dir, model1_hero, model1, model1_save_header, model1_cache,
                 model2_hero=None, model2=None, model2_save_header=None, model2_cache=None, real_heros=None):
        self.retreat_pos = None
        self.hero_strategy = {}
        self.state_cache = []
        self.model1_hero = model1_hero
        self.model2_hero = model2_hero
        self.real_heros = real_heros

        # 创建存储文件路径
        self.raw_log_file = open(save_dir + '/raw.log', 'w')
        self.state_file = open(save_dir + '/state.log', 'w')
        self.state_reward_file = open(save_dir + '/state_reward.log', 'w')

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        self.model1 = model1
        self.model1_save_header = model1_save_header
        self.model1_cache = model1_cache

        if model2_hero is not None:
            self.model2 = model2
            self.model2_save_header = model2_save_header
            self.model2_cache = model2_cache
        else:
            self.model2 = None

        self.model1_prev_act = 0
        self.model1_act = 0
        self.model2_prev_act = 0
        self.model2_act = 0
        self.save_batch = 20

        tvars = tf.trainable_variables()
        tvars_vals = U.get_session().run(tvars)

        for var, val in zip(tvars, tvars_vals):
            print(var.name, val)

    def remember_replay(self, state_infos, state_index, model_cache, model, hero_name, rival_hero,
                        prev_act, model_save_header, line_idx=1):
        prev_state = state_infos[state_index-1]
        state_info = state_infos[state_index]
        next_state = state_infos[state_index+1]
        hero_act = state_info.get_hero_action(hero_name)
        if hero_act is not None:
            # prev_new 简单计算，可能会有问题
            prev_new = 1 if prev_state.get_hero(hero_name).hp <= 0 else 0
            o4r = model_cache.output4replay(prev_new, hero_act.vpred)
            if o4r is not None:
                model.replay(o4r)

            ob = model.gen_input(state_info, hero_name, rival_hero)
            ac = hero_act.output_index
            vpred = hero_act.vpred
            new = StateUtil.if_hero_dead(state_info, next_state, hero_name)
            rew = model.get_reward(state_infos, state_index, hero_name, rival_hero, line_idx)
            state_info.add_rewards(hero_name, rew)
            model_cache.remember(ob, ac, vpred, new, rew, prev_new, prev_act)

            if o4r is not None:
                replay_time = model.iters_so_far
                if replay_time % self.save_batch == 0:
                   model.save(model_save_header + str(replay_time) + '/model')
            return True
        return False

    def train_line_model(self, raw_state_str):
        self.save_raw_log(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)

        # 重开时候会有以下报文  {"wldstatic":{"ID":9051},"wldruntime":{"State":0}}
        if raw_state_info.tick == -1:
            return ''

        if raw_state_info.tick >= 68508:
            debug_i = 1

        # 根据之前帧更新当前帧信息，变成完整的信息
        if raw_state_info.tick <= StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state_info = None
            self.state_cache = []
        elif prev_state_info is not None and prev_state_info.tick >= raw_state_info.tick:
            print("clear %s %s" % (prev_state_info.tick, raw_state_info.tick))
            self.state_cache = []
        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)

        self.state_cache.append(state_info)

        # 首先得到模型的选择，同时会将选择action记录到当前帧中
        action_strs = self.build_response(state_info, prev_state_info, self.model1, self.model1_hero)
        if self.model2_hero is not None:
            actions_model2 = self.build_response(state_info, prev_state_info, self.model2, self.model2_hero)
            action_strs.extend(actions_model2)

        reward_state_idx = len(self.state_cache) - LineModel.REWARD_DELAY_STATE_NUM
        # print('reward_state_idx: ' + str(reward_state_idx))
        state_with_reward = None
        if reward_state_idx > 1:
            added = self.remember_replay(self.state_cache, reward_state_idx, self.model1_cache, self.model1,
                                         self.model1_hero, self.model2_hero, self.model1_prev_act, self.model1_save_header)
            if self.model2 is not None:
                added = self.remember_replay(self.state_cache, reward_state_idx, self.model2_cache, self.model2,
                                             self.model2_hero, self.model1_hero, self.model2_prev_act,
                                             self.model2_save_header)

        # 如果达到了重开条件，重新开始游戏
        # 当线上第一个塔被摧毁时候重开
        if StateUtil.if_first_tower_destroyed_in_line(state_info, line_idx=1):
            print('重新开始游戏')
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

    def save_models(self):
        self.model1.save(self.model1_save_header + str(self.model1.get_memory_size()))
        if self.model2 is not None:
            self.model2.save(self.model2_save_header + str(self.model2.get_memory_size()))

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
    def build_response(self, state_info, prev_state_info, line_model, hero_name=None):

        battle_id = state_info.battleid
        tick = state_info.tick

        if tick >= 139062:
            db = 1

        action_strs=[]

        hero = state_info.get_hero(hero_name)
        prev_hero = prev_state_info.get_hero(hero.hero_name) if prev_state_info is not None else None

        # 检查是否重启游戏
        # 线上第一个塔被摧毁


        # 如果有可以升级的技能，优先升级技能3
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            skillid = 3 if 3 in skills else skills[0]
            update_cmd = CmdAction(hero.hero_name, CmdActionEnum.UPDATE, skillid, None, None, None, None, None, None)
            update_str = StateUtil.build_command(update_cmd)
            action_strs.append(update_str)

        # 检查周围状况
        near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(state_info, hero.hero_name,
                                                                StateUtil.LINE_MODEL_RADIUS + 3)

        # 回城相关逻辑
        # 如果在回城中且没有被打断则继续回城，什么也不用返回
        if prev_hero is not None:
            if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing and prev_hero.hp <= hero.hp \
                    and not StateUtil.if_hero_at_basement(hero):
                if not hero.skills[6].canuse:
                    print('回城中，继续回城')
                    return action_strs
                else:
                    print('回城失败')

        if hero.hp <= 0:
            self.hero_strategy[hero.hero_name] = None
            return action_strs

        # 处在少血状态是，且周围没有地方单位的情况下选择回城
        # if len(near_enemy_heroes) == 0 and len(near_enemy_units) == 0 and nearest_enemy_tower is None:
        #     if hero.hp/float(hero.maxhp) < LineTrainer.TOWN_HP_THRESHOLD:
        #         print('策略层：回城')
        #         # 检查英雄当前状态，如果在回城但是上一帧中受到了伤害，则将状态设置为正在回城，开始回城
        #         if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing:
        #             if prev_hero.hp > hero.hp:
        #                 town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None, None, None)
        #                 action_str = StateUtil.build_command(town_action)
        #                 action_strs.append(action_str)
        #         # 检查英雄当前状态，如果不在回城，则将状态设置为正在回城，开始回城
        #         elif self.hero_strategy[hero.hero_name] != ActionEnum.town_ing:
        #             self.hero_strategy[hero.hero_name] = ActionEnum.town_ing
        #             town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, hero.hero_name, None, None, None, None, None)
        #             action_str = StateUtil.build_command(town_action)
        #             action_strs.append(action_str)
        #
        #         # 无论上面怎么操作，玩家下面的动作应该都是在回城中，所以跳过其它的操作
        #         continue

        # 处在泉水之中的时候设置策略层为吃线
        if StateUtil.if_hero_at_basement(hero):
            if hero.hp < hero.maxhp:
                return action_strs

        # 撤退逻辑
        # TODO 甚至可以使用移动技能移动
        if hero.hero_name in self.hero_strategy and self.hero_strategy[hero.hero_name] == ActionEnum.retreat:
            dist = StateUtil.cal_distance(hero.pos, self.retreat_pos)
            if dist <= 2:
                print('到达撤退点附近')
                self.hero_strategy[hero.hero_name] = None
            elif prev_hero is not None and prev_hero.pos.to_string() == hero.pos.to_string():
                print('英雄卡住了，取消撤退')
                self.hero_strategy[hero.hero_name] = None
            else:
                print('仍然在撤退 ' + str(dist))
                return action_strs

        # 开始根据策略决定当前的行动
        # 对线情况下，首先拿到兵线，朝最前方的兵线移动
        # 如果周围有危险（敌方单位）则启动对线模型
        # 如果周围有小兵或者塔，需要他们都是在指定线上的小兵或者塔
        line_index = 1
        near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
        nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)
        if len(near_enemy_units_in_line) == 0 and len(nearest_enemy_tower_in_line) == 0 and (
                len(near_enemy_heroes) == 0 or
                StateUtil.if_in_line(hero, line_index, 4000) == -1):
            self.hero_strategy[hero.hero_name] = ActionEnum.line_1
            # print("策略层：因为附近没有指定兵线的敌人所以开始吃线 " + hero.hero_name)
            # 跟兵线
            front_soldier = StateUtil.get_frontest_soldier_in_line(state_info, line_index, hero.team)
            if front_soldier is None:
                action_str = StateUtil.build_action_command(hero.hero_name, 'HOLD', {})
                action_strs.append(action_str)
            else:
                # 得到最前方的兵线位置
                move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, front_soldier.pos, None, None,
                                        None, None)
                action_str = StateUtil.build_command(move_action)
                action_strs.append(action_str)
        else:
            # 使用模型进行决策
            # print("使用对线模型决定英雄%s的行动" % hero.hero_name)
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

            if hero_name == self.model1_hero:
                self.model1_prev_act = self.model1_act
                self.model1_act = action.output_index
            else:
                self.model2_prev_act = self.model2_act
                self.model2_act = action.output_index

            # 如果是要求英雄施法回城，更新英雄状态，这里涉及到后续多帧是否等待回城结束
            if action.action == CmdActionEnum.CAST and int(action.skillid) == 6:
                print("英雄%s释放了回城" % hero_name)
                self.hero_strategy[hero.hero_name] = ActionEnum.town_ing

            # 如果是选择了撤退，进行特殊标记，会影响到后续的行为
            if action.action == CmdActionEnum.RETREAT:
                print("英雄%s释放了撤退，撤退点为%s" % (hero_name, action.tgtpos.to_string()))
                self.hero_strategy[hero.hero_name] = ActionEnum.retreat
                self.retreat_pos = action.tgtpos

            # 保存action信息到状态帧中
            state_info.add_action(action)
        return action_strs
        # rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        # rsp_str = JSON.dumps(rsp_obj)
        # return rsp_str

