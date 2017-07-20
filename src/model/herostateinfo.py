# -*- coding: utf8 -*-
from equipstateinfo import EquipStateInfo
from fwdstateinfo import FwdStateInfo
from skillstateinfo import SkillStateInfo
from posstateinfo import PosStateInfo


class HeroStateInfo:
    def __init__(self, hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips, buffs, skills):
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

    @staticmethod
    def decode(obj, hero_name):
        print hero_name
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
        skills.append(SkillStateInfo.decode(obj['Skill0'], 'Skill0'))
        skills.append(SkillStateInfo.decode(obj['Skill1'], 'Skill1'))
        skills.append(SkillStateInfo.decode(obj['Skill2'], 'Skill2'))
        skills.append(SkillStateInfo.decode(obj['Skill3'], 'Skill3'))
        skills.append(SkillStateInfo.decode(obj['Skill4'], 'Skill4'))
        skills.append(SkillStateInfo.decode(obj['Skill5'], 'Skill5'))
        skills.append(SkillStateInfo.decode(obj['Skill6'], 'Skill6'))
        skills.append(SkillStateInfo.decode(obj['Skill7'], 'Skill7'))
        skills.append(SkillStateInfo.decode(obj['Skill8'], 'Skill8'))

        return HeroStateInfo(hero_name, state, cfg_id, pos, fwd, hp, maxhp, mp, maxmp, speed, att, gold, hprec, equips, buffs, skills)
