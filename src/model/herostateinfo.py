# -*- coding: utf8 -*-
from equipstateinfo import EquipStateInfo
from fwdstateinfo import FwdStateInfo
from skillstateinfo import SkillStateInfo
from posstateinfo import PosStateInfo


class HeroStateInfo:

    @staticmethod
    def merge_skills(prev_skills, delta_skills):
        merged_skills = []
        for prev in prev_skills:
            found = HeroStateInfo.find_skill(delta_skills, prev.skill_name)
            if found is None:
                merged_skills.append(prev)
            else:
                merged = prev.merge(found)
                merged_skills.append(merged)
        return merged_skills

    @staticmethod
    def find_skill(skills, skill_name):
        for skill in skills:
            if skill_name == skill.skill_name:
                return skill
        return None

    def merge(self, delta):
        hero_name = delta.hero_name if delta.hero_name is not None else self.hero_name
        speed = delta.speed if delta.speed is not None else self.speed
        equips = delta.equips if delta.equips is not None else self.equips
        buffs = delta.buffs if delta.buffs is not None else self.buffs
        state = delta.state if delta.state is not None else self.state
        cfg_id = delta.cfg_id if delta.cfg_id is not None else self.cfg_id
        pos = delta.pos if delta.pos is not None else self.pos
        fwd = delta.fwd if delta.fwd is not None else self.fwd
        att = delta.att if delta.att is not None else self.att
        hp = delta.hp if delta.hp is not None else self.hp
        maxhp = delta.maxhp if delta.maxhp is not None else self.maxhp
        mp = delta.mp if delta.mp is not None else self.mp
        maxmp = delta.maxmp if delta.maxmp is not None else self.maxmp
        gold = delta.gold if delta.gold is not None else self.gold
        hprec = delta.hprec if delta.hprec is not None else self.hprec
        attspeed = delta.attspeed if delta.attspeed is not None else self.attspeed
        mag = delta.mag if delta.mag is not None else self.mag
        attpen = delta.attpen if delta.attpen is not None else self.attpen
        magpen = delta.magpen if delta.magpen is not None else self.magpen
        attpenrate = delta.attpenrate if delta.attpenrate is not None else self.attpenrate
        magpenrate = delta.magpenrate if delta.magpenrate is not None else self.magpenrate
        movelock = delta.movelock if delta.movelock is not None else self.movelock

        vis1 = delta.vis1 if delta.vis1 is not None else self.vis1
        vis2 = delta.vis2 if delta.vis2 is not None else self.vis2
        vis3 = delta.vis3 if delta.vis3 is not None else self.vis3

        # team 的合并根据之前的结果来，不由delta决定
        team = self.team if self.team is not None else delta.team

        merged_skills = HeroStateInfo.merge_skills(self.skills, delta.skills)
        return HeroStateInfo(hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips,
                             buffs, merged_skills, vis1, vis2, vis3, attspeed, mag, attpen, magpen, attpenrate, magpenrate, movelock, team)

    def __init__(self, hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips, buffs,
                 skills, vis1, vis2, vis3, attspeed, mag, attpen, magpen, attpenrate, magpenrate, movelock, team):
        self.hero_name = hero_name
        self.speed = speed
        self.state = state
        self.cfg_id = cfg_id
        self.pos = pos
        self.fwd = fwd
        self.att = att
        self.hp = hp
        self.maxhp = maxhp
        self.mp = mp
        self.maxmp = maxmp
        self.gold = gold
        self.hprec = hprec
        self.equips = equips
        self.buffs = buffs
        self.skills = skills
        self.vis1 = vis1
        self.vis2 = vis2
        self.vis3 = vis3
        self.attspeed = attspeed    # 攻击强度，0表示默认值，1000表示翻倍
        self.mag = mag      # 法强
        self.attpen = attpen    # 攻击穿透，护甲-攻击穿透
        self.magpen = magpen    # 法术穿透
        self.attpenrate = attpenrate    # 攻击穿透比例，护甲x(1-攻击穿透比例）
        self.magpenrate = magpenrate
        self.movelock = movelock    # 是否可以移动
        self.team = team

    def is_enemy_visible(self):
        if self.team == 0:
            return self.vis1
        else:
            return self.vis2

    def encode(self):
        json_map = {'state': self.state, 'cfgID': self.cfg_id, 'pos': self.pos.encode(), 'fwd': self.fwd.encode(),
                    'hp': self.hp, 'maxhp': self.maxhp, 'maxmp': self.maxmp, 'mp': self.mp, 'speed': self.speed,
                    'att': self.att, 'gold': self.gold, 'Hprec': self.hprec, 'vis1': self.vis1, 'vis2': self.vis2,
                    'vis3': self.vis3, 'attspeed': self.attspeed, 'mag': self.mag, 'attpen': self.attpen, 'magpen': self.magpen,
                    'attpenrate': self.attpenrate, 'magpenrate': self.magpenrate, 'movelock': self.movelock, 'buff': self.buffs,
                    }
        for equip in self.equips:
            json_map[equip.name] = equip.encode()
        for skill in self.skills:
            json_map[skill.skill_name] = skill.encode()
        return dict((k, v) for k, v in json_map.items() if v is not None)

    @staticmethod
    def decode_add_skill(obj, skill_id):
        if skill_id in obj:
            return SkillStateInfo.decode(obj[skill_id], skill_id)
        return None

    @staticmethod
    def decode(obj, hero_name):
        hero_name = hero_name
        state = obj['state'] if 'state' in obj else None
        cfg_id = obj['cfgID'] if 'cfgID' in obj else None
        pos = PosStateInfo.decode(obj['pos']) if 'pos' in obj else None
        fwd = FwdStateInfo.decode(obj['fwd']) if 'fwd' in obj else None
        hp = obj['hp'] if 'hp' in obj else None
        maxhp = obj['maxhp'] if 'maxhp' in obj else None
        maxmp = obj['maxmp'] if 'maxmp' in obj else None

        #TODO 如果没有信息，mp默认等于0？
        mp = obj['mp'] if 'mp' in obj else None
        speed = obj['speed'] if 'speed' in obj else None
        att = obj['att'] if 'att' in obj else None
        gold = obj['gold'] if 'gold' in obj else None
        hprec = obj['Hprec'] if 'Hprec' in obj else None

        # 是否可见信息(下路阵营，上路阵营，中立生物是否可见）
        vis1 = obj['vis1'] if 'vis1' in obj else None
        vis2 = obj['vis2'] if 'vis2' in obj else None
        vis3 = obj['vis3'] if 'vis3' in obj else None

        # 更新字段
        attspeed = obj['attspeed'] if 'attspeed' in obj else None
        mag = obj['mag'] if 'mag' in obj else None
        attpen = obj['attpen'] if 'attpen' in obj else None
        magpen = obj['magpen'] if 'magpen' in obj else None
        attpenrate = obj['attpenrate'] if 'attpenrate' in obj else None
        magpenrate = obj['magpenrate'] if 'magpenrate' in obj else None
        movelock = obj['movelock'] if 'movelock' in obj else None

        equips = []
        if 'equip0' in obj:
            equips.append(EquipStateInfo.decode(obj['equip0'], 'equip0'))
        if 'equip1' in obj:
            equips.append(EquipStateInfo.decode(obj['equip1'], 'equip1'))
        if 'equip2' in obj:
            equips.append(EquipStateInfo.decode(obj['equip2'], 'equip2'))
        if 'equip3' in obj:
            equips.append(EquipStateInfo.decode(obj['equip3'], 'equip3'))
        if 'equip4' in obj:
            equips.append(EquipStateInfo.decode(obj['equip4'], 'equip4'))
        if 'equip5' in obj:
            equips.append(EquipStateInfo.decode(obj['equip5'], 'equip5'))
        if 'equip6' in obj:
            equips.append(EquipStateInfo.decode(obj['equip6'], 'equip6'))
        if 'equip7' in obj:
            equips.append(EquipStateInfo.decode(obj['equip7'], 'equip7'))

        buffs = obj['buff'] if 'buff' in obj else []

        skills = []
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill0')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill1')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill2')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill3')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill4')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill5')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill6')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill7')
        if skill_info is not None:
            skills.append(skill_info)
        skill_info = HeroStateInfo.decode_add_skill(obj, 'Skill8')
        if skill_info is not None:
            skills.append(skill_info)

        # 根据其实位置来决定英雄阵营，注意，这里的判断只有在第一帧时候是合理的，后续的其实应该根据merge来判断
        # 上路是team0，下路team1
        team = None if pos is None else 0 if pos.x < 0 else 1

        return HeroStateInfo(hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips,
                             buffs, skills, vis1, vis2, vis3, attspeed, mag, attpen, magpen, attpenrate, magpenrate, movelock, team)
