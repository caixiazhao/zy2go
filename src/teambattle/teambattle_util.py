#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
