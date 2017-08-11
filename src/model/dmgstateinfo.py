# -*- coding: utf8 -*-
from model.posstateinfo import PosStateInfo

# 造成的伤害信息，注意这里记录的技能是技能槽位置，0表示普通攻击
# 注：一次返回中有可能有多段攻击伤害，都是由同一个技能触发的
class DmgStateInfo(object):
    def __init__(self, atker, tgt, skillslot, dmg):
        self.atker = atker
        self.tgt = tgt
        self.skillslot = skillslot
        self.dmg = dmg

    @staticmethod
    def decode(obj):
        atker = obj['atker']
        tgt = obj['tgt'] if 'tgt' in obj else None
        skillslot = obj['skillslot'] if 'skillslot' in obj else None
        dmg = obj['dmg']
        return DmgStateInfo(atker, tgt, skillslot, dmg)

    def encode(self):
        json_map = {'atker': self.atker, 'tgt': self.tgt, 'skillslot': self.skillslot, 'dmg': self.dmg}
        return json_map