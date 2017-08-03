# -*- coding: utf8 -*-
import numpy as np
from src.util.replayer import Replayer as rp

class Line_input:
    def __init__(self, stateInformation):
        self.stateInformation = stateInformation
        self.hero_name = self.stateInformation.heros[0].hero_name
        self.team=self.stateInformation.heros[0].team
        self.hero_pos=self.stateInformation.heros[0].pos
        self.skills=[[10110,5,0,0,0,0,0,0,0,0,5,0,0,1,8000],[10120,6,0,0,0,0,0,0,0,0,0,0,6,3,6000],
                     [10130,8,0,0,0,0,0,0,0,0,0,7,0,4,3500],[10210,4,4,0,0,0,0,0,4,0,5,0,0,3,8000],
                     [10220,3,0,0,0,0,0,0,0,0,0,7,4,1,5000],[10230,2,10,5,7,0,0,0,0,0,0,0,0,6,6000]]

    def gen_input(self):
        state=[]

        for hero in self.stateInformation.heros:
            hero_input=self.gen_input_hero(hero)
            state=state+hero_input
            #todo:仅对1v1模型有效，第一个英雄为当前操作英雄
        min_tower_distance=int("Inf")
        nearest_tower=None
        for unit in self.stateInformation.units:
            if int(unit.unit_name)<27:
                #get the nearest tower, no matter which team it belongs to
                distance=rp.cal_distance(self.hero_pos,unit.pos)
                if distance<=min_tower_distance and unit.state=="in":
                    min_tower_distance=distance
                    nearest_tower=unit


        if min_tower_distance>20:
            nearest_tower=None
        tower_input=self.gen_input_building(nearest_tower)
        state=state+tower_input

        # creep infos
        enermy_creeps=rp.get_nearby_enemy_units(self.stateInformation,self.hero_name)
        m=len(enermy_creeps)
        n=8
        for i in range(n):
            if i < m:
                state=state+self.gen_input_creep(enermy_creeps[i])
            else:
                temp=np.zeros(6)
                state=state+list(temp)
        friend_creeps=rp.get_nearby_friend_units(self.stateInformation,self.hero_name)
        m=len(friend_creeps)
        for i in range(n):
            if i <m:
                state=state+self.gen_input_creep(friend_creeps[i])
            else:
                temp=np.zeros(6)
                state=state+list(temp)

        return state






    def gen_input_hero(self,hero):
        heroInfo=[int(hero.hero_name), hero.pos[0], hero.pos[1], hero.speed, hero.att, 2000, hero.mag, hero.hp, hero.mp,
                  1000+hero.attspeed, int(hero.movelock), hero.team]
        #todo: 2000 是普攻手长，现只适用于1,2号英雄，其他英雄可能手长不同
        if hero.stae=="in":
            heroInfo.append(1)
        else:
            heroInfo.append(0)

        if hero.vis1==None and hero.vis2!=None:
            heroInfo.append(int(hero.vis2))
        elif hero.vis2==None and hero.vis1!=None:
            heroInfo.append(int(hero.vis1))
        else:
            heroInfo.append(0)
        skill1=self.gen_input_skill(hero.skills[1])
        skill2=self.gen_input_skill(hero.skills[2])
        skill3=self.gen_input_skill(hero.skills[3])
        heroInfo=heroInfo+skill1+skill2+skill3
        return heroInfo
        #13+1+3*18

    def gen_input_skill(self,skill):
        skillid=skill.skill_name
        for i in range(len(self.skills)):
            if skillid==self.skills[i][0]:
                skill_info=self.skills[i]
        skill_info=skill_info+[skill.cost]
        if skill.cd!=None:
            skill_info.append(int(skill.cd))
        else:
            skill_info.append(skill.max_cd)
        if skill.canuse== None:
            skill_info.append(0)
        else:
            skill_info.append(int(skill.canuse))
        return skill_info
        #15+3

        #todo: skill

    def gen_input_building(self,building):
        if building==None:
            building_info=np.zeros(8)
            building_info=list(building_info)
        else:
            building_info=[int(building.unit_name), building.pos[0], building.pos[1], building.att, 7000, building.hp,
                           1000+building.attspeed, building.team]
        return building_info
        #8


    def gen_input_creep(self,creep):
        creep_info=[creep.pos[0],creep.pos[1],creep.att,creep.hp,1000+creep.attspeed,creep.team]
        return creep_info
        #6