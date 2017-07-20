# -*- coding: utf8 -*-
from herostateinfo import HeroStateInfo
from model.attackstateinfo import AttackStateInfo
from model.hitstateinfo import HitStateInfo
from unitstateinfo import UnitStateInfo

# 注意有些信息不是完整的，
# units是需要跟之前的信息进行累加的
# heros信息，其中一部分属性也是需要累加的
class StateInfo:
    def __init__(self, battleid, tick, heros, units):
        self.battleid = battleid
        self.tick = tick
        self.heros = heros
        self.units = units

    @staticmethod
    def decode(obj):
        battleid = obj['wldstatic']['ID']
        tick = obj['wldruntime']['tick']

        # 貌似从27-36是英雄
        heros = []
        heros.append(HeroStateInfo.decode(obj['27'], '27'))
        heros.append(HeroStateInfo.decode(obj['28'], '28'))
        heros.append(HeroStateInfo.decode(obj['29'], '29'))
        heros.append(HeroStateInfo.decode(obj['30'], '30'))
        heros.append(HeroStateInfo.decode(obj['31'], '31'))
        heros.append(HeroStateInfo.decode(obj['32'], '32'))
        heros.append(HeroStateInfo.decode(obj['33'], '33'))
        heros.append(HeroStateInfo.decode(obj['34'], '34'))
        heros.append(HeroStateInfo.decode(obj['35'], '35'))
        heros.append(HeroStateInfo.decode(obj['36'], '36'))

        # 其它单位
        units = []
        for key in obj.keys():
            if key.isdigit():
                if key < 27 or key > 36:
                  units.append(UnitStateInfo.decode(obj[key], key))
            else:
                print key

        attack_infos = []
        if 'attackinfos' in obj:
            for ai in obj['attackinfos']:
                attack_infos.append(AttackStateInfo.decode(ai))

        hit_infos = []
        if 'hitinfos' in obj:
            for hi in obj['hitinfos']:
                hit_infos.append(HitStateInfo.decode(hi))

        return StateInfo(battleid, tick, heros, units)
