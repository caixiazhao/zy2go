#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 给模型添加一些固定套路，在训练中随机选择，希望模型可以学习到这些正确的处理问题方式
# 首先是特殊技能的正确使用方式
# 对模型的影响分两个方面：
#   在选择模型行动时候，可以屏蔽错误的选择
#       大招周围没有人
#   在出现好的时机时候，选择更好的选择
#       敌我血量悬殊，
import math

from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from train.cmdactionenum import CmdActionEnum
from train.linemodel import LineModel
from util.replayer import Replayer
from util.stateutil import StateUtil
from random import randint


class TeamBattlePolicy:

    ENEMY_BATTLE_RANGE = 3

    # 技能选择时候的限制条件
    @staticmethod
    def check_skill_condition(skill_info, state_info, hero_info, tgt_hero, friends, opponents, debug=False):
        # 针对对自身附近范围内进行的伤害，检测是否有敌方英雄
        # 目前有查尔斯3技能，洛克2技能
        if (skill_info.hero_id == 101 and skill_info.skill_id == 3) or \
           (skill_info.hero_id == 104 and skill_info.skill_id == 2):
                heroes_in_range = TeamBattlePolicy.find_heros_in_range(state_info, hero_info.pos, opponents, skill_info.cast_distance)
                if len(heroes_in_range) == 0:
                    if debug: print("battle_id", state_info.battleid, "根据规则过滤技能", "hero_id", skill_info.hero_id, "skill_id", skill_info.skill_id)
                else:
                    if debug: print("battle_id", state_info.battleid, "可以释放技能", "hero_id", skill_info.hero_id, "skill_id",
                          skill_info.skill_id, "影响敌人", ",".join(heroes_in_range))
                return len(heroes_in_range) > 0

        # 针对对自身附近己方英雄的提升，检测附近是否有己方英雄
        # 目前有蕾娜斯3技能, 需要确定周围有人需要加血
        if skill_info.hero_id == 106 and skill_info.skill_id == 3:
            heroes_in_range = TeamBattlePolicy.find_heros_in_range(state_info, hero_info.pos, friends, skill_info.cast_distance)
            # 添加自身作为考虑
            heroes_in_range.append(hero_info.hero_name)
            heroes_need_heal = TeamBattlePolicy.get_hero_below_hp_ratio(state_info, heroes_in_range, 0.7)
            if len(heroes_in_range) == 0:
                if debug: print("battle_id", state_info.battleid, "根据规则过滤技能", "hero_id", skill_info.hero_id, "skill_id", skill_info.skill_id)
            return len(heroes_need_heal) > 0

        # 针对自身的buff技能，确定战斗范围内有敌方英雄
        # 目前有德古拉3技能，盖娅3技能
        if (skill_info.hero_id == 102 and skill_info.skill_id == 3) or \
           (skill_info.hero_id == 103 and skill_info.skill_id == 3):
            heroes_in_range = TeamBattlePolicy.find_heros_in_range(state_info, hero_info.pos, opponents, TeamBattlePolicy.ENEMY_BATTLE_RANGE)
            if len(heroes_in_range) == 0:
                if debug: print("battle_id", state_info.battleid, "根据规则过滤技能", "hero_id", skill_info.hero_id, "skill_id", skill_info.skill_id)
            return len(heroes_in_range) > 0
        return True

    @staticmethod
    def find_heros_in_range(state_info, pos1, heroes, range):
        heroes_in_range = []
        for hero in heroes:
            hero_info = state_info.get_hero(hero)
            dis = TeamBattlePolicy.in_skill_range(pos1, hero_info.pos, range)
            if dis != -1:
                heroes_in_range.append(hero)
        return heroes_in_range

    @staticmethod
    def in_skill_range(pos1, pos2, range):
        dis = StateUtil.cal_distance(pos1, pos2)
        if dis < range:
            return dis
        return -1

    @staticmethod
    def get_hero_below_hp_ratio(state_info, heroes, ratio):
        result_heroes = []
        for hero in heroes:
            hero_info = state_info.get_hero(hero)
            if hero_info.hp / float(hero_info.maxhp) <= ratio:
                result_heroes.append(hero)
        return result_heroes