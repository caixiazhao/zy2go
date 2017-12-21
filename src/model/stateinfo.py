# -*- coding: utf8 -*-
from model.herostateinfo import HeroStateInfo
from model.attackstateinfo import AttackStateInfo
from model.cmdaction import CmdAction
from model.dmgstateinfo import DmgStateInfo
from model.hitstateinfo import HitStateInfo
from model.unitstateinfo import UnitStateInfo


# 注意有些信息不是完整的，
# units是需要跟之前的信息进行累加的
# heros信息，其中一部分属性也是需要累加的

class StateInfo:
    def get_hero_tower_dmg(self, hero_name):
        total_dmg = 0
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and int(dmg.tgt) < 27:
                tower = self.get_unit(dmg.tgt)
                total_dmg += float(dmg.dmg)/tower.maxhp
        return total_dmg

    def get_hero_dmg_skill(self, hero_name, skill_slot, tgt_id):
        total_dmg = 0
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and dmg.tgt == tgt_id and int(dmg.skillslot) == int(skill_slot):
                total_dmg += dmg.dmg
        return total_dmg

    def get_hero_total_dmg(self, hero_name, tgt_id):
        total_dmg = 0
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and dmg.tgt == tgt_id:
                total_dmg += dmg.dmg
        return total_dmg

    def if_hero_hit_unit(self, hero_name, unit_id):
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and dmg.tgt == unit_id:
                return True
        return False

    def if_hero_hit_any_unit(self, hero_name, rival_hero_name):
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and int(dmg.tgt) > 27 and dmg.tgt != rival_hero_name and int(dmg.skillslot) == 0:
                return dmg.tgt
        # return None

    def if_hero_hit_tower(self, hero_name):
        for dmg in self.dmg_infos:
            if dmg.atker == hero_name and int(dmg.tgt) < 26:
                return dmg.tgt
        return None

    def if_tower_attack_hero(self, hero_name):
        for att in self.attack_infos:
            if int(att.atker) < 26 and str(att.defer) == hero_name:
                return att

    def if_unit_attack_hero(self, unit_name, hero_name):
        for att in self.attack_infos:
            if str(att.atker) == unit_name and str(att.defer) == hero_name:
                return att
        for hit in self.hit_infos:
            if hit.atker == unit_name and hit.tgt == hero_name:
                return hit
        return None

    def get_hero_attack_info(self, hero_name):
        for att in self.attack_infos:
            if str(att.atker) == hero_name:
                return att
        return None

    def get_hero_hit_with_skill(self, hero_name, skill_id):
        hit_infos = []
        for hit in self.hit_infos:
            if hit.atker == hero_name and hit.skill == str(skill_id):
                hit_infos.append(hit)
        return hit_infos

    def get_hero_be_attacked_info(self, hero_name):
        hitted = []
        for hit in self.hit_infos:
            if hit.tgt == hero_name:
                hitted.append(hit.atker)
        return hitted

    def get_obj(self, obj_name):
        obj = self.get_hero(obj_name)
        if obj is None:
            obj = self.get_unit(obj_name)
        return obj

    def get_unit(self, unit_name):
        for unit in self.units:
            if unit.unit_name == unit_name:
                return unit
        return None

    def get_hero(self, hero_name):
        for hero in self.heros:
            if hero.hero_name == hero_name:
                return hero
        return None

    def get_hero_action(self, hero_name):
        for action in self.actions:
            if action.hero_name == hero_name:
                return action
        return None

    def get_hero_pos(self, name):
        for hero in self.heros:
            if hero.hero_name == name:
                return hero.pos
        return None

    def update_hero(self, hero_info):
        for i in range(len(self.heros)):
            hero = self.heros[i]
            if hero.hero_name == hero_info.hero_name:
                self.heros[i] == hero

    def update_unit(self, unit_info):
        for i in range(len(self.units)):
            unit = self.units(i)
            if unit.unit_name == unit_info.unit_name:
                self.units[i] == unit

    def update_attack_info(self, attack_info):
        # 首先删除掉所有同样攻击发起人的（注意，偶尔会出现一个攻击发起人发起多次攻击到情况，这里忽略)
        self.attack_infos = [att for att in self.attack_infos if att.atker != attack_info.atker]
        self.attack_infos.append(attack_info)

    def get_attack_info(self, attacker):
        for att in self.attack_infos:
            if att.atker == attacker:
                return att
        return None

    def merge(self, delta):
        # 合并英雄信息
        merged_heros = []
        for hero in delta.heros:
            found = self.get_hero(hero.hero_name)
            merged = found.merge(hero)
            merged_heros.append(merged)
        for prev in self.heros:
            found = delta.get_hero(prev.hero_name)
            if found is None:
                merged_heros.append(prev)

        # 合并单位信息
        merged_units = []
        for unit in delta.units:
            prev_unit = self.get_unit(unit.unit_name)
            if prev_unit is not None:
                # 如果hp变成了0或者状态为out，则不再添加它
                # 事实上，hp=0，之后可能有几帧的延迟才会变成out，以前者为准
                if prev_unit.hp != 0 and prev_unit.state != 'out':
                    merged = prev_unit.merge(unit)
                    merged_units.append(merged)
            else:
                # 因为死亡延迟的问题，这里我们需要判断"新的"单位是否有stat=in这个信息
                if unit.state is not None and unit.state == 'in':
                    merged_units.append(unit)
        for prev in self.units:
            cur_unit = delta.get_unit(prev.unit_name)
            if cur_unit is None:
                # 如果hp变成了0或者状态为out，则不再添加它
                # 事实上，hp=0，之后可能有几帧的延迟才会变成out，以前者为准
                if prev.hp != 0 and prev.state != 'out':
                    merged_units.append(prev)

        return StateInfo(self.battleid, delta.tick, merged_heros, merged_units,
                         delta.attack_infos, delta.hit_infos, delta.dmg_infos, delta.actions, delta.buff_infos)

    def add_action(self, action):
        for i, act in enumerate(self.actions):
            if act.hero_name == action.hero_name:
                self.actions[i] = action
                return
        self.actions.append(action)

    def add_rewards(self, hero_name, reward):
        for action in self.actions:
            if action.hero_name == hero_name:
                action.reward = reward
                # print("rewards: %s->%s, tick: %s, action: %s, skillid: %s, tgtid: %s" % (hero_name, str(reward), self.tick,
                #      action.action, action.skillid, action.tgtid))
                break

    def __init__(self, battleid, tick, heros, units, attack_infos, hit_infos, dmg_infos, actions, buff_infos=[]):
        self.battleid = battleid
        self.tick = tick
        self.heros = heros
        self.units = units
        self.attack_infos = attack_infos
        self.hit_infos = hit_infos
        self.dmg_infos = dmg_infos
        self.actions = actions
        self.buff_infos = buff_infos

    @staticmethod
    def decode_hero(obj, hero_id):
        hero_str = str(hero_id)
        if hero_str in obj:
            # 解析之后做基本的检查，判断是否具有技能信息（不够鲁棒）。
            hero_info = HeroStateInfo.decode(obj[hero_str], hero_str)
            if len(hero_info.skills) > 0:
                return hero_info
        return None

    def encode(self):
        json_map = {'wldstatic': {'ID' : self.battleid}, 'wldruntime': {'tick' : self.tick}}
        for hero in self.heros:
            json_map[hero.hero_name] = hero.encode()
        for unit in self.units:
            json_map[unit.unit_name] = unit.encode()
        json_map['attackinfos'] = [ai.encode() for ai in self.attack_infos]
        json_map['hitinfos'] = [hi.encode() for hi in self.hit_infos]
        json_map['dmginfos'] = [di.encode() for di in self.dmg_infos]
        json_map['actions'] = [ac.encode() for ac in self.actions]
        return dict((k, v) for k, v in json_map.items() if v is not None)

    @staticmethod
    def decode(obj):
        battleid = obj['wldstatic']['ID']
        tick = obj['wldruntime']['tick'] if 'tick' in obj['wldruntime'] else -1

        # 忽略了第一帧中的兵线信息

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
        # 最后一次递增需要回滚
        hero_id -= 1

        # 其它单位
        units = []
        for key in obj.keys():
            if key.isdigit():
                key1 = int(key)
                # todo: in my python3 version, there is a type error, so I use a int key1 replace key
                if key1 < 27 or key1 > hero_id:
                  units.append(UnitStateInfo.decode(obj[key], key))

        attack_infos = []
        if 'attackinfos' in obj:
            for ai in obj['attackinfos']:
                attack_infos.append(AttackStateInfo.decode(ai))

        hit_infos = []
        if 'hitinfos' in obj:
            for hi in obj['hitinfos']:
                hit_infos.append(HitStateInfo.decode(hi))

        dmg_infos = []
        if 'dmginfos' in obj:
            for di in obj['dmginfos']:
                dmg_infos.append(DmgStateInfo.decode(di))

        actions = []
        if 'actions' in obj:
            for ac in obj['actions']:
                actions.append(CmdAction.decode(ac))

        return StateInfo(battleid, tick, heros, units, attack_infos, hit_infos, dmg_infos, actions, [])
