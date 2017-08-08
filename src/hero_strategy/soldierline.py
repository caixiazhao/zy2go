# -*- coding: utf8 -*-


# 记录玩家的关键行为，用来分析玩家的行为信息
class SoldierLine:
    def __init__(self, team_id, line_index, pos, units):
        self.team_id = team_id
        self.line_index = line_index
        self.pos = pos
        self.units = units
