#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import json as JSON
from random import randint

from hero_strategy.soldierline import SoldierLine
from model.fwdstateinfo import FwdStateInfo
from model.posstateinfo import PosStateInfo
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum


class StateUtil:
    # 注：游戏并不会严格的每528返回一个值，这个只是PC情况，而且中间这个值也可能缩短
    TICK_PER_STATE = 528
    NEARBY_BASEMENT_RADIUS = 7
    ATTACK_HERO_RADIUS = 7  # 13.5
    ATTACK_UNIT_RADIUS = 7  # 10
    TOWER_ATTACK_RADIUS = 8

    # 需要和ATTACK_HERO_RADIUS一致才行
    LINE_MODEL_RADIUS = 7
    GOLD_GAIN_RADIUS = 11
    MAX_RADIUS = 50

    BASEMENT_TEAM_0 = PosStateInfo(-75680, -80, 0)
    BASEMENT_TEAM_1 = PosStateInfo(75140, -80, 0)

    ATTACK_SKILL_RANGES = {"10101": 2000, "10110": 8000, "10l120": 6000, "10130": 3500,
                           "10200": 2000, "10210": 8000, "10220": 5000, "10230": 6000}

    LINE_WAY_POINTS = [
        [PosStateInfo(56800, 0, -2800), PosStateInfo(54000, 0, -5100), PosStateInfo(53000, 0, -20000),
         PosStateInfo(37500, 0, -29500), PosStateInfo(31800, 0, -38700), PosStateInfo(14000, 0, -54500),
         PosStateInfo(-600, 0, -61000), PosStateInfo(-22100, 0, -47000), PosStateInfo(-33400, 0, -37500),
         PosStateInfo(-41000, 0, -27000), PosStateInfo(-51000, 0, -13000), PosStateInfo(-56300, 0, 800)],

        [PosStateInfo(58100, 0, -100), PosStateInfo(45100, 0, -2000), PosStateInfo(28800, 0, 500),
         PosStateInfo(16900, 0, 1000), PosStateInfo(0, 0, -1000), PosStateInfo(-11500, 0, 300), PosStateInfo(-17400, 0, -200),
         PosStateInfo(-44900, 0, 2600), PosStateInfo(-56500, 0, 1700)],

        [PosStateInfo(56900, 0, 2600), PosStateInfo(54000, 0, 5000), PosStateInfo(54200, 0, 18400),
         PosStateInfo(43300, 0, 25700), PosStateInfo(36500, 0, 34000), PosStateInfo(26000, 0, 45200),
         PosStateInfo(0, 0, 60800), PosStateInfo(-20600, 0, 51700), PosStateInfo(-39900, 0, 30000),
         PosStateInfo(-52900, 0, 14800), PosStateInfo(-56800, 0, 2600)]]

    @staticmethod
    def if_hero_dead(prev_state, cur_state, hero_name):
        prev_hero = prev_state.get_hero(hero_name)
        cur_hero = cur_state.get_hero(hero_name)
        dead = 1 if prev_hero.hp > 0 and cur_hero.hp <= 0 else 0
        if dead:
            breakpoint = 1
        return dead

    @staticmethod
    def get_attack_cast_dmg(cur_state, next_state, next_next_state, hero_name, rival_hero):
        dmg = 0
        cur_act = cur_state.get_hero_action(hero_name)
        skill_slot = cur_act.skillid
        # 只有攻击才会计算对对方英雄造成的伤害
        if cur_act.action == CmdActionEnum.CAST:
            # 对于技能，查看当前帧和后续帧，这个技能造成的伤害
            dmg = next_state.get_hero_dmg_skill(hero_name, skill_slot, rival_hero)
            dmg += next_next_state.get_hero_dmg_skill(hero_name, skill_slot, rival_hero)
        elif cur_act.action == CmdActionEnum.ATTACK:
            # 对于物攻，同样因为伤害有延迟，先检查玩家在下一帧的行动
            # 如果不是物攻，这读取这两帧中间的物攻伤害
            next_act = next_state.get_hero_action(hero_name)
            if next_act is None or next_act.action != CmdActionEnum.ATTACK:
                dmg = next_state.get_hero_dmg_skill(hero_name, skill_slot, rival_hero)
                dmg += next_next_state.get_hero_dmg_skill(hero_name, skill_slot, rival_hero)
            else:
                # 否则只计算当前帧的，简单起见
                dmg = next_state.get_hero_dmg_skill(hero_name, skill_slot, rival_hero)
        return dmg

    @staticmethod
    # 固定检测中路第一个塔是否被摧毁了
    def if_first_tower_destroyed_in_middle_line(state_info):
        for unit in state_info.units:
            if unit.pos.x == 17110 or unit.pos.x == -17110:
                if unit.hp <= 0:
                    print(unit.unit_name + '塔被摧毁, win:' + str(unit.team) + " detail：" + unit.pos.to_string())
                    return unit.team
        return None

    @staticmethod
    def get_tower_hp_change(state_info, next_info, hero_name, line_idx, self_tower=True):
        hero_state = state_info.get_hero(hero_name)
        near_own_towers = StateUtil.get_near_towers_in_line(state_info, hero_state, line_idx, StateUtil.LINE_MODEL_RADIUS)
        if self_tower:
            near_own_towers = [t for t in near_own_towers if t.team == hero_state.team]
        else:
            near_own_towers = [t for t in near_own_towers if t.team != hero_state.team]
        hp_change = 0
        destroyed = False
        for tower in near_own_towers:
            next_state_tower = next_info.get_unit(tower.unit_name)
            if next_state_tower is None or next_state_tower.hp <= 0:
                hp_change += float(tower.hp)/tower.maxhp
                destroyed = True
            else:
                hp_change += float(tower.hp - next_state_tower.hp)/tower.maxhp
        return hp_change, destroyed

    @staticmethod
    def get_skills_can_upgrade(hero_info):
        skills = []
        for i in range(1, 4):
            skill_info = hero_info.skills[i]
            if skill_info.up:
                skills.append(i)
        return skills

    @staticmethod
    def get_basement(hero_info):
        return StateUtil.BASEMENT_TEAM_1 if hero_info.team == 1 else StateUtil.BASEMENT_TEAM_0

    @staticmethod
    def if_hero_at_basement(hero_info):
        basement = StateUtil.BASEMENT_TEAM_1 if hero_info.team == 1 else StateUtil.BASEMENT_TEAM_0
        distance = StateUtil.cal_distance(hero_info.pos, basement)
        if distance < StateUtil.NEARBY_BASEMENT_RADIUS:
            return True
        else:
            return False

    @staticmethod
    def if_unit_monster(unit_info):
        # TODO 需要两个boss的id
        if int(unit_info.cfg_id) == 612 or int(unit_info.cfg_id) == 6410 or int(unit_info.cfg_id) == 611:
            return True
        return False

    @staticmethod
    def if_unit_tower(unit_name):
        if 26 >= int(unit_name) > 0:
            return True
        return False

    @staticmethod
    def if_unit_hero(unit_name):
        if 27 <= int(unit_name) <= 28:
            return True
        return False

    @staticmethod
    def get_heros_in_team(state_info, team_id):
        return [hero for hero in state_info.heros if hero.team == team_id]

    @staticmethod
    def get_units_in_team(state_info, team_id):
        return [unit for unit in state_info.units if unit.team == team_id and unit.state == 'in' and unit.hp > 0]

    @staticmethod
    def get_dead_units_in_line(state_info, team_id, line_index, hero_info=None, search_range=MAX_RADIUS):
        result = []
        for unit in state_info.units:
            # 小兵死亡最后一条maxhp=0, hp=1，state=out，倒数第二条 maxhp正常，hp=0 state=in
            # 我们还是以ｈｐ＝０作为死亡的信息吧
            if unit.hp <= 0 and unit.team == team_id:
                if StateUtil.if_in_line(unit, line_index) > 0:
                    if hero_info is not None:
                        if StateUtil.cal_distance(unit.pos, hero_info.pos) <= search_range:
                            result.append(unit)
                    else:
                        result.append(unit)
        return result

    @staticmethod
    # TODO 核对信息
    def get_unit_value(unit_name, unit_cfgid):
        if int(unit_cfgid) == 911:
            return 25
        if int(unit_cfgid) == 912:
            return 20
        if int(unit_cfgid) == 913:
            return 50
        if int(unit_cfgid) == 914:
            return 50
        if int(unit_name) < 27:
            return 200
        else:
            print("unknow value unit %s cfg %s" % (unit_name, unit_cfgid))
        return -1

    @staticmethod
    def get_frontest_soldier_in_line(state_info, line_index, team_id):
        units = StateUtil.get_units_in_team(state_info, team_id)
        soldiers = [u for u in units if not StateUtil.if_unit_monster(u) and not StateUtil.if_unit_tower(u.unit_name)]
        soldiers_in_line = 0
        frontest = None
        for idx, soldier in enumerate(soldiers):
            line_pos = StateUtil.if_in_line(soldier, line_index)
            if line_pos >= 0:
                soldiers_in_line += 1
                frontest = frontest if frontest is not None and ((frontest.pos.x > soldier.pos.x and team_id == 0) or
                                    (frontest.pos.x < soldier.pos.x and team_id == 1)) else soldier

        # print('front_point team:%s, line:%s, %s/%s in line, frontest.x: %s' % (team_id, line_index, soldiers_in_line,
        #                                                                      len(soldiers), 0 if frontest is None else frontest.pos.x))
        return frontest

    @staticmethod
    def get_units_in_line(units, line_index):
        units_in_line = []
        for unit in units:
            if unit is None:
                continue
            line_pos = StateUtil.if_in_line(unit, line_index)
            if line_pos >= 0:
                units_in_line.append(unit)
        return units_in_line

    # 得到兵线位置，小兵数量
    # 兵线编号，从左到右为0-2
    # 逻辑过于复杂，可能因为一个兵线格子过长，计算中点时候导致离真实的两波小兵都很远
    @staticmethod
    def get_solider_lines(state_info, line_index, team_id):
        units = StateUtil.get_units_in_team(state_info, team_id)
        soldiers = [u for u in units if not StateUtil.if_unit_monster(u) and not StateUtil.if_unit_tower(u.unit_name)]
        line_pos_map = {}
        soldiers_in_line = 0
        for idx, soldier in enumerate(soldiers):
            line_pos = StateUtil.if_in_line(soldier, line_index)
            if line_pos >= 0:
                soldiers_in_line += 1
                if line_pos not in line_pos_map:
                    line_pos_map[line_pos] = [soldier.unit_name]
                else:
                    line_pos_map[line_pos].append(soldier.unit_name)

        print('front_point team:%s, line:%s, %s/%s in line' % (team_id, line_index, soldiers_in_line, len(soldiers)))

        # 遍历所有的小兵位置信息，然后返回小兵的集中点
        # 集中点的定义为：每个格子记录一个集中点，为这个格子内所有小兵的中心位置
        soldier_lines = []
        cache_units = []
        for line_pos_idx in range(len(StateUtil.LINE_WAY_POINTS[line_index])):
            # 如果当前兵线区域没有小兵，则连续中断，将之前连续的部分存成一个集中点
            if line_pos_idx not in line_pos_map:
                # 计算中点
                pos = StateUtil.cal_soldier_wave_point(state_info, line_pos_map[line_pos_idx])
                sl = SoldierLine(team_id, line_index, pos, cache_units)
                soldier_lines.append(sl)

        # 按照兵线从开始到结尾进行排序 team0的顺序需要翻转
        if team_id == 1 and len(soldier_lines) > 0:
            soldier_lines.reverse()

        return soldier_lines

    @staticmethod
    def cal_soldier_wave_point(state_info, unit_index_list):
        cached_x = 0
        cached_z = 0
        for unit_name in unit_index_list:
            unit = state_info.get_unit(unit_name)
            cached_x += unit.pos.x
            cached_z += unit.pos.z
        return PosStateInfo(int(cached_x/len(unit_index_list)),int( -80),int( cached_z/len(unit_index_list)))


    # 返回单位在兵线上的位置
    # 结果从0开始
    @staticmethod
    def if_in_line(unit_info, line_index, range=3000):
        line = StateUtil.LINE_WAY_POINTS[line_index]
        for idx, point in enumerate(line):
            if idx >= len(line) - 1:
                continue
            next_point = line[idx+1]
            bound_x1 = min(next_point.x, point.x)
            bound_x2 = max(next_point.x, point.x)
            bound_y1 = min(next_point.z, point.z) - range
            bound_y2 = max(next_point.z, point.z) + range
            if bound_x1 <= unit_info.pos.x <= bound_x2 and bound_y1 <= unit_info.pos.z <= bound_y2:
                return idx
        return -1

    @staticmethod
    def parse_state_log(json_str):
        # print(json_str)
        json_str = json_str[23:]
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
    def get_nearby_enemy_heros(state_info, hero_id, max_distance=ATTACK_HERO_RADIUS):
        hero = state_info.get_hero(hero_id)
        enemy_hero_team = 1 - hero.team
        enemy_heros = StateUtil.get_heros_in_team(state_info, enemy_hero_team)

        nearby_enemies = []
        for enemy in enemy_heros:
            # 首先需要确定敌方英雄可见
            if enemy.is_enemy_visible() and enemy.hp > 0:
                distance = StateUtil.cal_distance(hero.pos, enemy.pos)
                if distance < max_distance:
                    nearby_enemies.append(enemy)
        nearby_enemies.sort(key=lambda h: int(h.hero_name), reverse=True)
        return nearby_enemies

    @staticmethod
    def get_nearby_friend_units(state_info, hero_id, max_distance=ATTACK_HERO_RADIUS):
        hero = state_info.get_hero(hero_id)
        friend_unit_team = hero.team
        friend_units = StateUtil.get_units_in_team(state_info, friend_unit_team)

        nearby_friend_units = []
        for unit in friend_units:
            # 排除掉塔
            # 排除掉野怪
            if int(unit.unit_name) > 26 and not StateUtil.if_unit_monster(unit) and unit.hp > 0:
                distance = StateUtil.cal_distance(hero.pos, unit.pos)
                if distance < max_distance:
                    nearby_friend_units.append(unit)
        nearby_friend_units.sort(key=lambda u: int(u.unit_name), reverse=True)
        return nearby_friend_units

    @staticmethod
    def get_nearby_enemy_units(state_info, hero_id, max_distance=ATTACK_HERO_RADIUS):
        hero = state_info.get_hero(hero_id)
        enemy_unit_team = 1 - hero.team
        enemy_units = StateUtil.get_units_in_team(state_info, enemy_unit_team)

        nearby_enemy_units = []
        for unit in enemy_units:
            # 排除掉塔
            # 排除掉野怪
            if int(unit.unit_name) > 26 and not StateUtil.if_unit_monster(unit) and unit.hp > 0 and unit.state == 'in':
                distance = StateUtil.cal_distance(hero.pos, unit.pos)
                if distance < max_distance:
                    nearby_enemy_units.append(unit)
        nearby_enemy_units.sort(key=lambda u: int(u.unit_name), reverse=True)
        return nearby_enemy_units

    @staticmethod
    def get_nearest_enemy_tower(state_info, hero_id, max_distance=ATTACK_HERO_RADIUS):
        hero = state_info.get_hero(hero_id)
        enemy_unit_team = 1 - hero.team
        enemy_units = StateUtil.get_units_in_team(state_info, enemy_unit_team)
        nearest_enemy_tower = None
        for unit in enemy_units:
            # 排除小兵
            # 排除掉野怪
            if int(unit.unit_name) < 27 and not StateUtil.if_unit_monster(unit) and unit.hp > 0:
                distance = StateUtil.cal_distance(hero.pos, unit.pos)
                if distance < max_distance:
                    nearest_enemy_tower=unit
                    max_distance=distance
        return nearest_enemy_tower

    @staticmethod
    def get_first_tower(state_info, hero):
        for unit in state_info.units:
            if unit.team == hero.team and (unit.pos.x == 17110 or unit.pos.x == -17110):
                return unit
        return None

    @staticmethod
    def get_hp_restore_place(state_info, hero):
        for unit in state_info.units:
            if unit.team == hero.team and (unit.pos.x == 17110 or unit.pos.x == -17110):
                # 移动到塔后侧
                near_tower_x = unit.pos.x - 3000 if hero.team == 0 else unit.pos.x + 3000
                pos = PosStateInfo(near_tower_x, unit.pos.y, unit.pos.z)
                return pos
        return None

    @staticmethod
    # 和下面函数的区别是这里是到达补血点
    def get_tower_behind(tower_info, hero, line_index):
        near_tower_x = tower_info.pos.x - 4000 if hero.team == 0 else tower_info.pos.x + 4000
        pos = PosStateInfo(near_tower_x, tower_info.pos.y, tower_info.pos.z)
        return pos

    @staticmethod
    # 这里是到达一个撤退点，注意不要去吃加血符文
    def get_retreat_pos(state_info, hero, line_index):
        towers = []
        for unit in state_info.units:
            if StateUtil.if_unit_tower(unit.unit_name) and unit.team == hero.team:
                if StateUtil.if_in_line(unit, line_index) >= 0:
                    # 在英雄后面的塔
                    if hero.team == 0 and hero.pos.x > unit.pos.x:
                        towers.append(unit)
                    elif hero.team == 1 and hero.pos.x < unit.pos.x:
                        towers.append(unit)
        if len(towers) > 0:
            towers.sort(key=lambda t: math.fabs(hero.pos.x - t.pos.x), reverse=False)
            near_tower = towers[0]
            # 移动到塔后侧
            near_tower_x = near_tower.pos.x - 3000 if hero.team == 0 else near_tower.pos.x + 3000
            near_tower_z = near_tower.pos.z - 2000 if hero.team == 0 else near_tower.pos.z + 2000
            pos = PosStateInfo(near_tower_x, near_tower.pos.y, near_tower_z)
            return pos
        else:
            basement_pos = StateUtil.BASEMENT_TEAM_1 if hero.team == 1 else StateUtil.BASEMENT_TEAM_0
            return basement_pos

    @staticmethod
    def get_near_towers_in_line(state_info, hero_state, line_idx, distance):
        towers = []
        for unit in state_info.units:
            if int(unit.unit_name) <= 26:
                if StateUtil.if_in_line(unit, line_idx) >= 0:
                    if StateUtil.cal_distance(unit.pos, hero_state.pos) < distance:  # 根据配置得来
                        towers.append(unit)
        return towers

    @staticmethod
    def cal_distance2(pos1, pos2):
        # 忽略y值
        distance = math.sqrt((pos1.x - pos2.x) * (pos1.x - pos2.x) + (pos1.z - pos2.z) * (pos1.z - pos2.z))
        return distance

    @staticmethod
    def cal_distance(pos1, pos2):
        # 忽略y值
        distance = math.sqrt((pos1.x - pos2.x) * (pos1.x - pos2.x) + (pos1.z - pos2.z) * (pos1.z - pos2.z)) / 1000
        return distance

    @staticmethod
    def if_retreat(prev_pos, cur_pos, hero):
        if hero.team == 0 and cur_pos.x < prev_pos.x:
            return True
        if hero.team == 1 and cur_pos.x > prev_pos.x:
            return True
        return False

    @staticmethod
    def mov(direction):
        # 根据输入0~7这8个整数，选择上下左右等八个方向返回
        if direction == 0:
            return FwdStateInfo(1000, 0, 0)
        elif direction == 1:
            return FwdStateInfo(707, 0, 707)
        elif direction == 2:
            return FwdStateInfo(0, 0, 1000)
        elif direction == 3:
            return FwdStateInfo(-707, 0, 707)
        elif direction == 4:
            return FwdStateInfo(0, 0, -1000)
        elif direction == 5:
            return FwdStateInfo(-707, 0, -707)
        elif direction == 6:
            return FwdStateInfo(-1000, 0, 0)
        else:
            return FwdStateInfo(-707, 0, 707)

    @staticmethod
    def build_command(action):
        if action.action == CmdActionEnum.MOVE and action.tgtpos is not None:
            return {"hero_id": action.hero_name, "action": 'MOVE', "pos": action.tgtpos.to_string()}
        if action.action == CmdActionEnum.MOVE and action.fwd is not None:
            return {"hero_id": action.hero_name, "action": 'MOVE', "fwd": action.fwd.to_string()}
        if action.action == CmdActionEnum.ATTACK and action.tgtid is not None:
            return {"hero_id": action.hero_name, "action": 'ATTACK', "tgtid": str(action.tgtid)}
        if action.action == CmdActionEnum.CAST and action.skillid is not None:
            command = {"hero_id": action.hero_name, "action": 'CAST', "skillid": str(action.skillid)}
            if action.tgtid is not None:
                command['tgtid'] = str(action.tgtid)
            if action.tgtpos is not None:
                command['tgtpos'] = action.tgtpos.to_string()
            if action.fwd:
                command['fwd'] = action.fwd.to_string()
            return command
        if action.action == CmdActionEnum.UPDATE and action.skillid is not None:
            return {"hero_id": action.hero_name, "action": 'UPDATE', "skillid": str(action.skillid)}
        if action.action == CmdActionEnum.BUY and action.itemid is not None:
            return {"hero_id": action.hero_name, "action": 'BUY', "itemid": str(action.itemid)}
        if action.action == CmdActionEnum.AUTO:
            return {"hero_id": action.hero_name, "action": 'AUTO'}
        if action.action == CmdActionEnum.HOLD:
            # 设置hold的行为为移动到本地。因为如果之前一个动作是攻击，hold等于继续攻击
            return {"hero_id": action.hero_name, "action": 'MOVE', "pos": action.tgtpos.to_string()}
        if action.action == CmdActionEnum.RETREAT:
            return {"hero_id": action.hero_name, "action": 'MOVE', "pos": action.tgtpos.to_string()}
        if action.action == CmdActionEnum.RESTART:
            return {"hero_id": action.hero_name, "action": 'RESTART'}
        raise ValueError('unexpected action type ' + str(action.action))

    @staticmethod
    def build_action_command(hero_id, action, parameters):
        #todo 这个函数现在只传了一个action进来，但是现在的action里面以及包含了需要的信息了，这个函数需要重写一下
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
        if action == 'RESTART':
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

    @staticmethod
    def get_hit_rival_tower_dmg_ratio(cur_state, next_state, next_next_state, hero_name):
        dmg = 0
        cur_act = cur_state.get_hero_action(hero_name)
        skill_slot = cur_act.skillid
        if cur_act.action == CmdActionEnum.ATTACK:
            # 对于物攻，同样因为伤害有延迟，先检查玩家在下一帧的行动
            # 如果不是物攻，这读取这两帧中间的物攻伤害
            next_act = next_state.get_hero_action(hero_name)
            if next_act is None or next_act.action != CmdActionEnum.ATTACK:
                dmg = next_state.get_hero_tower_dmg(hero_name)
                dmg += next_next_state.get_hero_tower_dmg(hero_name)
            else:
                # 否则只计算当前帧的，简单起见
                dmg = next_state.get_hero_tower_dmg(hero_name)
        return dmg