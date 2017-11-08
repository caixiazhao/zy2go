#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON
import random

import tensorflow as tf
import time
from time import gmtime, strftime

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum
from train.linemodel_ppo1 import LineModel_PPO1
from util.linetrainer_policy import LineTrainerPolicy
from util.modelthread import ModelThread
from util.replayer import Replayer
from util.stateutil import StateUtil
import baselines.common.tf_util as U
from datetime import datetime

class LineTrainerPPO:
    TOWN_HP_THRESHOLD = 0.3

    def __init__(self, battle_id, save_dir, model_process, model1_hero, model1_cache,
                 model2_hero=None, model2_cache=None, real_hero=None,
                 policy_ratio=-1, policy_continue_acts=3):
        self.battle_id = battle_id
        self.retreat_pos = None
        self.hero_strategy = {}
        self.state_cache = []
        self.model1_hero = model1_hero
        self.model2_hero = model2_hero
        self.model1_total_death = 0
        self.model2_total_death = 0
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
                self.model1_total_death += StateUtil.if_hero_dead(state_info, next_state, hero_name)
                total_death = self.model1_total_death
            else:
                self.model2_total_death += StateUtil.if_hero_dead(state_info, next_state, hero_name)
                total_death = self.model2_total_death
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

    def remember_replay(self, state_infos, state_index, model_cache, model_process, hero_name, rival_hero,
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
            model_name = ModelThread.NAME_MODEL_1 if hero_name == self.model1_hero else ModelThread.NAME_MODEL_2
            if o4r is not None:
                # 批量计算的情况下等待结果。但是不清空训练完成信号，防止还有训练器没有收到这个信号。
                # 等到下次训练开始再清空
                # 一直等待，这里需要观察客户端连接超时开始重试后的情况
                # TODO 这里清空缓存是不是不太好
                model_process.train_queue.put((self.battle_id, model_name, o4r, batchsize))
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
            # 即使在当前帧模型没有决策的情况下，也可能触发结束条件和启动训练
            rew = 10 if loss_team != hero_info.team else -10
            model_cache.change_last(new, rew)
            prev_new = model_cache.get_prev_new()
            o4r, batch_size = model_cache.output4replay(prev_new, -1)
            model_name = ModelThread.NAME_MODEL_1 if hero_name == self.model1_hero else ModelThread.NAME_MODEL_2
            if o4r is not None:
                model_process.train_queue.put((self.battle_id, model_name, o4r, batch_size))
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
            return ''

        if raw_state_info.tick == 43560:
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

        # 持久化
        self.state_cache.append(state_info)
        # self.save_state_log(state_info)

        # 首先得到模型的选择，同时会将选择action记录到当前帧中
        action_strs = []
        if self.model1_hero is not None:
            actions_model1, restart = self.build_response(self.state_cache, -1, self.model1_hero)
            action_strs.extend(actions_model1)
        if self.model2_hero is not None and not restart:
            actions_model2, restart = self.build_response(self.state_cache, -1, self.model2_hero)
            action_strs.extend(actions_model2)

        # 计算奖励值，如果有真实玩家，因为需要推测行为的原因，则多往前回朔几帧
        reward_state_idx = -2 if self.real_hero is None else -4
        new = 0
        if len(self.state_cache) + reward_state_idx > 0:
            new, loss_team = self.if_restart(self.state_cache, reward_state_idx)
            if self.model1_hero is not None:
                self.remember_replay(self.state_cache, reward_state_idx, self.model1_cache, self.model_process,
                                         self.model1_hero, self.model2_hero, new, loss_team)
            if self.model2_hero is not None:
                self.remember_replay(self.state_cache, reward_state_idx, self.model2_cache, self.model_process,
                                         self.model2_hero, self.model1_hero, new, loss_team)

        # 如果达到了重开条件，重新开始游戏
        # 当线上第一个塔被摧毁时候重开
        if new == 1 or restart:
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]

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

    # 双方英雄集中到中路中间区域，进行对线
    # 一方英雄回城之后，负责等他满血后回到对战区
    def build_response(self, state_cache, state_index, hero_name):
        action_strs=[]
        restart = False

        # 对于模型，分析当前帧的行为
        if self.real_hero != hero_name:
            state_info = state_cache[state_index]
        # 如果有真实玩家，我们需要一些历史数据，所以分析3帧前的行为
        elif len(state_cache) > 3:
            state_info = state_cache[state_index-3]
            next1_state_info = state_cache[state_index-2]
            next2_state_info = state_cache[state_index-1]
            next3_state_info = state_cache[state_index]
        else:
            return action_strs

        # 如果有可以升级的技能，优先升级技能3
        hero = state_info.get_hero(hero_name)
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
        nearest_friend_units = StateUtil.get_nearby_friend_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)

        # 开始根据策略决定当前的行动
        # 对线情况下，首先拿到兵线，朝最前方的兵线移动
        # 如果周围有危险（敌方单位）则启动对线模型
        # 如果周围有小兵或者塔，需要他们都是在指定线上的小兵或者塔
        line_index = 1
        near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
        nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)
        if (len(near_enemy_units_in_line) == 0 and len(nearest_enemy_tower_in_line) == 0 and (
                len(near_enemy_heroes) == 0 or
                StateUtil.if_in_line(hero, line_index, 4000) == -1)
            ) or\
            (len(nearest_friend_units) == 0 and len(near_enemy_units_in_line) == 0 and
            len(near_enemy_heroes) == 0 and len(nearest_enemy_tower_in_line) == 1):
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
            if self.real_hero != hero_name:
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
                begin_time = datetime.now()
                action, explorer_ratio, action_ratios = self.get_action(state_info, hero_name, rival_hero)
                end_time = datetime.now()
                delta = end_time - begin_time
                self.time_cache.append(delta.microseconds)
                if len(self.time_cache) >= 1000:
                    print("average model time", sum(self.time_cache)//len(self.time_cache))
                    self.time_cache = []

                # 考虑使用固定策略
                # 如果决定使用策略，会连续n条行为全都采用策略（比如确保对方残血时候连续攻击的情况）
                # 如果策略返回为空则表示策略中断
                if self.policy_ratio > 0 and (
                        0 < self.cur_policy_act_idx_map[hero_name] < self.policy_continue_acts
                        or random.uniform(0, 1) <= self.policy_ratio
                ):
                    policy_action = LineTrainerPolicy.choose_action(state_info, action_ratios, hero_name, rival_hero,
                                            near_enemy_units, nearest_enemy_tower, nearest_friend_units)
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
                    print('battle_id', self.battle_id, '训练结束，重启游戏')
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

    def get_action(self, state_info, hero_name, rival_hero):
        model_name = ModelThread.NAME_MODEL_1 if hero_name == self.model1_hero else ModelThread.NAME_MODEL_2
        self.model_process.action_queue.put((self.battle_id, model_name, state_info, hero_name, rival_hero))

        # 有一个总的等待时长，如果超时则表示后台模型线程在处理这场战斗的请求时候出现了什么问题
        timeout = time.time() + 60
        while True:
            if time.time() > timeout:
                print('line_trainer', self.battle_id, '很久没有收到模型的计算结果')
                return None

            # 超时会有异常抛出
            self.model_process.done_signal.wait(10)
            print('line_trainer ', self.battle_id, '等到一个信号')
            # check package
            with self.model_process.lock:
                if (self.battle_id, model_name) in self.model_process.results.keys():
                    action, explorer_ratio, action_ratios = self.model_process.results.pop((self.battle_id, model_name))
                    self.model_process.done_signal.clear()
                    return action, explorer_ratio, action_ratios


    def wait_train(self, battle_id, model_name, o4r, batchsize, model_cache, model_process):
        if model_process.train_done_signal.is_set():
            model_process.train_done_signal.clear()
        model_process.train_queue.put((battle_id, model_name, o4r, batchsize))
        print('line_trainer', battle_id, '开始等待训练结果')
        model_process.train_done_signal.wait()
        model_cache.clear_cache()
