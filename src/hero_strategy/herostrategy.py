# -*- coding: utf8 -*-


# 记录玩家的关键行为，用来分析玩家的行为信息
class HeroStrategy:
    def __init__(self, hero_name, strategy_list):
        self.hero_name = hero_name
        self.strategy_list = strategy_list
