# -*- coding: utf8 -*-
from herostateinfo import HeroStateInfo
from model.attackstateinfo import AttackStateInfo
from model.hitstateinfo import HitStateInfo
from unitstateinfo import UnitStateInfo


# 注意有些信息不是完整的，
# units是需要跟之前的信息进行累加的
# heros信息，其中一部分属性也是需要累加的
class StateInfo:
    def get_hero_attack_info(self, hero_name):
        for att in self.attack_infos:
            if att.atker == hero_name:
                return att
        return None

    def get_hero_be_attacked_info(self, hero_name):
        hitted = []
        for hit in self.hit_infos:
            if hit.tgt == hero_name:
                hitted.append(hit.atker)
        return hitted

    def get_unit(self, unit_name):
        for unit in self.units:
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_hero(self, hero_name):
        for hero in self.heros:
            if hero.name == hero_name:
                return hero
        return None

    def merge(self, delta):
        # 合并英雄信息
        merged_heros = []
        for hero in delta.heros:
            found = False
            for prev_hero in self.heros:
                if hero.hero_name == prev_hero.hero_name:
                    merged = prev_hero.merge(hero)
                    merged_heros.append(merged)
                    found = True
            if not found:
                merged_heros.append(hero)
                #会在这返回，很奇怪
        for prev in self.heroes:
            found = False
            for merged in merged_heros:
                if prev.hero_name == merged.hero_name:
                    found = True
            if not found:
                merged_heros.append(prev)

        # 合并单位信息
        merged_units = []
        for unit in delta.units:

                found = False
                for prev_unit in self.units:
                    if unit.unit_name == prev_unit.unit_name:
                        merged = prev_unit.merge(unit)
                        merged_units.append(merged)
                        self.units
                        found = True
                if not found:
                    merged_units.append(unit)
        for prev in self.units:
            # 如果状态为out则表示这个单位已经被销毁，不再加入列表中
            if prev.state != 'out':
                found = False
                for merged in merged_units:
                    if prev.unit_name == merged.unit_name:
                        found = True
                if not found:
                    merged_units.append(prev)


        return StateInfo(self.battleid, delta.tick, merged_heros, merged_units)

    #def get_hero_pos(self,hero_id):


    def __init__(self, battleid, tick, heros, units, attack_infos, hit_infos):
        self.battleid = battleid
        self.tick = tick
        self.heros = heros
        self.units = units
        self.attack_infos = attack_infos
        self.hit_infos = hit_infos

    @staticmethod
    def decode_hero(obj, hero_id):
        hero_str = str(hero_id)
        if hero_str in obj:
            # 解析之后做基本的检查，判断是否具有技能信息（不够鲁棒）。
            hero_info = HeroStateInfo.decode(obj[hero_str], hero_str)
            if len(hero_info.skills) > 0:
                return hero_info
        return None

    @staticmethod
    def decode(obj):
        battleid = obj['wldstatic']['ID']
        tick = obj['wldruntime']['tick']

        # 貌似从27-36是英雄
        heros = []
        hero_id = 27
        while True:
            hero_info = StateInfo.decode_hero(obj, hero_id)
            if hero_info is not None:
                heros.append(hero_info)
                hero_id += 1
            else:
                break

        # 其它单位
        units = []
        for key in obj.keys():
            if key.isdigit():
                if key < 27 or key > hero_id:
                  units.append(UnitStateInfo.decode(obj[key], key))

        attack_infos = []
        if 'attackinfos' in obj:
            for ai in obj['attackinfos']:
                attack_infos.append(AttackStateInfo.decode(ai))

        hit_infos = []
        if 'hitinfos' in obj:
            for hi in obj['hitinfos']:
                hit_infos.append(HitStateInfo.decode(hi))

        return StateInfo(battleid, tick, heros, units, attack_infos, hit_infos)
