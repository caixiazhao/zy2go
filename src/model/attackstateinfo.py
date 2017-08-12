# -*- coding: utf8 -*-
from model.posstateinfo import PosStateInfo

# 攻击信息defer可以为0，表示没有目标，也可以搭配tgtpos，比如闪现或者指定方向施法，也可能是被动技能
class AttackStateInfo(object):
    def __init__(self, atker, defer, tgtpos, skill):
        self.atker = atker
        self.defer = defer
        self.tgtpos = tgtpos
        self.skill = skill

    @staticmethod
    def decode(obj):
        atker = obj['atker']
        defer = obj['defer'] if 'defer' in obj else None
        tgtpos = PosStateInfo.decode(obj['tgtpos']) if 'tgtpos' in obj else None
        skill = obj['skill']
        return AttackStateInfo(atker, defer, tgtpos, skill)

    def encode(self):
        json_map = {'atker': self.atker, 'defer': self.defer, 'tgtpos':self.tgtpos, 'skill': self.skill}
        return dict((k, v) for k, v in json_map.items() if v is not None)
