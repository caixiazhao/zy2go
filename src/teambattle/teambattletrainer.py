#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as JSON

# 5v5团战控制器
# 需要完成以下任务
#   战斗开始升级英雄到指定级别，购买指定道具
#   两边英雄达到指定位置，目前可以先指定为中路河道
#   设置一个战斗范围，只有死亡和撤退可以脱离战斗范围（如何执行撤退？）
#   战斗中由模型给出每个英雄的行为
#   计算双方战斗得分

# 控制开团
#   首先根据英雄持续搜索周围的敌方英雄，锁链式的找到所有在周围的英雄
#   然后，屏蔽不可用的技能时候，如果是因为距离过远，将结果变为向对方移动
#   最后，设定一个团战范围，如果英雄想要离开团战圈子，需要将他拉回来

#   首先尝试的方案：
#   输入考虑添加其它人的行为
from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from model.skillcfginfo import SkillTargetEnum
from model.stateinfo import StateInfo
from teambattle.team_ppocache import TEAM_PPO_CACHE
from teambattle.teambattle_input import TeamBattleInput
from teambattle.teambattle_policy import TeamBattlePolicy
from teambattle.teambattle_util import TeamBattleUtil
from train.cmdactionenum import CmdActionEnum
from util.equiputil import EquipUtil
from util.httputil import HttpUtil
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from time import gmtime, strftime
import numpy as np
from random import shuffle, randint


class TeamBattleTrainer:

    BATTLE_POINT_X = 0
    BATTLE_POINT_Z = -31000
    BATTLE_CIRCLE = PosStateInfo(BATTLE_POINT_X, 0, BATTLE_POINT_Z)
    BATTLE_CIRCLE_RADIUS_BATTLE_START = 8
    BATTLE_CIRCLE_RADIUS_BATTLE_ING = 10
    SHRINK_TIME = 60

    def __init__(self, save_root_path, battle_id, model_util, gamma):
        self.battle_id = battle_id
        self.model_util = model_util
        self.state_cache = []
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.raw_log_file = open(save_root_path + '/raw_' + str(battle_id) + '.log', 'w')
        self.dead_heroes = []
        self.battle_started = -1
        self.model_caches = {}
        self.rebooting = False
        for hero in self.heros:
            self.model_caches[hero] = TEAM_PPO_CACHE(gamma)

        # 计算奖励值时候因为要看历史数据，所以需要这两个当时的状态信息。后续可以考虑如何避免这种缓存
        self.battle_heroes_cache = []
        self.dead_heroes_cache = []
        self.data_inputs = []

    def save_raw_log(self, raw_log_str):
        self.raw_log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + raw_log_str + "\n")
        self.raw_log_file.flush()

    def build_response(self, raw_state_str):
        self.save_raw_log(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None
        response_strs = []

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)

        # 重开时候会有以下报文  {"wldstatic":{"ID":9051},"wldruntime":{"State":0}}
        if raw_state_info.tick == -1:
            return {"ID": raw_state_info.battleid, "tick": -1}

        if raw_state_info.tick <= StateUtil.TICK_PER_STATE and (prev_state_info is None or prev_state_info.tick > raw_state_info.tick):
            print("clear")
            prev_state_info = None
            self.state_cache = []
            self.battle_started = -1
            self.battle_heroes_cache = []
            self.dead_heroes = []
            self.dead_heroes_cache = []
            self.data_inputs = []
            self.rebooting = False
        elif prev_state_info is None and raw_state_info.tick > StateUtil.TICK_PER_STATE :
            # 不是开始帧的话直接返回重启游戏
            # 还有偶然情况下首帧没有tick（即-1）的情况，这种情况下只能重启本场战斗
            print("battle_id", self.battle_id, "tick", state_info.tick, '不是开始帧的话直接返回重启游戏', raw_state_info.tick)
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]
            rsp_obj = {"ID": raw_state_info.battleid, "tick": raw_state_info.tick, "cmd": action_strs}
            rsp_str = JSON.dumps(rsp_obj)
            return rsp_str

        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)
        hero = state_info.get_hero("27")

        if hero is None or hero.hp is None:
            # 偶然情况处理，如果找不到英雄，直接重开
            print("battle_id", self.battle_id, "tick", state_info.tick, '不是开始帧的话直接返回重启游戏', raw_state_info.tick)
            action_strs = [StateUtil.build_action_command('27', 'RESTART', None)]
            rsp_obj = {"ID": raw_state_info.battleid, "tick": raw_state_info.tick, "cmd": action_strs}
            rsp_str = JSON.dumps(rsp_obj)
            return rsp_str

        # 战斗前准备工作
        if len(self.state_cache) == 0:
            # 第一帧的时候，添加金钱和等级
            for hero in self.heros:
                add_gold_cmd = CmdAction(hero, CmdActionEnum.ADDGOLD, None, None, None, None, None, None, None)
                add_gold_cmd.gold = 3000
                add_gold_str = StateUtil.build_command(add_gold_cmd)
                response_strs.append(add_gold_str)

                add_lv_cmd = CmdAction(hero, CmdActionEnum.ADDLV, None, None, None, None, None, None, None)
                add_lv_cmd.lv = 9
                add_lv_str = StateUtil.build_command(add_lv_cmd)
                response_strs.append(add_lv_str)
        elif len(self.state_cache) > 1:
            # 第二帧时候开始，升级技能，购买装备，这个操作可能会持续好几帧
            for hero in self.heros:
                upgrade_cmd = self.upgrade_skills(state_info, hero)
                if upgrade_cmd is not None:
                    response_strs.append(upgrade_cmd)

                buy_cmd = self.buy_equip(state_info, hero)
                if buy_cmd is not None:
                    response_strs.append(buy_cmd)

        for hero in self.heros:
            # 判断是否英雄死亡
            if prev_state_info is not None:
                dead = StateUtil.if_hero_dead(prev_state_info, state_info, hero)
                if dead == 1 and hero not in self.dead_heroes:
                    print("battle_id", self.battle_id, "tick", state_info.tick, "英雄死亡", hero, "tick", state_info.tick)
                    self.dead_heroes.append(hero)

        # 首先要求所有英雄站到团战圈内，然后开始模型计算，这时候所有的行动都有模型来决定
        # 需要过滤掉无效的行动，同时屏蔽会离开战斗圈的移动
        #TODO 开始团战后，如果有偶尔的技能移动会离开圈，则拉回来

        # 这里会排除掉死亡的英雄，他们不需要再加入团战
        # 团战范围在收缩
        battle_range = self.cal_battle_range(len(self.state_cache) - self.battle_started)
        heroes_in_range, heroes_out_range = TeamBattleTrainer.all_in_battle_range(state_info, self.heros, self.dead_heroes, battle_range)
        print('battle_id', self.battle_id, "battle_range", battle_range)

        # 缓存参战情况和死亡情况，用于后续训练
        self.battle_heroes_cache.append(list(heroes_in_range))
        self.dead_heroes_cache.append(list(self.dead_heroes))

        if state_info.tick >= 142560:
            debuginfo = True

        # 团战还没有开始，有英雄还在圈外
        if len(heroes_out_range) > 0:
            if self.battle_started > -1:
                print('battle_id', self.battle_id, "战斗已经开始，但是为什么还有英雄在团战圈外", ','.join(heroes_out_range), "battle_range", battle_range)

            # 移动到两个开始战斗地点附近
            # 如果是团战开始之后，移动到团战中心点
            for hero in heroes_out_range:
                start_point_x = 0
                start_point_z = TeamBattleTrainer.BATTLE_CIRCLE_RADIUS_BATTLE_START * 1000 if self.battle_started == -1 else 0
                if TeamBattleUtil.get_hero_team(hero) == 0:
                    start_point_z *= -1
                start_point_z += TeamBattleTrainer.BATTLE_POINT_Z
                tgt_pos = PosStateInfo(start_point_x, 0, start_point_z)
                move_action = CmdAction(hero, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, None, None)
                mov_cmd_str = StateUtil.build_command(move_action)
                response_strs.append(mov_cmd_str)
        # 团战已经开始
        elif not self.rebooting:
            if self.battle_started == -1:
                self.battle_started = len(self.state_cache)
            action_cmds, input_list = self.get_model_actions(state_info, heroes_in_range)
            data_input_map = {}
            for action_cmd, data_input in zip(action_cmds, input_list):
                hero_info = state_info.get_hero(action_cmd.hero_name)
                # 测试，蕾娜斯技能
                # if int(hero_info.cfg_id) == 101 or int(hero_info.cfg_id) == 106:
                action_str = StateUtil.build_command(action_cmd)
                response_strs.append(action_str)
                state_info.add_action(action_cmd)
                data_input_map[action_cmd.hero_name] = data_input

            # 缓存所有的模型输入，用于后续训练
            self.data_inputs.append(data_input_map)

        # 添加记录到缓存中
        self.state_cache.append(state_info)

        # 将模型行为加入训练缓存，同时计算奖励值
        # 注意：因为奖励值需要看后续状态，所以这个计算会有延迟
        last_x_index = 2
        if self.battle_started > -1 and len(self.data_inputs) >= last_x_index:
            if self.rebooting:
                # 测试发现重启指令发出之后，可能下一帧还没开始重启战斗，这种情况下抛弃训练
                print("battle_id", self.battle_id, "tick", state_info.tick, "warn", "要求重启战斗，但是还在收到后续帧状态")
            else:
                state_index = len(self.state_cache) - last_x_index
                win, win_team, left_heroes = self.remember_replay_heroes(-last_x_index, state_index, battle_range)

                # 团战结束条件
                # 首先战至最后一人
                # all_in_team = TeamBattleUtil.all_in_one_team(heroes_in_range)
                # if self.battle_started:
                #     if len(self.dead_heroes) >= 9 or (len(self.dead_heroes) >= 5 and all_in_team > -1):
                if win == 1:
                    # 重启游戏
                    print('battle_id', self.battle_id, "重启游戏", "剩余人员", ','.join(left_heroes))
                    response_strs = [StateUtil.build_action_command('27', 'RESTART', None)]
                    self.rebooting = True
        # battle_heros = self.search_team_battle(state_info)
        # if len(battle_heros) > 0:
        #     print("team battle heros", ';'.join(battle_heros))
        #
        # heros_need_model = []
        # for hero in self.heros:
        #     # 判断是否英雄死亡
        #     if prev_state_info is not None:
        #         dead = StateUtil.if_hero_dead(prev_state_info, state_info, hero)
        #         if dead == 1 and hero not in self.dead_heroes:
        #             self.dead_heroes.append(hero)
        #
        #     # 复活的英雄不要再去参团
        #     if hero in self.dead_heroes:
        #         continue
        #
        #     # near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero, TeamBattleTrainer.MODEL_RANGE)
        #     if hero not in battle_heros:
        #         # 移动到团战点附近，添加部分随机
        #         rdm_delta_x = randint(0, 1000)
        #         rdm_delta_z = randint(0, 1000)
        #         tgt_pos = PosStateInfo(TeamBattleTrainer.BATTLE_POINT_X + rdm_delta_x, 0, TeamBattleTrainer.BATTLE_POINT_Z + rdm_delta_z)
        #         move_action = CmdAction(hero, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, None, None)
        #         mov_cmd_str = StateUtil.build_command(move_action)
        #         response_strs.append(mov_cmd_str)
        #     else:
        #         # 启动模型决策
        #         heros_need_model.append(hero)
        #
        # if len(heros_need_model) > 0:
        #     action_cmds = self.get_model_actions(state_info, heros_need_model)
        #     for action_cmd in action_cmds:
        #         action_str = StateUtil.build_command(action_cmd)
        #         response_strs.append(action_str)
        #         state_info.add_action(action_cmd)

            #TODO 记录模型输出，用于后续训练

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": response_strs}
        rsp_str = JSON.dumps(rsp_obj)
        print('battle_id', self.battle_id, 'response', rsp_str)
        return rsp_str

    def cal_battle_range(self, action_times):
        battle_range = TeamBattleTrainer.BATTLE_CIRCLE_RADIUS_BATTLE_START if self.battle_started == -1 \
            else TeamBattleTrainer.BATTLE_CIRCLE_RADIUS_BATTLE_ING - int(action_times / TeamBattleTrainer.SHRINK_TIME)
        return battle_range

    # last_x_index 表示这是倒数第x个状态，这里不用准确数字而是用-1、-2是因为state_cache，data_inputs长度不同
    # state_index 表示状态在帧缓存中的位置，用于计算奖励值折旧时候使用
    def remember_replay_heroes(self, last_x_index, state_index, battle_range):
        prev_state = self.state_cache[last_x_index - 1]
        state_info = self.state_cache[last_x_index]
        next_state = self.state_cache[last_x_index + 1]
        battle_heroes = self.battle_heroes_cache[last_x_index]
        dead_heroes = self.dead_heroes_cache[last_x_index]
        data_input_map = self.data_inputs[last_x_index]

        # 计算奖励值情况
        state_info, win, win_team, left_heroes = self.model_util.cal_rewards(prev_state, state_info, next_state, battle_heroes, dead_heroes)

        if state_info.tick >= 50028:
            debug_here = 1

        # 设置一场战斗的最大游戏时长，到时直接重启，所有玩家最终奖励为零，没有输赢
        if win == 0 and battle_range <= 0:
            print('battle_id', self.battle_id, "到达游戏最大时长，直接重启，需要确认是否有异常情况")
            win = 1

        for action in state_info.actions:
            # 行为有可能为空，比如英雄已经挂了，但是他最后的动作在后续几帧都可能有影响，也有可能是因为
            # print('battle_id', self.battle_id, "remember_replay_heroes", action.hero_name)
            data_input = data_input_map[action.hero_name] if action.action != CmdActionEnum.EMPTY else None
            self.remember_train_data(state_info, state_index, data_input, action.hero_name, win)

        # 如果战斗结束，需要训练所有模型
        if win == 1:
            for hero_name in self.heros:
                model_cache = self.model_caches[hero_name]
                prev_new = model_cache.get_prev_new()
                o4r, batchsize = model_cache.output4replay(prev_new)

                # 提交给训练模块
                print('battle_id', self.battle_id, 'trainer', hero_name, '添加训练集')
                self.model_util.set_train_data(hero_name, self.battle_id, o4r, batchsize)
                model_cache.clear_cache()

        print("battle_id", self.battle_id, "tick", state_info.tick, "remember_replay_heroes", "win", win, "剩余人员", ','.join(left_heroes),
              "输入—战斗人员", ','.join(battle_heroes), "输入—阵亡人员", ','.join(dead_heroes))
        return win, win_team, left_heroes

    # 保存训练数据，计算行为奖励，触发训练
    #TODO 在游戏重启时候需要同时训练所有的模型
    def remember_train_data(self, state_info, state_index, data_input, hero_name, new):
        hero_act = state_info.get_hero_action(hero_name)
        model_cache = self.model_caches[hero_name]

        if hero_act is not None:
            # prev_new 简单计算，可能会有问题
            prev_new = model_cache.get_prev_new()
            ob = data_input
            ac = hero_act.output_index
            vpred = hero_act.vpred
            rew = hero_act.reward
            model_cache.remember(ob, ac, vpred, new, rew, prev_new, state_index)

    @staticmethod
    def all_in_battle_range(state_info, all_heroes, dead_heroes, battle_range):
        heroes_in = []
        heroes_out = []
        for hero in all_heroes:
            if hero not in dead_heroes:
                hero_info = state_info.get_hero(hero)
                dis = TeamBattleTrainer.in_battle_range(hero_info.pos, battle_range)
                if dis != -1:
                    heroes_out.append(hero)
                    # print('battle_id', state_info.battleid, "all_in_battle_range", "found hero not in circle", hero, "battle_range", battle_range, "distance", dis)
                else:
                    heroes_in.append(hero)
        return heroes_in, heroes_out

    # 考察一个英雄是否在团战圈中
    @staticmethod
    def in_battle_range(pos, battle_range):
        dis = StateUtil.cal_distance2(pos, TeamBattleTrainer.BATTLE_CIRCLE)
        if dis < battle_range * 1000 + 500:
            return -1
        return dis

    def search_team_battle(self, state_info):
        max_team = set()
        for hero in self.heros:
            battle_heros = self.search_team_battle_hero(state_info, hero)
            if len(battle_heros) > 1 and len(battle_heros) > len(max_team):
                max_team = battle_heros
        return max_team

    def search_team_battle_hero(self, state_info, hero):
        # 检查是否有团战，并且得到团战的范围内所有的单位
        # 团战范围的定义
        # 首先从一个英雄开始找起，如果它周围有敌人，就把敌人和自己人全都列为范围内，然后用新的人物继续寻找
        # 注：这里只找一个开团点
        checked_heros = set()
        team_battle_heros = set()

        # 找到第一个周围有敌人的
        team_battle_heros.add(hero)

        while len(checked_heros) < len(team_battle_heros):
            for hero in team_battle_heros.copy():
                if hero not in checked_heros:
                    near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero, TeamBattleTrainer.MODEL_RANGE)
                    for enemy in near_enemy_heroes:
                        team_battle_heros.add(enemy.hero_name)
                    checked_heros.add(hero)

        return team_battle_heros

    def get_model_actions(self, state_info, heros):
        # 目前的思路是，每个英雄首先自己算行为，然后拿到每个英雄的行为之后，将状态信息+队友的选择都交给模型，重新计算自己的选择，迭代
        # 最后得到每个英雄的行为

        # TODO 另一个思路：调整为第一个人先选，然后第二个人，一直往后，后面的人会在参数中添加上之前人的行为
        # TODO 同时可以变成按照模型给出maxq大小来决定谁先选
        # 这样的好处是所有人选择的行为就是最后执行的行为

        # 暂时为随机英雄先选
        random_heros = list(heros)
        shuffle(random_heros)

        # 得到当前团战范围，因为会收缩
        battle_range = self.cal_battle_range(len(self.state_cache) - self.battle_started)

        action_cmds = []
        input_list = []
        for hero in random_heros:
            hero_info = state_info.get_hero(hero)
            data_input = TeamBattleInput.gen_input(state_info, hero)
            data_input = np.array(data_input)

            # 对于之前的英雄行为，加入输入
            for prev_action in action_cmds:
                data_input = TeamBattleInput.add_other_hero_action(data_input, hero_info, prev_action)

            action_list, explor_value, vpreds, clear_cache = self.model_util.get_action_list(self.battle_id, hero, data_input)
            action_str = ' '.join(str("%.4f" % float(act)) for act in action_list)
            print("battle_id", self.battle_id, "tick", state_info.tick, "hero", hero, "model action list", action_str)
            unaval_list = TeamBattleTrainer.list_unaval_actions(action_list, state_info, hero, heros, battle_range)
            unaval_list_str = ' '.join(str("%.4f" % float(act)) for act in unaval_list)
            print("battle_id", self.battle_id, "tick", state_info.tick, "hero", hero, "model remove_unaval_actions", unaval_list_str)
            friends, opponents = TeamBattleUtil.get_friend_opponent_heros(heros, hero)
            action_cmd, max_q, selected = TeamBattleTrainer.get_action_cmd(action_list, unaval_list, state_info, hero, friends, opponents)
            print("battle_id", self.battle_id, "tick", state_info.tick, "hero", hero, "model get_action", StateUtil.build_command(action_cmd), "max_q", max_q, "selected", selected)

            # 如果模型升级了，需要清空所有缓存用作训练的行为
            if clear_cache:
                print('battle_id', self.battle_id, '清空训练缓存')
                for hero_name in self.heros:
                    self.model_caches[hero_name].clear_cache()

            action_cmds.append(action_cmd)
            input_list.append(data_input)
        return action_cmds, input_list

    @staticmethod
    # 过滤输出结果，删除掉不可执行的选择
    # 这里有两个思路，像原来一样只执行可以执行的
    # 第二种是面对不可执行的，我们就选择逼近对方
    # 输出信息：
    # 移动：八个方向；物理攻击：五个攻击目标；技能1：五个攻击目标；技能2：五个攻击目标；技能3：五个攻击目标
    # 技能攻击目标默认为对方英雄。如果是辅助技能，目标调整为自己人
    # 对于技能可以是自己也可以是对方的，目前无法处理
    def list_unaval_actions(acts, state_info, hero_name, team_battle_heros, battle_range, debug=False):
        friends, opponents = TeamBattleUtil.get_friend_opponent_heros(team_battle_heros, hero_name)
        avail_list = acts.copy()
        for i in range(len(acts)):
            hero = state_info.get_hero(hero_name)
            selected = i
            if selected < 8:  # move
                # 不再检查movelock，因为攻击硬直也会造成这个值变成false（false表示不能移动）
                # 屏蔽会离开战圈的移动
                fwd = StateUtil.mov(selected)
                move_pos = TeamBattleUtil.play_move(hero, fwd)
                in_range = TeamBattleTrainer.in_battle_range(move_pos, battle_range)
                if in_range != -1:
                    avail_list[selected] = -1
                else:
                    avail_list[selected] = 1
                continue
            elif selected < 13:  # 物理攻击：五个攻击目标
                if hero.skills[0].canuse != True and (hero.skills[0].cd == 0 or hero.skills[0].cd == None):
                    # 普通攻击也有冷却，冷却时canuse=false，此时其实我们可以给出攻击指令的
                    # 所以只有当普通攻击冷却完成（cd=0或None）时，canuse仍为false我们才认为英雄被控，不能攻击
                    # 被控制住
                    avail_list[selected] = -1
                    if debug: print("普攻受限，放弃普攻")
                    continue
                else:  # 敌方英雄
                    target_index = selected - 8
                    target_hero = TeamBattleUtil.get_target_hero(hero_name, friends, opponents, target_index)
                    if target_hero is None:
                        avail_list[selected] = -1
                        if debug: print("找不到对应目标英雄")
                        continue
                    rival_info = state_info.get_hero(target_hero)
                    dist = StateUtil.cal_distance(hero.pos, rival_info.pos)
                    # 英雄不可见
                    if not rival_info.is_enemy_visible():
                        avail_list[selected] = -1
                        if debug: print("英雄不可见")
                        continue
                    # 英雄太远，放弃普攻
                    # if dist > self.att_dist:
                    if dist > StateUtil.ATTACK_HERO_RADIUS:
                        avail_list[selected] = 0
                        if debug: print("英雄太远，放弃普攻")
                        continue
                    # 对方英雄死亡时候忽略这个目标
                    elif rival_info.hp <= 0:
                        avail_list[selected] = -1
                        if debug: print("对方英雄死亡")
                        continue
                avail_list[selected] = 1
            elif selected < 28:  # skill1
                # TODO 处理持续施法，目前似乎暂时还不需要
                skillid = int((selected - 13) / 5 + 1)
                if hero.skills[skillid].canuse != True:
                    # 被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    avail_list[selected] = -1
                    if debug: print("技能受限，放弃施法" + str(skillid) + " hero.skills[x].canuse=" + str(
                        hero.skills[skillid].canuse) + " tick=" + str(state_info.tick))
                    continue
                if hero.skills[skillid].cost is not None and hero.skills[skillid].cost > hero.mp:
                    # mp不足
                    # 特殊情况，德古拉1，2技能是扣除血量
                    if not (hero.cfg_id == '103' and (skillid == 1 or skillid == 2)):
                        avail_list[selected] = -1
                        if debug: print("mp不足，放弃施法" + str(skillid))
                        continue
                if hero.skills[skillid].cd > 0:
                    # 技能未冷却
                    avail_list[selected] = -1
                    if debug: print("技能cd中，放弃施法" + str(skillid))
                    continue
                tgt_index = selected - 13 - (skillid - 1) * 5
                skill_info = SkillUtil.get_skill_info(hero.cfg_id, skillid)
                # TODO 这个buff逻辑还没有测试对应的英雄
                is_buff = True if skill_info.cast_target == SkillTargetEnum.buff else False
                is_self = True if skill_info.cast_target == SkillTargetEnum.self else False
                tgt_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, tgt_index, is_buff, is_self)

                if tgt_hero is None:
                    avail_list[selected] = -1
                    if debug: print("找不到对应目标英雄")
                    continue
                [tgtid, tgtpos] = TeamBattleTrainer.choose_skill_target(tgt_index, state_info,
                                                                        skill_info, hero_name, hero.pos, tgt_hero, debug)
                if tgtid == -1 or tgtid == 0:
                    avail_list[selected] = tgtid
                    if debug: print("目标不符合施法要求")
                    continue
                else:
                    # 根据规则再去过滤
                    policy_avail = TeamBattlePolicy.check_skill_condition(skill_info, state_info, hero, tgt_hero, friends, opponents)
                    if not policy_avail:
                        avail_list[selected] == -1
                    else:
                        avail_list[selected] = 1
        return avail_list

    @staticmethod
    def choose_skill_target(selected, state_info, skill_info, hero_name, pos, tgt_hero_name, debug=False):
        hero_info = state_info.get_hero(hero_name)
        if selected == 0:
            # 施法目标为自己
            # 首先判断施法目标是不是只限于敌方英雄
            if skill_info.cast_target == SkillTargetEnum.self and hero_name != str(tgt_hero_name):
                if debug: print("施法目标为self，但是对象不是自己")
                return [-1, None]
            tgtid = hero_name
            # TODO 这里有点问题，如果是目标是自己的技能，是不是要区分下目的，否则fwd计算会出现问题
            tgtpos = None
        if selected <= 4:
            # 攻击对方英雄
            tgt_hero = state_info.get_hero(tgt_hero_name)
            if tgt_hero.team != hero_info.team and not tgt_hero.is_enemy_visible():
                if debug: print("敌方英雄不可见")
                tgtid = -1
                tgtpos = None
            elif StateUtil.cal_distance(tgt_hero.pos, pos) > skill_info.cast_distance:
                if debug: print("技能攻击不到对方 %s %s %s" % (
                    tgt_hero_name, StateUtil.cal_distance(tgt_hero.pos, pos), skill_info.cast_distance))
                tgtid = 0
                tgtpos = None
            # 对方英雄死亡时候忽略这个目标
            elif tgt_hero.hp <= 0:
                if debug: print("技能攻击不了对方，对方已经死亡")
                tgtid = -1
                tgtpos = None
            else:
                tgtid = tgt_hero_name
                tgtpos = tgt_hero.pos
        return tgtid, tgtpos

    @staticmethod
    def get_action_cmd(action_list, unaval_list, state_info, hero_name, friends, opponents, revert=False):
        hero = state_info.get_hero(hero_name)
        found = False
        while not found:
            max_q = max(action_list)

            if max_q <= -1:
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, hero.pos, None, None, 48, None)
                return action, max_q, -1

            selected = action_list.index(max_q)
            avail_type = unaval_list[selected]
            if avail_type == -1:
                #TODO avail_type == 0: 是否考虑技能不可用时候不接近对方
                # 不可用行为
                action_list[selected] = -1
                continue

            if selected < 8:  # move
                fwd = StateUtil.mov(selected, revert)
                # 根据我们的移动公式计算一个目的地，缺点是这样可能被障碍物阻挡，同时可能真的可以移动距离比我们计算的长
                tgtpos = TeamBattleUtil.set_move_target(hero, fwd)
                # tgtpos = PosStateInfo(hero.pos.x + fwd.x * 15, hero.pos.y + fwd.y * 15, hero.pos.z + fwd.z * 15)
                action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, tgtpos, None, None, selected, None)
                return action, max_q, selected
            elif selected < 13:  # 对敌英雄使用普攻
                target_index = selected - 8
                target_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, target_index)
                target_hero_info = state_info.get_hero(target_hero)
                avail_type = unaval_list[selected]
                if avail_type == 0:
                    action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, target_hero_info.pos, None, None, selected, None)
                else:
                    action = CmdAction(hero.hero_name, CmdActionEnum.ATTACK, 0, target_hero, None, None, None, selected, None)
                return action, max_q, selected
            elif selected < 28:  # skill
                skillid = int((selected - 13) / 5 + 1)
                tgt_index = selected - 13 - (skillid - 1) * 5
                skill_info = SkillUtil.get_skill_info(hero.cfg_id, skillid)
                is_buff = True if skill_info.cast_target == SkillTargetEnum.buff else False
                is_self = True if skill_info.cast_target == SkillTargetEnum.self else False
                tgt_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, tgt_index, is_buff, is_self)
                tgt_pos = state_info.get_hero(tgt_hero).pos
                fwd = tgt_pos.fwd(hero.pos)
                avail_type = unaval_list[selected]
                if avail_type == 0:
                    action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, selected, None)
                else:
                    action = CmdAction(hero.hero_name, CmdActionEnum.CAST, skillid, tgt_hero, tgt_pos, fwd, None, selected, None)
                return action, max_q, selected

    def buy_equip(self, state_info, hero_name):
        # 决定是否购买道具
        buy_action = EquipUtil.buy_equip(state_info, hero_name)
        if buy_action is not None:
            buy_str = StateUtil.build_command(buy_action)
            return buy_str

    def upgrade_skills(self, state_info, hero_name):
        # 如果有可以升级的技能，优先升级技能3
        hero = state_info.get_hero(hero_name)
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            skillid = 3 if 3 in skills else skills[0]
            update_cmd = CmdAction(hero.hero_name, CmdActionEnum.UPDATE, skillid, None, None, None, None, None, None)
            update_str = StateUtil.build_command(update_cmd)
            return update_str




