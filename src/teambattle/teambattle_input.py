#!/usr/bin/env python
# -*- coding: utf-8 -*-


# 团战输入信息
# 需要扩大检索范围，但是针对不可攻击的英雄，需要更多的标注
# 考虑到配合问题，将其他英雄的攻击信息纳入到输入中
# 英雄信息，技能信息，攻击信息
#TODO 支持在塔附近开团
from model.skillcfginfo import SkillTargetEnum
from teambattle.teambattle_util import TeamBattleUtil
from train.cmdactionenum import CmdActionEnum
from train.line_input_lite import Line_Input_Lite
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
import numpy as np


class TeamBattleInput:
    NORMARLIZE = 10000
    HERO_LIST = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
    TEAM_A = ['27', '28', '29', '30', '31']
    TEAM_B = ['32', '33', '34', '35', '36']

    # 英雄信息向量大小20+3*23
    # query_hero 表示这是哪个英雄进行计算发起的请求
    @staticmethod
    def gen_input_hero(hero, query_hero, revert=False):
        if hero is None or hero.state == 'out' or hero.hp <= 0:
            return list(np.zeros(20 + 3 * 23))

        # 添加英雄基础信息 11个
        hero_input = [
            TeamBattleInput.normalize_value(hero.pos.x - query_hero.pos.x if not revert else -(hero.pos.x - query_hero.pos.x)),
            TeamBattleInput.normalize_value(hero.pos.z - query_hero.pos.z if not revert else -(hero.pos.z - query_hero.pos.z)),
            TeamBattleInput.normalize_value(hero.speed),
            # # todo: 2 是普攻手长，现只适用于1,2号英雄，其他英雄可能手长不同
            # 0.2,
            TeamBattleInput.normalize_value(hero.hp),
            hero.hp / float(hero.maxhp),
            TeamBattleInput.normalize_value(hero.hprec),
            TeamBattleInput.normalize_value(hero.mp),
            TeamBattleInput.normalize_value(hero.mag),
            TeamBattleInput.normalize_value(hero.magpen),
            TeamBattleInput.normalize_value(hero.magpenrate),
            hero.team if not revert else 1 - hero.team]

        # 添加物理攻击信息，预留5个攻击对象位，9个
        hero_input.append(TeamBattleInput.normalize_value(hero.att)),
        hero_input.append(TeamBattleInput.normalize_value(hero.attspeed)),
        hero_input.append(TeamBattleInput.normalize_value(hero.attpen)),
        hero_input.append(TeamBattleInput.normalize_value(hero.attpenrate)),
        hero_input.append(0)
        hero_input.append(0)
        hero_input.append(0)
        hero_input.append(0)
        hero_input.append(0)

        # 添加技能信息
        skill_info1 = SkillUtil.get_skill_info(hero.cfg_id, 1)
        skill_info2 = SkillUtil.get_skill_info(hero.cfg_id, 2)
        skill_info3 = SkillUtil.get_skill_info(hero.cfg_id, 3)
        skill_input1 = TeamBattleInput.gen_input_skill(skill_info1, hero.skills[1])
        skill_input2 = TeamBattleInput.gen_input_skill(skill_info2, hero.skills[2])
        skill_input3 = TeamBattleInput.gen_input_skill(skill_info3, hero.skills[3])

        hero_input = hero_input + skill_input1 + skill_input2 + skill_input3
        return hero_input

    @staticmethod
    def normalize_value(value):
        return float(value)/TeamBattleInput.NORMARLIZE

    @staticmethod
    def normalize_value_static(value):
        return float(value)/TeamBattleInput.NORMARLIZE

    @staticmethod
    def normalize_skill_value(value):
        return float(value)/10

    # 技能信息向量大小=18+5
    @staticmethod
    def gen_input_skill(skill_cfg_info, skill):
        skill_input = [
            TeamBattleInput.normalize_skill_value(skill_cfg_info.instant_dmg),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.sustained_dmg),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.restore),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.defend_bonus),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.attack_bonus),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.restore_bonus),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.move_bonus),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.defend_weaken),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.attack_weaken),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.move_weaken),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.stun),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.blink),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.dmg_range),
            TeamBattleInput.normalize_skill_value(skill_cfg_info.cast_distance),
            # 是否可以给自己和敌人施法，是否可以给队友施法
            1 if skill_cfg_info.cast_target == SkillTargetEnum.self or skill_cfg_info.cast_target == SkillTargetEnum.both or skill_cfg_info.cast_target == SkillTargetEnum.buff else 0,
            1 if skill_cfg_info.cast_target == SkillTargetEnum.rival or skill_cfg_info.cast_target == SkillTargetEnum.both else 0,
            1 if skill_cfg_info.cast_target == SkillTargetEnum.buff or skill_cfg_info.cast_target == SkillTargetEnum.buff else 0]

        skill_canuse = int(skill.canuse) if skill.canuse is not None else 0
        skill_input.append(skill_canuse)

        # 施法对象，预留5个空位，敌人或者队友
        # 这里的目标，统一为，敌人，队友都是27-31这种顺序排序
        # TODO 需要决定这里到底留几个槽，5个还是10个
        skill_input.append(0)
        skill_input.append(0)
        skill_input.append(0)
        skill_input.append(0)
        skill_input.append(0)
        return skill_input

    @staticmethod
    def gen_input(state_info, hero_name):
        input_data = []

        # 添加英雄状态， 英雄排序为ID大小排序，
        # 目前，即使距离很远的英雄，也提供信息，只是会在结果过滤时候去掉选择他们的行为
        hero_info = state_info.get_hero(hero_name)
        input_data += TeamBattleInput.gen_input_hero(hero_info, hero_info)
        friends, opponents = TeamBattleUtil.get_friend_opponent_heros(TeamBattleInput.HERO_LIST, hero_name)
        for friend_name in friends:
            friend_info = state_info.get_hero(friend_name)
            input_data += TeamBattleInput.gen_input_hero(friend_info, hero_info)
        for opponent_name in opponents:
            opponent_info = state_info.get_hero(opponent_name)
            input_data += TeamBattleInput.gen_input_hero(opponent_info, hero_info)
        return input_data

    # 添加其他英雄的行为到决策中
    # 这里只添加自己方的行为
    # 所以一个思路是在输入中对每一个英雄后面添加一个行为串，记录上一次的行为，缺点是太过稀疏
    # 所以缩减到英雄后面添加几个信息，技能1-4攻击对方英雄1-5或者治疗己方英雄1-5
    @staticmethod
    def add_other_hero_action(input_data, hero_info, action_cmd, debug=False):
        # 如果是自己，则忽略
        if hero_info.hero_name == action_cmd.hero_name:
            return input_data

        # 如果不是攻击类行为，忽略
        if action_cmd.action != CmdActionEnum.ATTACK and action_cmd.action != CmdActionEnum.CAST:
            return input_data

        # 如果不是己方的动作，忽略
        friends, opponents = TeamBattleUtil.get_friend_opponent_heros(TeamBattleInput.HERO_LIST, hero_info.hero_name)
        if action_cmd.hero_name != hero_info.hero_name and action_cmd.hero_name not in friends:
            return input_data

        # 更新输入数据
        # 首先找到目标英雄ID，然后找到使用的技能ID
        hero_index = friends.index(action_cmd.hero_name) + 1
        tgt_hero_index = TeamBattleInput.TEAM_A.index(action_cmd.tgtid) if action_cmd.tgtid in TeamBattleInput.TEAM_A \
            else TeamBattleInput.TEAM_B.index(action_cmd.tgtid)
        change_index = hero_index * 89 + 15 + tgt_hero_index if action_cmd.action == CmdActionEnum.ATTACK \
            else hero_index * 89 + 20 + (int(action_cmd.skillid) - 1) * 23 + 18 + tgt_hero_index

        prev_value = input_data[change_index]
        if prev_value != 0:
            if debug: print("add_other_hero_action", "must be something wrong", "prev_value not zero")
        input_data[change_index] = 1
        debug_action_str = StateUtil.build_command(action_cmd)
        if debug: print("add_other_hero_action", "add_hero_info", hero_info.hero_name, "hero_index", hero_index, "tgt_hero_index", tgt_hero_index,
              "action_cmd.action", action_cmd.action, "action_cmd_skill", action_cmd.skillid, "change_index", change_index, "cmd", debug_action_str)
        return input_data





