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
from teambattle.teambattle_input import TeamBattleInput
from teambattle.teambattle_util import TeamBattleUtil
from train.cmdactionenum import CmdActionEnum
from util.equiputil import EquipUtil
from util.httputil import HttpUtil
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from random import randint
from time import gmtime, strftime
import numpy as np
from random import shuffle

class TeamBattleTrainer:

    BATTLE_POINT_X = 0
    BATTLE_POINT_Z = -30000
    BATTLE_CIRCLE = PosStateInfo(BATTLE_POINT_X, 0, BATTLE_POINT_Z)
    MODEL_RANGE = 15
    BATTLE_CIRCLE_RADIUS = 7

    def __init__(self, battle_id, model_util):
        self.battle_id = battle_id
        self.model_util = model_util
        save_dir = HttpUtil.get_save_root_path()
        self.state_cache = []
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.raw_log_file = open(save_dir + '/raw_' + str(battle_id) + '.log', 'w')
        self.dead_heroes = []
        self.battle_started = False

    def save_raw_log(self, raw_log_str):
        self.raw_log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + raw_log_str + "\n")
        self.raw_log_file.flush()

    def build_response(self, raw_state_str):
        print(raw_state_str)
        self.save_raw_log(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None
        response_strs = []

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)
        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)

        # 重开时候会有以下报文  {"wldstatic":{"ID":9051},"wldruntime":{"State":0}}
        if raw_state_info.tick == -1:
            return {"ID": raw_state_info.battleid, "tick": -1}

        if raw_state_info.tick <= StateUtil.TICK_PER_STATE and (prev_state_info is None or prev_state_info.tick > raw_state_info.tick):
            print("clear")
            prev_state_info = None
            self.state_cache = []
            self.battle_started = False

        # 战斗前准备工作
        if len(self.state_cache) == 0:
            # 第一帧的时候，添加金钱和等级
            for hero in self.heros:
                add_gold_cmd = CmdAction(hero, CmdActionEnum.ADDGOLD, None, None, None, None, None, None, None)
                add_gold_cmd.gold = 5000
                add_gold_str = StateUtil.build_command(add_gold_cmd)
                response_strs.append(add_gold_str)

                add_lv_cmd = CmdAction(hero, CmdActionEnum.ADDLV, None, None, None, None, None, None, None)
                add_lv_cmd.lv = 10
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
                    self.dead_heroes.append(hero)

        # 首先要求所有英雄站到团战圈内，然后开始模型计算，这时候所有的行动都有模型来决定
        # 需要过滤掉无效的行动，同时屏蔽会离开战斗圈的移动
        #TODO 开始团战后，如果有偶尔的技能移动会离开圈，则拉回来

        # 这里会排除掉死亡的英雄，他们不需要再加入团战
        heroes_in_range, heroes_out_range = self.all_in_battle_range(state_info, self.heros, self.dead_heroes)

        # 团战还没有开始，有英雄还在圈外
        if len(heroes_out_range) > 0:
            if self.battle_started:
                print("战斗已经开始，但是为什么还有英雄在团战圈外", ','.join(heroes_out_range))

            # 移动到两个开始战斗地点附近，添加部分随机
            for hero in heroes_out_range:
                start_point_x = TeamBattleTrainer.BATTLE_CIRCLE_RADIUS * 1000
                if TeamBattleUtil.get_hero_team(hero) == 0:
                    start_point_x *= -1
                start_point_z = TeamBattleTrainer.BATTLE_POINT_Z
                tgt_pos = PosStateInfo(start_point_x, 0, start_point_z)
                move_action = CmdAction(hero, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, None, None)
                mov_cmd_str = StateUtil.build_command(move_action)
                response_strs.append(mov_cmd_str)
        # 团战已经开始
        else:
            if not self.battle_started:
                self.battle_started = True
            action_cmds = self.get_model_actions(state_info, heroes_in_range)
            for action_cmd in action_cmds:
                action_str = StateUtil.build_command(action_cmd)
                response_strs.append(action_str)
                state_info.add_action(action_cmd)

        # 团战结束条件
        # 首先战至最后一人
        all_in_team = TeamBattleUtil.all_in_one_team(heroes_in_range)
        if self.battle_started:
            if len(self.dead_heroes) >= 9 or (len(self.dead_heroes) >= 5 and all_in_team > -1):
                # 重启游戏
                print("重启游戏", "剩余人员", ','.join(heroes_in_range))
                response_strs = [StateUtil.build_action_command('27', 'RESTART', None)]

                #TODO 处理奖励值，对于死亡英雄的最终奖励，应该考虑衰减系数
                #TODO 提供训练数据



        #TODO 复活的英雄不要回去参加战斗

        #TODO 设置战斗结束条件

        #TODO 首先移动到己方的汇合位置，然后一起朝团战位置移动

        #TODO 如果离开团战圈，需要拉回来

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


        # 添加记录到缓存中
        self.state_cache.append(state_info)

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": response_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

    def all_in_battle_range(self, state_info, all_heroes, dead_heroes):
        heroes_in = []
        heroes_out = []
        for hero in all_heroes:
            if hero not in dead_heroes:
                hero_info = state_info.get_hero(hero)
                if not TeamBattleTrainer.in_battle_range(hero_info.pos):
                    heroes_out.append(hero)
                else:
                    heroes_in.append(hero)
        if len(heroes_out) > 0:
            print("all_in_battle_range", "found hero not in circle", ','.join(heroes_out))
        return heroes_in, heroes_out

    # 考察一个英雄是否在团战圈中
    @staticmethod
    def in_battle_range(pos):
        dis = StateUtil.cal_distance(pos, TeamBattleTrainer.BATTLE_CIRCLE)
        if dis < TeamBattleTrainer.MODEL_RANGE/2:
            return True
        return False

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

        action_cmds = []
        input_list = []
        for hero in random_heros:
            hero_info = state_info.get_hero(hero)
            data_input = TeamBattleInput.gen_input(state_info, hero)
            data_input = np.array(data_input)

            # 对于之前的英雄行为，加入输入
            for prev_action in action_cmds:
                data_input = TeamBattleInput.add_other_hero_action(data_input, hero_info, prev_action)

            action_list, explor_value, vpreds = self.model_util.get_action_list(hero, data_input)
            action_str = ' '.join(str("%.4f" % float(act)) for act in action_list)
            print("model action list", action_str)
            unaval_list = TeamBattleTrainer.list_unaval_actions(action_list, state_info, hero, heros)
            unaval_list_str = ' '.join(str("%.4f" % float(act)) for act in unaval_list)
            print("model remove_unaval_actions", unaval_list_str)
            friends, opponents = TeamBattleUtil.get_friend_opponent_heros(heros, hero)
            action_cmd = TeamBattleTrainer.get_action_cmd(action_list, unaval_list, state_info, hero, friends, opponents)
            print("model get_action", StateUtil.build_command(action_cmd))

            action_cmds.append(action_cmd)
            input_list.append(data_input)
        return action_cmds

    @staticmethod
    # 过滤输出结果，删除掉不可执行的选择
    # 这里有两个思路，像原来一样只执行可以执行的
    # 第二种是面对不可执行的，我们就选择逼近对方
    # 输出信息：
    # 移动：八个方向；物理攻击：五个攻击目标；技能1：五个攻击目标；技能2：五个攻击目标；技能3：五个攻击目标
    # 技能攻击目标默认为对方英雄。如果是辅助技能，目标调整为自己人
    # 对于技能可以是自己也可以是对方的，目前无法处理
    def list_unaval_actions(acts, state_info, hero_name, team_battle_heros, debug=False):
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
                in_range = TeamBattleTrainer.in_battle_range(move_pos)
                if not in_range:
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
                skillid = int((selected - 13) / 5 + 1)
                if hero.skills[skillid].canuse != True:
                    # 被沉默，被控制住（击晕击飞冻结等）或者未学会技能
                    avail_list[selected] = -1
                    if debug: print("技能受限，放弃施法" + str(skillid) + " hero.skills[x].canuse=" + str(
                        hero.skills[skillid].canuse) + " tick=" + str(state_info.tick))
                    continue
                if hero.skills[skillid].cost is not None and hero.skills[skillid].cost > hero.mp:
                    # mp不足
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
                if skill_info.cast_target == SkillTargetEnum.self:
                        # TODO
                        cast_debug = 1
                is_buff = True if skill_info.cast_target == SkillTargetEnum.buff else False
                tgt_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, tgt_index, is_buff)

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
                    avail_list[selected] = 1
        return avail_list

    @staticmethod
    def choose_skill_target(selected, state_info, skill_info, hero_name, pos, tgt_hero_name, debug=False):
        hero_info = state_info.get_hero(hero_name)
        if selected == 0:
            # 施法目标为自己
            # 首先判断施法目标是不是只限于敌方英雄
            if skill_info.cast_target == SkillTargetEnum.rival:
                return [-1, None]
            tgtid = hero_name
            # TODO 这里有点问题，如果是目标是自己的技能，是不是要区分下目的，否则fwd计算会出现问题
            tgtpos = None
        elif selected <= 4:
            # 攻击对方英雄
            # 首先判断施法目标是不是只限于自己
            if skill_info.cast_target == SkillTargetEnum.self:
                return [-1, None]
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
                return action

            selected = action_list.index(max_q)
            avail_type = unaval_list[selected]
            if avail_type == -1:
                # 不可用行为
                action_list[selected] = -1
                continue

            if selected < 8:  # move
                fwd = StateUtil.mov(selected, revert)
                tgtpos = PosStateInfo(hero.pos.x + fwd.x * 15, hero.pos.y + fwd.y * 15, hero.pos.z + fwd.z * 15)
                action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, tgtpos, None, None, selected, None)
                return action
            elif selected < 13:  # 对敌英雄使用普攻
                target_index = selected - 8
                target_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, target_index)
                target_hero_info = state_info.get_hero(target_hero)
                avail_type = unaval_list[selected]
                if avail_type == 0:
                    action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, target_hero_info.pos, None, None, selected, None)
                else:
                    action = CmdAction(hero.hero_name, CmdActionEnum.ATTACK, 0, target_hero, None, None, None, selected, None)
                return action
            elif selected < 28:  # skill
                skillid = int((selected - 13) / 5 + 1)
                tgt_index = selected - 13 - (skillid - 1) * 5
                skill_info = SkillUtil.get_skill_info(hero.cfg_id, skillid)
                is_buff = True if skill_info.cast_target == SkillTargetEnum.buff else False
                tgt_hero = TeamBattleUtil.get_target_hero(hero.hero_name, friends, opponents, tgt_index, is_buff)
                tgt_pos = state_info.get_hero(tgt_hero).pos
                fwd = tgt_pos.fwd(hero.pos)
                avail_type = unaval_list[selected]
                if avail_type == 0:
                    action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, selected, None)
                else:
                    action = CmdAction(hero.hero_name, CmdActionEnum.CAST, skillid, tgt_hero, tgt_pos, fwd, None, selected, None)
                return action

    def upgrade_skills(self, state_info, hero_name):
        # 决定是否购买道具
        buy_action = EquipUtil.buy_equip(state_info, hero_name)
        if buy_action is not None:
            buy_str = StateUtil.build_command(buy_action)
            return buy_str

    def buy_equip(self, state_info, hero_name):
        # 如果有可以升级的技能，优先升级技能3
        hero = state_info.get_hero(hero_name)
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            skillid = 3 if 3 in skills else skills[0]
            update_cmd = CmdAction(hero.hero_name, CmdActionEnum.UPDATE, skillid, None, None, None, None, None, None)
            update_str = StateUtil.build_command(update_cmd)
            return update_str




