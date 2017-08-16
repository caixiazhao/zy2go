# -*- coding: utf8 -*-
import numpy as np

from util.skillutil import SkillUtil
from util.stateutil import StateUtil


class Line_input:
    #注：这个值需要小心调整，会和找附近塔的逻辑有冲突
    NEAR_TOWER_RADIUS = 20

    def __init__(self, stateInformation,hero_name, rival_hero):
        self.stateInformation = stateInformation
        self.hero_name = hero_name
        self.rival_hero = rival_hero
        for hero in stateInformation.heros:
            if hero.hero_name==hero_name:
                self.team=hero.team
                self.hero_pos=hero.pos
        self.skills=[[10110,5,0,0,0,0,0,0,0,0,5,0,0,1,8],[10120,6,0,0,0,0,0,0,0,0,0,0,6,3,6],
                     [10130,8,0,0,0,0,0,0,0,0,0,7,0,4,3.5],[10210,4,4,0,0,0,0,0,4,0,5,0,0,3,8],
                     [10220,3,0,0,0,0,0,0,0,0,0,7,4,1,5],[10230,2,10,5,7,0,0,0,0,0,0,0,0,6,6]]
        #对英雄101,102技能信息的临时编码

    def gen_input(self):
        state=[]

        # 添加双方英雄信息，对线模型暂时只考虑1v1的情况
        my_hero_info = self.stateInformation.get_hero(self.hero_name)
        rival_hero_info = self.stateInformation.get_hero(self.rival_hero)
        my_hero_input = self.gen_input_hero(my_hero_info)

        # 首先判断对手英雄的位置，如果距离过远则不加入队伍中
        if StateUtil.cal_distance(my_hero_info.pos, rival_hero_info.pos) > self.NEAR_TOWER_RADIUS:
            rival_hero_input = np.zeros(len(my_hero_input)).tolist()
            # print "对手距离过远，不作为输入信息"
        else:
            rival_hero_input = self.gen_input_hero(rival_hero_info)
        state += my_hero_input
        state += rival_hero_input

        # 添加附近塔信息（1个）,搜索半径为self.NEAR_TOWER_RADIUS
        #TODO 如果半径过大可能会有多个塔，需要处理这种情况
        nearest_tower = StateUtil.if_near_tower(self.stateInformation, my_hero_info, self.NEAR_TOWER_RADIUS)
        tower_input=self.gen_input_building(nearest_tower)
        state += tower_input

        # 小兵信息
        enermy_creeps=StateUtil.get_nearby_enemy_units(self.stateInformation,self.hero_name)
        m=len(enermy_creeps)
        n=8
        for i in range(n):
            if i < m:
                state=state+self.gen_input_creep(enermy_creeps[i])
            else:
                temp=np.zeros(6)
                state=state+list(temp)
        friend_creeps=StateUtil.get_nearby_friend_units(self.stateInformation,self.hero_name)
        m=len(friend_creeps)
        for i in range(n):
            if i <m:
                state=state+self.gen_input_creep(friend_creeps[i])
            else:
                temp=np.zeros(6)
                state=state+list(temp)

        return state
        #返回总信息向量大小=2*68+8+16*6=240

    #TODO 需要更多注释
    # 英雄信息向量大小13+1+3*18
    def gen_input_hero(self,hero):
        heroInfo=[int(hero.hero_name), hero.pos.x, hero.pos.z, hero.speed, hero.att, 2, hero.mag, hero.hp, hero.mp,
                  1000+hero.attspeed, int(hero.movelock), hero.team]
        #todo: 2 是普攻手长，现只适用于1,2号英雄，其他英雄可能手长不同
        if hero.state=="in":
            heroInfo.append(1)
        else:
            heroInfo.append(0)

        if hero.vis1==None and hero.vis2!=None:
            heroInfo.append(int(hero.vis2))
        elif hero.vis2==None and hero.vis1!=None:
            heroInfo.append(int(hero.vis1))
        else:
            heroInfo.append(0)
        skill_info1 = SkillUtil.get_skill_info(hero.cfg_id, 1)
        skill_info2 = SkillUtil.get_skill_info(hero.cfg_id, 2)
        skill_info3 = SkillUtil.get_skill_info(hero.cfg_id, 3)

        skill_input1 = self.gen_input_skill(skill_info1, hero.skills[1])
        skill_input2 = self.gen_input_skill(skill_info2, hero.skills[2])
        skill_input3 = self.gen_input_skill(skill_info3, hero.skills[3])
        heroInfo=heroInfo+skill_input1+skill_input2+skill_input3
        return heroInfo

    # 技能信息向量大小=15+3
    def gen_input_skill(self, skill_cfg_info, skill):
        skill_input = [skill_cfg_info.instant_dmg, skill_cfg_info.sustained_dmg, skill_cfg_info.restore,
            skill_cfg_info.defend_bonus, skill_cfg_info.attack_bonus, skill_cfg_info.restore_bonus,
            skill_cfg_info.move_bonus, skill_cfg_info.defend_weaken, skill_cfg_info.attack_weaken,
            skill_cfg_info.move_weaken, skill_cfg_info.stun, skill_cfg_info.blink, skill_cfg_info.dmg_range,
            skill_cfg_info.cast_distance, skill_cfg_info.cast_target]

        skill_cost = skill.cost if skill.cost is not None else 0
        skill_max_cd = skill.max_cd if skill.max_cd is not None else 0
        skill_canuse = int(skill.canuse) if skill.canuse is not None else 0
        skill_input.append(skill_cost)
        skill_input.append(skill_max_cd)
        skill_input.append(skill_canuse)
        return skill_input


    def gen_input_building(self,building):
        if building==None:
            building_info=np.zeros(8)
            building_info=list(building_info)
        else:
            building_info=[int(building.unit_name), building.pos.x, building.pos.z, building.att, 7000, building.hp,
                           1000+building.attspeed, building.team]
        return building_info
        #建筑信息向量大小=8


    def gen_input_creep(self,creep):
        creep_info=[creep.pos.x,creep.pos.z,creep.att,creep.hp,1000+creep.attspeed,creep.team]
        return creep_info
        #单个小兵信息大小=6