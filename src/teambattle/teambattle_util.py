#!/usr/bin/env python
# -*- coding: utf-8 -*-
from model.posstateinfo import PosStateInfo


class TeamBattleUtil:
    @staticmethod
    def get_friend_opponent_heros(team_battle_heros, hero):
        if int(hero) <= 31:
            friends = [hero for hero in team_battle_heros if int(hero) <= 31]
            friends.remove(hero)
            opponents = [hero for hero in team_battle_heros if int(hero) > 31]
            return friends, opponents
        elif int(hero) > 31:
            friends = [hero for hero in team_battle_heros if int(hero) > 31]
            friends.remove(hero)
            opponents = [hero for hero in team_battle_heros if int(hero) <= 31]
            return friends, opponents

    @staticmethod
    # 找到目标英雄，因为范围内的敌我英雄可能不是一个全集
    def get_target_hero(hero, friends, opponents, target_index, is_buff=False):
        if not is_buff:
            start_hero_id = 27 if int(hero) > 31 else 32
            target_hero_id = start_hero_id + target_index
            if str(target_hero_id) in opponents:
                return str(target_hero_id)
            else:
                return None
        else:
            start_hero_id = 27 if int(hero) <= 31 else 32
            target_hero_id = start_hero_id + target_index
            if str(target_hero_id) in friends:
                return str(target_hero_id)
            else:
                return None

    @staticmethod
    def get_hero_team(hero_name):
        if int(hero_name) > 31:
            return 0
        return 1


    @staticmethod
    # 返回队伍名，不符合则返回-1
    def all_in_one_team(hero_names):
        if len(hero_names) <= 1:
            return -1
        test_heroes = list(hero_names)
        sorted(test_heroes)
        if TeamBattleUtil.get_hero_team(test_heroes[0]) == TeamBattleUtil.get_hero_team(test_heroes[-1]):
            return TeamBattleUtil.get_hero_team(test_heroes[0])
        return -1

    @staticmethod
    def play_move(hero_info, fwd, time_second=0.5):
       return PosStateInfo(hero_info.pos.x + time_second * fwd.x * hero_info.speed / 1000,
                           hero_info.pos.y + time_second * fwd.y * hero_info.speed / 1000,
                           hero_info.pos.z + time_second * fwd.z * hero_info.speed / 1000)

