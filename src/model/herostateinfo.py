# -*- coding: utf8 -*-
from equipstateinfo import EquipStateInfo
from fwdstateinfo import FwdStateInfo
from skillstateinfo import SkillStateInfo
from posstateinfo import PosStateInfo


class HeroStateInfo:
    def merge_skills(self, skills):
        merged_skills = []
        for skill in skills:
            found = False
            for prev_skill in self.skills:
                if prev_skill.skill_name == skill.skill_name:
                    merged = prev_skill.merge(skill)
                    merged_skills.append(merged)
                    found = True
            if not found:
                merged_skills.append(skill)
        return merged_skills

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

        #TODO 可见信息不需要合并? 需要确认到底哪些信息需要合并
        vis1 = delta.vis1
        vis2 = delta.vis2
        vis3 = delta.vis3

        skills = self.merge_skills(delta.skills)
        return HeroStateInfo(hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips, buffs, skills, vis1, vis2, vis3)

    def __init__(self, hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips, buffs, skills, vis1, vis2, vis3):
        self.hero_name = hero_name
        self.speed = speed
        self.equips = equips
        self.buffs = buffs
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
        self.skills = skills
        self.vis1 = vis1
        self.vis2 = vis2
        self.vis3 = vis3

    @staticmethod
    def decode_add_skill(obj, skill_id, skills):
        if skill_id in obj:
            skills.append(SkillStateInfo.decode(obj[skill_id], skill_id))
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
        maxmp = obj['maxmp'] if 'maxmp' in obj else 0

        #TODO 如果没有信息，mp默认等于0？
        mp = obj['mp'] if 'mp' in obj else 0
        speed = obj['speed'] if 'speed' in obj else None
        att = obj['att'] if 'att' in obj else None
        gold = obj['gold'] if 'gold' in obj else None
        hprec = obj['Hprec'] if 'Hprec' in obj else None

        # 是否可见信息
        vis1 = obj['vis1'] if 'vis1' in obj else None
        vis2 = obj['vis2'] if 'vis2' in obj else None
        vis3 = obj['vis3'] if 'vis3' in obj else None

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
        HeroStateInfo.decode_add_skill(obj, 'Skill0', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill1', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill2', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill3', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill4', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill5', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill6', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill7', skills)
        HeroStateInfo.decode_add_skill(obj, 'Skill8', skills)

        return HeroStateInfo(hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips,
                             buffs, skills, vis1, vis2, vis3)
