# -*- coding: utf8 -*-


# 记录玩家的关键行为，用来分析玩家的行为信息
class StrategyAction(object):
    def __init__(self, hero_name, tick, pos, action, target_info):
        self.hero_name = hero_name
        self.tick = tick
        self.pos = pos
        self.action = action
        self.target_info = target_info  # 表示目标信息，可以是英雄，塔，野怪

