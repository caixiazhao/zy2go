#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import json as JSON
from random import randint

from model.posstateinfo import PosStateInfo
from model.stateinfo import StateInfo


class StateUtil:
    # 注：游戏并不会严格的每528返回一个值，这个只是PC情况，而且中间这个值也可能缩短
    TICK_PER_STATE = 528
    NEARBY_TOWER_RADIUS = 7
    NEARBY_BASEMENT_RADIUS = 7
    ATTACK_HERO_RADIUS = 13  # 13.5
    ATTACK_UNIT_RADIUS = 9  # 10

    ATTACK_SKILL_RANGES = {"10101": 2000, "10110": 8000, "10120": 6000, "10130": 3500,
                           "10200": 2000, "10210": 8000, "10220": 5000, "10230": 6000}

    @staticmethod
    def can_attack_hero(hero_info, defer_hero_info, skill_id):
        return None

    @staticmethod
    def get_skills_can_upgrade(hero_info):
        skills = []
        for i in range(1, 4):
            skill_info = hero_info.skills[i]
            if skill_info.up:
                skills.append(i)
        return skills

    @staticmethod
    def if_hero_at_basement(hero_info):
        basement = PosStateInfo(75140, -80, 0) if hero_info.team == 0 else PosStateInfo(-75680, -80, 0)
        distance = StateUtil.cal_distance(hero_info.pos, basement)
        if distance < StateUtil.NEARBY_BASEMENT_RADIUS:
            return True
        else:
            return False

    @staticmethod
    def if_unit_monster(unit_info):
        # TODO 需要两个boss的id
        if unit_info.cfg_id == 612 or unit_info.cfg_id == 6410 or unit_info.cfg_id == 611:
            return True
        return False

    @staticmethod
    def get_heros_in_team(state_info, team_id):
        return [hero for hero in state_info.heros if hero.team == team_id]

    @staticmethod
    def get_units_in_team(state_info, team_id):
        return [unit for unit in state_info.units if unit.team == team_id and unit.state == "in"]

    @staticmethod
    def parse_state_log(json_str):
        # print(json_str)
        # json_str = json_str[23:]
        # todo maybe becasu python3, the time before the { should be cut off
        state_json = JSON.loads(json_str)
        state_info = StateInfo.decode(state_json)
        return state_info

    @staticmethod
    def update_state_log(prev_state, cur_state):
        if prev_state is None:
            return cur_state
        # 因为每一次传输时候并不是全量信息，所以需要好上一帧的完整信息进行合并
        # 合并小兵信息
        # 合并野怪信息
        # 合并塔信息
        # 合并英雄信息
        new_state = prev_state.merge(cur_state)
        return new_state

    @staticmethod
    def get_nearby_enemy_heros(state_info, hero_id):
        hero = state_info.get_hero(hero_id)
        enemy_hero_team = 1 - hero.team
        enemy_heros = StateUtil.get_heros_in_team(state_info, enemy_hero_team)

        nearby_enemies = []
        for enemy in enemy_heros:
            # 首先需要确定敌方英雄可见
            if enemy.is_enemy_visible():
                distance = StateUtil.cal_distance(hero.pos, enemy.pos)
                if distance < StateUtil.ATTACK_HERO_RADIUS:
                    nearby_enemies.append(enemy)
        return nearby_enemies

    @staticmethod
    def get_nearby_friend_units(state_info, hero_id):
        hero = state_info.get_hero(hero_id)
        friend_unit_team = hero.team
        friend_units = StateUtil.get_units_in_team(state_info, friend_unit_team)

        nearby_friend_units = []
        for unit in friend_units:
            # 排除掉塔
            # 排除掉野怪
            if int(unit.unit_name) > 26 and not StateUtil.if_unit_monster(unit):
                distance = StateUtil.cal_distance(hero.pos, unit.pos)
                if distance < StateUtil.ATTACK_UNIT_RADIUS:
                    nearby_friend_units.append(unit)
        return nearby_friend_units

    @staticmethod
    def get_nearby_enemy_units(state_info, hero_id):
        hero = state_info.get_hero(hero_id)
        enemy_unit_team = 1 - hero.team
        enemy_units = StateUtil.get_units_in_team(state_info, enemy_unit_team)

        nearby_enemy_units = []
        for unit in enemy_units:
            # 排除掉塔
            # 排除掉野怪
            if int(unit.unit_name) > 26 and not StateUtil.if_unit_monster(unit):
                distance = StateUtil.cal_distance(hero.pos, unit.pos)
                if distance < StateUtil.ATTACK_UNIT_RADIUS:
                    nearby_enemy_units.append(unit)
        return nearby_enemy_units

    @staticmethod
    def get_nearby_monsters(state_info, hero_id):
        # TODO 考虑是否可见vis1表示下路阵营是否可见
        return None

    @staticmethod
    def if_near_tower(state_info, hero_state):
        for unit in state_info:
            if int(unit.unit_name) <= 26:
                if StateUtil.cal_distance(unit.pos, hero_state.pos) < 7:  # 根据配置得来
                    return unit
        return None

    @staticmethod
    def if_self_tower(tower_state, hero_name):
        # 英雄27-31属于阵营A，相对应的塔的x值大于0的属于阵营A，塔的编号为1-26
        if int(hero_name) <= 31 and tower_state.pos.x > 0:
            return True
        if int(hero_name) > 31 and tower_state.pos.x < 0:
            return True
        return False

    @staticmethod
    def cal_distance(pos1, pos2):
        # 忽略y值
        distance = math.sqrt((pos1.x - pos2.x) * (pos1.x - pos2.x) + (pos1.y - pos2.y) * (pos1.y - pos2.y)) / 1000
        return distance

    @staticmethod
    def if_retreat(prev_pos, cur_pos, hero_name):
        if int(hero_name) <= 31 and cur_pos.x > prev_pos.x:
            return True
        if int(hero_name) > 31 and cur_pos.x < prev_pos.y:
            return True
        return False

    @staticmethod
    def build_action_command(action):
        if action.action == 'MOVE' and action.pos is not None:
            return {"hero_id": action.hero_name, "action": action.action, "pos": action.pos}
        if action.action == 'ATTACK' and action.tgtid is not None:
            return {"hero_id": action.hero_name, "action": action.action, "tgtid": action.tgtid}
        if action.action == 'CAST' and action.skillid is not None:
            command = {"hero_id": action.hero_name, "action": action.action, "skillid": action.skillid}
            if action.tgtid is not None:
                command['tgtid'] = action.tgtid
            if action.tgtpos is not None:
                command['tgtpos'] = action.tgtpos
            if action.fwd:
                command['fwd'] = action.fwd
            return command
        if action.action == 'UPDATE' and action.skillid is not None:
            return {"hero_id": action.hero_name, "action": action, "skillid": action.skillid}
        if action.action == 'AUTO':
            return {"hero_id": action.hero_name, "action": action.action}
        if action.action == 'HOLD':
            return {"hero_id": action.hero_name, "action": action.action}
        raise ValueError('unexpected action type ' + action)

    @staticmethod
    def build_action_command(hero_id, action, parameters):
        if action == 'MOVE' and 'pos' in parameters:
            return {"hero_id": hero_id, "action": action, "pos": parameters['pos']}
        if action == 'ATTACK' and 'tgtid' in parameters:
            return {"hero_id": hero_id, "action": action, "tgtid": parameters['tgtid']}
        if action == 'CAST' and 'skillid' in parameters:
            command = {"hero_id": hero_id, "action": action, "skillid": parameters['skillid']}
            if 'tgtid' in parameters:
                command['tgtid'] = parameters['tgtid']
            if 'tgtpos' in parameters:
                command['tgtpos'] = parameters['tgtpos']
            if 'fwd' in parameters:
                command['fwd'] = parameters['fwd']
            return command
        if action == 'UPDATE' and 'skillid' in parameters:
            return {"hero_id": hero_id, "action": action, "skillid": parameters['skillid']}
        if action == 'AUTO':
            return {"hero_id": hero_id, "action": action}
        if action == 'HOLD':
            return {"hero_id": hero_id, "action": action}
        raise ValueError('unexpected action type ' + action)

    @staticmethod
    def build_action_response(state_info):
        battle_id = state_info.battleid
        tick = state_info.tick

        action_strs = []
        for hero in state_info.heros:
            # 测试代码：
            # 如果有可以升级的技能，直接选择第一个升级
            skills = StateUtil.get_skills_can_upgrade(hero)
            if len(skills) > 0:
                update_str = StateUtil.build_action_command(hero.hero_name, 'UPDATE', {'skillid': str(skills[0])})
                action_strs.append(update_str)

            # 得到周围的英雄和敌人单位信息
            action_str = None
            nearby_enemy_heros = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name)
            nearby_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name)
            total_len = len(nearby_enemy_heros) + len(nearby_enemy_units)
            if total_len > 0:
                ran_pick = randint(0, total_len - 1)
                tgtid = nearby_enemy_heros[ran_pick].hero_name if ran_pick < len(nearby_enemy_heros) \
                    else nearby_enemy_units[ran_pick - len(nearby_enemy_heros)].unit_name
                tgtpos = nearby_enemy_heros[ran_pick].pos if ran_pick < len(nearby_enemy_heros) \
                    else nearby_enemy_units[ran_pick - len(nearby_enemy_heros)].pos
                fwd = tgtpos.fwd(hero.pos)

                # 优先使用技能
                # 其实技能需要根据种类不同来返回朝向，目标，或者目标地点，甚至什么都不传
                for skillid in range(1, 4):
                    # canuse不光代表是否英雄被沉默了，不能使用技能，也表示当前技能等级是否为0而导致不可用，还表示是否在cd中
                    if hero.skills[skillid].canuse:
                        action_str = StateUtil.build_action_command(hero.hero_name, 'CAST',
                                                                   {'skillid': str(skillid), 'tgtid': tgtid,
                                                                    'tgtpos': tgtpos.to_string(),
                                                                    'fwd': fwd.to_string()})
                        break
                if action_str is None:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'ATTACK', {'tgtid': tgtid})
            # 在前1分钟，命令英雄到达指定地点
            elif StateUtil.TICK_PER_STATE * 2 * 40 > int(tick) > 528:
                if hero.team == 0:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'MOVE', {'pos': '( -5000, -80, 0)'})
                else:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'MOVE', {'pos': '( 5000, -80, 0)'})
            else:
                action_str = StateUtil.build_action_command(hero.hero_name, 'HOLD', {})

            action_strs.append(action_str)

        rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str
