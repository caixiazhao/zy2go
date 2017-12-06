# -*- coding: utf8 -*-
import numpy as np

from model.skillcfginfo import SkillTargetEnum
from util.skillutil import SkillUtil
from util.stateutil import StateUtil


class Line_Input_Lite:
    NORMARLIZE = 10000

    #注：这个值需要小心调整，会和找附近塔的逻辑有冲突
    NEAR_TOWER_RADIUS = 20

    def __init__(self, stateInformation, hero_name, rival_hero, line_idx=1):
        self.stateInformation = stateInformation
        self.hero_name = hero_name
        self.rival_hero = rival_hero
        self.line_idx = line_idx
        for hero in stateInformation.heros:
            if hero.hero_name==hero_name:
                self.team=hero.team
                self.hero_pos=hero.pos

    def gen_team_input(self):
        hero = self.stateInformation.get_hero(self.hero_name)
        team = 1 if hero.team == 1 else 0
        team_input = []
        for i in range(64):
            team_input.append(team)
        return team_input

    # 返回总信息向量大小=2*67+9*3+16*7=273
    def gen_line_input(self, revert=False):
        state=[]

        my_hero_info = self.stateInformation.get_hero(self.hero_name)
        rival_hero_info = self.stateInformation.get_hero(self.rival_hero)

        # 添加附近塔信息（2个）,搜索半径为self.NEAR_TOWER_RADIUS
        nearest_towers = StateUtil.get_near_towers_in_line(self.stateInformation, my_hero_info, self.line_idx, self.NEAR_TOWER_RADIUS)
        nearest_towers_rival = [t for t in nearest_towers if t.team != my_hero_info.team]
        nearest_towers_team = [t for t in nearest_towers if t.team == my_hero_info.team]
        # print("input debug", ":", "hero", self.hero_name, 'rival_tower', nearest_towers_rival, 'team_tower', nearest_towers_team)

        # 添加双方英雄信息，对线模型暂时只考虑1v1的情况
        my_hero_input = self.gen_input_hero(my_hero_info, nearest_towers_rival, revert)

        # 首先判断对手英雄的位置，如果距离过远则不加入队伍中
        if StateUtil.cal_distance(my_hero_info.pos, rival_hero_info.pos) > self.NEAR_TOWER_RADIUS:
            rival_hero_input = np.zeros(len(my_hero_input)).tolist()
            # print "对手距离过远，不作为输入信息"
        else:
            rival_hero_input = self.gen_input_hero(rival_hero_info, nearest_towers_rival, revert)
        state += my_hero_input
        state += rival_hero_input

        # print(self.hero_name + ' 训练输入信息，敌方塔信息：' + ','.join([str(t.unit_name) for t in nearest_towers_rival]))
        # print(self.hero_name + ' 训练输入信息，己方塔信息：' + ','.join([str(t.unit_name) for t in nearest_towers_team]))
        if len(nearest_towers_rival) == 0:
            tower_input1 = self.gen_input_building(None)
            tower_input2 = self.gen_input_building(None)
        elif len(nearest_towers_rival) == 1:
            tower_input1 = self.gen_input_building(nearest_towers_rival[0], self.stateInformation, self.hero_name, revert)
            tower_input2 = self.gen_input_building(None)
        # 当玩家处在高地时候会有超过2个塔
        elif len(nearest_towers_rival) >= 2:
            tower_input1 = self.gen_input_building(nearest_towers_rival[0], self.stateInformation, self.hero_name, revert)
            tower_input2 = self.gen_input_building(nearest_towers_rival[1], self.stateInformation, self.hero_name, revert)
        else:
            tower_input1 = self.gen_input_building(nearest_towers_rival[0], self.stateInformation, self.hero_name, revert)
            tower_input2 = self.gen_input_building(nearest_towers_rival[1], self.stateInformation, self.hero_name, revert)
        # 添加一个己方塔
        if len(nearest_towers_team) == 0:
            tower_input3 = self.gen_input_building(None)
        else:
            tower_input3 = self.gen_input_building(nearest_towers_team[0], self.stateInformation, self.hero_name, revert)
        state += tower_input1
        state += tower_input2
        state += tower_input3

        # 小兵信息
        enermy_creeps=StateUtil.get_nearby_enemy_units(self.stateInformation,self.hero_name)
        m=len(enermy_creeps)
        n=8
        for i in range(n):
            if i < m:
                state=state+self.gen_input_creep(enermy_creeps[i], self.stateInformation, self.hero_name, nearest_towers_rival, revert)
            else:
                temp=self.gen_input_creep(None)
                state=state+list(temp)
        friend_creeps=StateUtil.get_nearby_friend_units(self.stateInformation, self.hero_name)
        m=len(friend_creeps)
        for i in range(n):
            if i <m:
                state=state+self.gen_input_creep(friend_creeps[i], self.stateInformation, self.hero_name, nearest_towers_rival)
            else:
                temp = self.gen_input_creep(None)
                state=state+list(temp)

        return state

    def normalize_value(self, value):
        return float(value)/Line_Input_Lite.NORMARLIZE

    @staticmethod
    def normalize_value_static(value):
        return float(value)/Line_Input_Lite.NORMARLIZE

    def normalize_skill_value(self, value):
        return float(value)/10

    #TODO 需要更多注释
    # 英雄信息向量大小16+3*17
    def gen_input_hero(self, hero, rival_towers, revert=False):
        if hero.state == 'out' or hero.hp <= 0:
            return list(np.zeros(16+3*17))

        dis_rival = 10000
        if len(rival_towers) > 0:
            dis_list = [StateUtil.cal_distance2(hero.pos, t.pos) for t in rival_towers]
            dis_rival = min(dis_list)

        hero_input = [self.normalize_value(hero.pos.x if not revert else -hero.pos.x),
                  self.normalize_value(hero.pos.z if not revert else -hero.pos.z),
                  self.normalize_value(hero.speed),
                  self.normalize_value(hero.att),
                  self.normalize_value(hero.attspeed),
                  self.normalize_value(hero.attpen),
                  self.normalize_value(hero.attpenrate),
                  # # todo: 2 是普攻手长，现只适用于1,2号英雄，其他英雄可能手长不同
                  # 0.2,
                  self.normalize_value(hero.hp),
                  hero.hp/float(hero.maxhp),
                  self.normalize_value(hero.hprec),
                  self.normalize_value(hero.mp),
                  self.normalize_value(hero.mag),
                  self.normalize_value(hero.magpen),
                  self.normalize_value(hero.magpenrate),
                  self.normalize_value(dis_rival),
                  hero.team if not revert else 1-hero.team]

        # is_enemy_visible = hero.is_enemy_visible()
        # hero_input.append(int(is_enemy_visible))

        skill_info1 = SkillUtil.get_skill_info(hero.cfg_id, 1)
        skill_info2 = SkillUtil.get_skill_info(hero.cfg_id, 2)
        skill_info3 = SkillUtil.get_skill_info(hero.cfg_id, 3)

        skill_input1 = self.gen_input_skill(skill_info1, hero.skills[1])
        skill_input2 = self.gen_input_skill(skill_info2, hero.skills[2])
        skill_input3 = self.gen_input_skill(skill_info3, hero.skills[3])
        hero_input=hero_input+skill_input1+skill_input2+skill_input3
        return hero_input

    # 技能信息向量大小=5
    def gen_input_skill(self, skill_cfg_info, skill):
        skill_input = [
            self.normalize_skill_value(skill_cfg_info.instant_dmg),
            self.normalize_skill_value(skill_cfg_info.sustained_dmg),
            self.normalize_skill_value(skill_cfg_info.restore),
            self.normalize_skill_value(skill_cfg_info.defend_bonus),
            self.normalize_skill_value(skill_cfg_info.attack_bonus),
            self.normalize_skill_value(skill_cfg_info.restore_bonus),
            self.normalize_skill_value(skill_cfg_info.move_bonus),
            self.normalize_skill_value(skill_cfg_info.defend_weaken),
            self.normalize_skill_value(skill_cfg_info.attack_weaken),
            self.normalize_skill_value(skill_cfg_info.move_weaken),
            self.normalize_skill_value(skill_cfg_info.stun),
            self.normalize_skill_value(skill_cfg_info.blink),
            self.normalize_skill_value(skill_cfg_info.dmg_range),
            self.normalize_skill_value(skill_cfg_info.cast_distance),
            # 是否可以给自己和敌人施法
            1 if skill_cfg_info.cast_target == SkillTargetEnum.self or skill_cfg_info.cast_target == SkillTargetEnum.both else 0,
            1 if skill_cfg_info.cast_target == SkillTargetEnum.rival or skill_cfg_info.cast_target == SkillTargetEnum.both else 0]

        # skill_cost = skill.cost if skill.cost is not None else 0
        # skill_max_cd = skill.max_cd if skill.max_cd is not None else 0
        skill_canuse = int(skill.canuse) if skill.canuse is not None else 0
        # skill_input.append(self.normalize_value(skill_cost))
        # skill_input.append(self.normalize_value(skill_max_cd))
        skill_input.append(skill_canuse)
        return skill_input

    # 建筑信息向量大小9个字段
    def gen_input_building(self,building, state_info=None, hero_name=None, revert=False):
        if building is None:
            building_info=np.zeros(9)
            building_info=list(building_info)
        else:
            hero_info = state_info.get_hero(hero_name)
            building_info=[self.normalize_value(int(building.unit_name)),
                           self.normalize_value(building.pos.x if not revert else -building.pos.x),
                           self.normalize_value(building.pos.z if not revert else -building.pos.z),
                           self.normalize_value(building.att),
                           self.normalize_value(7000),
                           self.normalize_value(building.hp),
                           self.normalize_value(StateUtil.cal_distance2(building.pos, hero_info.pos)),
                           building.team if not revert else 1-building.team]
            # 添加是否在攻击当前英雄
            attack_info = state_info.if_unit_attack_hero(building.unit_name, hero_name)
            if attack_info is None:
                building_info.append(0)
            else:
                building_info.append(1)
        return building_info

    # 单个小兵信息大小=7
    def gen_input_creep(self, creep, state_info=None, hero_name=None, towers=None, revert=False):
        if creep is None:
            return list(np.zeros(7))

        dis = 10000
        if len(towers) > 0:
            dis_list = [StateUtil.cal_distance2(creep.pos, t.pos) for t in towers]
            dis = min(dis_list)

        creep_info=[self.normalize_value(creep.pos.x if not revert else -creep.pos.x),
                    self.normalize_value(creep.pos.z if not revert else -creep.pos.z),
                    self.normalize_value(creep.att),
                    self.normalize_value(creep.hp),
                    self.normalize_value(dis),
                    creep.team if not revert else 1-creep.team]

        # 添加是否在攻击当前英雄
        attack_info = state_info.if_unit_attack_hero(creep.unit_name, hero_name)
        if attack_info is None:
            creep_info.append(0)
        else:
            creep_info.append(1)
        return creep_info