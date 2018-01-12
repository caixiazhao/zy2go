#!/usr/bin/env python
# -*- coding: utf-8 -*-


# 团战输入信息
# 需要扩大检索范围，但是针对不可攻击的英雄，需要更多的标注
# 考虑到配合问题，将其他英雄的攻击信息纳入到输入中
# 英雄信息，技能信息，攻击信息
#TODO 支持在塔附近开团
from util.stateutil import StateUtil


class TeamBattleInput:

    @staticmethod
    def gen_input(state_info, hero_name):
        return
    #     # 得到周围范围内友方英雄信息
    #
    #     # 得到周围范围内敌方英雄信息
    #     nearest_towers = StateUtil.get_nearby_enemy_heros(self.stateInformation, my_he
    #                                                        self.NEAR_TOWER_RADIUS)
    #     nearest_towers_rival = [t for t in nearest_towers if t.team != my_hero_info.team]
    #     nearest_towers_team = [t for t in nearest_towers if t.team == my_hero_info.team]
    #
    #     # 添加英雄状态
    #
    #     # 添加技能状态
    #
    # @staticmethod
    # def add_hero_action_info():
