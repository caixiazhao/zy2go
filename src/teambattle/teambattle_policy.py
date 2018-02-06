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
from model.skillcfginfo import SkillTargetEnum
from teambattle.teambattle_util import TeamBattleUtil
from train.cmdactionenum import CmdActionEnum
from train.linemodel import LineModel
from util.replayer import Replayer
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from random import randint


class TeamBattlePolicy:

    ENEMY_BATTLE_RANGE = 3
    ENEMY_BATTLE_RANGE_LARGE = 7

    # 得到推荐的英雄行动ID
    @staticmethod
    def gen_attack_cast_action_indic(hero_info, enemy_info, friends, opponents):
        recommmend_actions = []
        tgt_idx = opponents.index(enemy_info.hero_name)

        # 添加物理攻击
        action_idx = TeamBattleUtil.get_action_index(tgt_idx, 0)
        recommmend_actions.append(action_idx)

        # 添加技能攻击
        for skill_id in range(1, 4):
            skill_info = SkillUtil.get_skill_info(hero_info.cfg_id, skill_id)
            if skill_info.cast_target == SkillTargetEnum.rival:
                action_idx = TeamBattleUtil.get_action_index(tgt_idx, skill_id)
                recommmend_actions.append(action_idx)
            elif skill_info.cast_target == SkillTargetEnum.self:
                # 如果技能对象是自己，添加自己作为目标，
                # 注意，这里的合理性会由技能检查条件来覆盖
                action_idx = TeamBattleUtil.get_action_index(0, skill_id)
                recommmend_actions.append(action_idx)
        return recommmend_actions

    # 在一些特定情况下，命令英雄作出不同的选择
    @staticmethod
    def select_action_by_strategy(state_info, hero_info, friends, opponents, debug=True):
        recommend_action_set = set()

        # 在周围有残血英雄的情况下，优先攻击对方
        # 在团战前中期，只有身边小范围内有敌对英雄时候会触发这个条件，在中后期，扩大搜索残血敌人的范围
        if TeamBattlePolicy.get_hp_ratio(hero_info) > 0.6:
            search_range = TeamBattlePolicy.ENEMY_BATTLE_RANGE_LARGE if len(friends) >= len(opponents) and len(opponents) <= 2 else TeamBattlePolicy.ENEMY_BATTLE_RANGE
            enemies_in_low_hp = TeamBattlePolicy.get_enemies_low_hp(state_info, hero_info, opponents, search_range, 0.3)
            #TODO 理想情况下，这时候应该评估自己的存活率，然后再行动，甚至血量都不需要这么悬殊
            for enemy_info in enemies_in_low_hp:
                rcmd_actions = TeamBattlePolicy.gen_attack_cast_action_indic(hero_info, enemy_info, friends, opponents)
                if debug: print("battle_id", state_info.battleid, "追击残血英雄", hero_info.hero_name, "推荐行为",
                                ','.join(str(act) for act in rcmd_actions))
                recommend_action_set = recommend_action_set.union(rcmd_actions)

        # 在残血的情况下，优先移动
        if TeamBattlePolicy.get_hp_ratio(hero_info) < 0.3:
            mov_idx = list(range(8))
            recommend_action_set.union(mov_idx)
            if debug: print("battle_id", state_info.battleid, "优先移动", hero_info.hero_name)
        return recommend_action_set

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

    @staticmethod
    def get_hp_ratio(hero_info):
        return hero_info.hp / float(hero_info.maxhp)

    @staticmethod
    def get_enemies_low_hp(state_info, hero_info, opponents, range, hp_ratio):
        enemies_in_range = TeamBattlePolicy.find_heros_in_range(state_info, hero_info.pos, opponents, range)
        enemies_in_low_hp = []
        for enemy_name in enemies_in_range:
            enemy_info = state_info.get_hero(enemy_name)
            if TeamBattlePolicy.get_hp_ratio(enemy_info) <= hp_ratio:
                enemies_in_low_hp.append(enemy_info)
        return enemies_in_low_hp
