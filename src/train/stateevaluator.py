# -*- coding: utf8 -*-

# 给每个游戏状态进行打分，评估英雄处于优势还是劣势
# 评估的方式可以有很多种，比如使用神经网络来评估
# 这里我们先使用最简单的方式，考察双方英雄的血量变化
# 同时给超低血量一个危险权重
# 给死亡一个最大的负分
class StateEvaluator:
    @staticmethod
    def score(state_info, prev_state, team_a, team_b):
        for hero in team_a:
            cur_hero_info = state_info.get_hero(hero)
            prev_hero_info = prev_state.get_hero(hero)


    @staticmethod
    def score_hp_change(cur_hero_info, prev_hero_info):
        # 考察血量变化
        # 同时给超低血量一个危险权重
        # 给死亡一个最大的负分
        if cur_hero_info.hp <= 0 and prev_hero_info.hp > 0:
            return -5
        else:
            prev_score = 1 - prev_hero_info.hp + max(0, 0.6 - prev_hero_info.hp) + 2 * max(0, 0.3 - prev_hero_info.hp)
            return prev_score