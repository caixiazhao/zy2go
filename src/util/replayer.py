#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 解析json日志，还原出来基础信息
# 得到每次
#   英雄位置信息，
#   兵线信息
#   技能冷却信息
#   攻击信息
#   野怪信息
# 统计出来
#   玩家意图

# 第一条信息貌似和后续信息有所不同
import json as JSON
import math
from random import randint

from hero_strategy.actionenum import ActionEnum
from hero_strategy.herostrategy import HeroStrategy
from hero_strategy.strategyaction import StrategyAction
from hero_strategy.strategyrecords import StrategyRecords
from model.posstateinfo import PosStateInfo
from src.model.stateinfo import StateInfo


class Replayer:
    # 注：游戏并不会严格的每528返回一个值，这个只是PC情况，而且中间这个值也可能缩短
    TICK_PER_STATE = 528
    NEARBY_TOWER_RADIUS = 7
    NEARBY_BASEMENT_RADIUS = 7
    ATTACK_HERO_RADIUS = 13 #13.5
    ATTACK_UNIT_RADIUS = 9 #10

    ATTACK_SKILL_RANGES = {"10101": 2000, "10110": 8000, "10120": 6000, "10130":3500,
                           "10200": 2000, "10210": 8000, "10220": 5000, "10230":6000}

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
        distance = Replayer.cal_distance(hero_info.pos, basement)
        if distance < Replayer.NEARBY_BASEMENT_RADIUS:
            return True
        else:
            return False

    @staticmethod
    def if_unit_monster(unit_info):
        #TODO 需要两个boss的id
        if unit_info.cfg_id == 612 or unit_info.cfg_id == 6410 or unit_info.cfg_id == 611:
            return True
        return False

    @staticmethod
    def get_heros_in_team(state_info, team_id):
        return [hero for hero in state_info.heros if hero.team == team_id]

    @staticmethod
    def get_units_in_team(state_info, team_id):
        return [unit for unit in state_info.units if unit.team == team_id]

    @staticmethod
    def parse_state_log(json_str):
        #print(json_str)
        json_str = json_str[23:]
        #maybe becasu python3, the time before the { should be cut off
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
        enemy_heros = Replayer.get_heros_in_team(state_info, enemy_hero_team)

        nearby_enemies = []
        for enemy in enemy_heros:
            # 首先需要确定敌方英雄可见
            if enemy.is_enemy_visible():
                distance = Replayer.cal_distance(hero.pos, enemy.pos)
                if distance < Replayer.ATTACK_HERO_RADIUS:
                    nearby_enemies.append(enemy)
        return nearby_enemies

    @staticmethod
    def get_nearby_enemy_units(state_info, hero_id):
        hero = state_info.get_hero(hero_id)
        enemy_unit_team = 1 - hero.team
        enemy_units = Replayer.get_units_in_team(state_info, enemy_unit_team)

        nearby_enemy_units = []
        for unit in enemy_units:
            # 排除掉塔
            # 排除掉野怪
            if int(unit.unit_name) > 26 and not Replayer.if_unit_monster(unit):
                distance = Replayer.cal_distance(hero.pos, unit.pos)
                if distance < Replayer.ATTACK_UNIT_RADIUS:
                    nearby_enemy_units.append(unit)
        return nearby_enemy_units

    @staticmethod
    def get_nearby_monsters(state_info, hero_id):
        #TODO 考虑是否可见vis1表示下路阵营是否可见
        return None

    @staticmethod
    def if_near_tower(state_info, hero_state):
        for unit in state_info:
            if int(unit.unit_name) <= 26:
                if Replayer.cal_distance(unit.pos, hero_state.pos) < 7:     #根据配置得来
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
        distance = math.sqrt((pos1.x -pos2.x)*(pos1.x - pos2.x) + (pos1.y - pos2.y)*(pos1.y - pos2.y))/1000
        return distance

    @staticmethod
    def if_retreat(prev_pos, cur_pos, hero_name):
        if int(hero_name) <= 31 and cur_pos.x > prev_pos.x:
            return True
        if int(hero_name) > 31 and cur_pos.x < prev_pos.y:
            return True
        return False

    @staticmethod
    def guess_strategy(state_infos):
        # 根据英雄的位置和状态猜测他当之前一段时间内的策略层面的决定
        # 根据特殊事件来猜测玩家策略
        # 1. 攻击野怪
        # 2. 攻击兵线
        # 3. 攻击塔
        # 4. 周围有多少其它英雄，来区分支援，团战，gank
        # 5. 战斗撤退很难评估
        # 6. 埋伏的判断
        hero_strategies = []
        for hero in state_infos[0]:
            hero_strategy = HeroStrategy(hero.hero_name, [])
            hero_strategies.append(hero_strategy)
        strg_records = StrategyRecords(state_infos[0].battle_id, hero_strategies)

        prev_state = None
        for index, state_info in enumerate(state_infos):
            for hero in state_info.heros:
                # 首先拿英雄主动攻击信息
                att = state_info.get_hero_attack_info(hero.hero_name)
                if att is not None:
                    # 得到被攻击者信息
                    # 如果是野怪则确认是打野
                    # 如果是小兵则是兵线，还需要根据之前的走位来判断
                    # 如果是英雄，可能性有很多，1.兵线上的对抗，2.Gank，3.团战 4.防守, 5.支援
                    target = state_info.get_unit(att.defer)
                    if target is not None:
                        sa = StrategyAction(hero.hero_name, state_info.tick, hero.pos, ActionEnum.attack, target)
                        strg_records.add_hero_action(sa)
                    else:
                        target = state_info.get_hero(att.defer)
                        if target is not None:
                            sa = StrategyAction(hero.hero_name, state_info.tick, hero.pos, ActionEnum.attack, target)
                            strg_records.add_hero_action(sa)

                # 得到英雄被攻击信息
                hitted = state_info.get_hero_be_attacked_info(hero.hero_name)
                if len(hitted) > 0:
                    # 具体被谁攻击了的信息，交给后续判断逻辑去识别
                    hitted_action = StrategyAction(hero.hero_name, state_info.tick, hero.pos, ActionEnum.be_attacked, hitted)
                    strg_records.add_hero_action(hitted_action)

                # 检查可视信息变化情况，如果从对方不可视变成了可视，之后的行为决定了是战斗还是撤退
                # 如果是静立不动超过一段时间，且之后发生了战斗可以认为是在等待时机
                if prev_state is not None:
                    prev_hero = prev_state.get_hero(hero.hero_name)
                    if prev_state.vis2 != hero.vis2:
                        prev_vis = StrategyAction(prev_hero.hero_name, prev_state.tick, prev_hero.pos, ActionEnum.vis_change, prev_hero.vis2)
                        cur_vis = StrategyAction(hero.hero_name, cur_state.tick, hero.pos, ActionEnum.vis_change, hero.vis2)
                        strg_records.add_hero_action(prev_vis)
                        strg_records.add_hero_action(cur_vis)

                # 检查位移信息，接近防守塔的行为
                tower = Replayer.if_near_tower(state_info, hero)
                if tower is not None:
                    self_tower = Replayer.if_self_tower(tower, hero.hero_name)
                    action_type = ActionEnum.near_self_tower if self_tower else ActionEnum.near_enemy_tower
                    near_tower = StrategyAction(hero.hero_name, cur_state.tick, hero.pos, action_type, tower.unit_name)
                    strg_records.add_hero_action(near_tower)

                # 检查位移信息，查看是否在撤退
                # 我们首先将连续4s(后述8个)都在后撤的行为判定为撤退吧
                # 至于这个行为是不是真的retreat还需要根据之前是否有发生战斗来决定
                prev_hero = prev_state.get_hero(hero.hero_name)
                if_retreat = Replayer.if_retreat(prev_hero.pos, hero.pos, hero.hero_name)
                checked = 0
                while checked < 8 and index + checked < len(state_infos)-2:
                    cal_state = state_infos[index+checked]
                    cal_next_state = state_infos[index+checked+1]
                    cal_state_hero = cal_state.get_hero(hero.hero_name)
                    cal_next_state_hero = cal_next_state.get_hero(hero.hero_name)
                    if_retreat = Replayer.if_retreat(cal_state_hero.pos, cal_next_state_hero.pos, hero.hero_name)
                    if not if_retreat:
                        break
                if if_retreat and checked == 7:
                    retreat_action = StrategyAction(hero.hero_name, cur_state.tick, hero.pos, ActionEnum.retreat, None)
                    strg_records.add_hero_action(retreat_action)

                # 检查位移信息，是否在兵线

            prev_state = state_info

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
            skills = Replayer.get_skills_can_upgrade(hero)
            if len(skills) > 0:
                update_str = Replayer.build_action_command(hero.hero_name, 'UPDATE', {'skillid': str(skills[0])})
                action_strs.append(update_str)

            # 得到周围的英雄和敌人单位信息
            action_str = None
            nearby_enemy_heros = Replayer.get_nearby_enemy_heros(state_info, hero.hero_name)
            nearby_enemy_units = Replayer.get_nearby_enemy_units(state_info, hero.hero_name)
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
                    if hero.skills[skillid].canuse:
                        action_str = Replayer.build_action_command(hero.hero_name, 'CAST',
                                                                   {'skillid': str(skillid), 'tgtid': tgtid,
                                                                    'tgtpos': tgtpos.to_string(), 'fwd': fwd.to_string()})
                        break
                if action_str is None:
                    action_str = Replayer.build_action_command(hero.hero_name, 'ATTACK', {'tgtid': tgtid})
            # 在前1分钟，命令英雄到达指定地点
            elif Replayer.TICK_PER_STATE * 2 * 40 > int(tick) > 528:
                if hero.team == 0:
                    action_str = Replayer.build_action_command(hero.hero_name, 'MOVE', {'pos': '( -5000, -80, 0)'})
                else:
                    action_str = Replayer.build_action_command(hero.hero_name, 'MOVE', {'pos': '( 5000, -80, 0)'})
            else:
                action_str = Replayer.build_action_command(hero.hero_name, 'HOLD', {})

            action_strs.append(action_str)

        rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

if __name__ == "__main__":
    path = "C:/Users/Administrator/Desktop/zy2go/battle_logs/tempbattlelog.log"
    file = open(path, "r")
    lines = file.readlines()

    # for line in lines:
    #     bd_json = json.loads(line)
    #     battle_detail = BattleRoundDetail.decode(bd_json)
    #     model.remember(battle_detail)
    state_logs = []
    prev_state = None
    replayer = Replayer()
    for line in lines:
        if prev_state is not None and int(prev_state.tick) > 21510:
            i = 1

        cur_state = replayer.parse_state_log(line)

        if cur_state.tick == Replayer.TICK_PER_STATE:
            print "clear"
            prev_stat = None
        elif prev_stat is not None and prev_stat.tick + Replayer.TICK_PER_STATE > cur_state.tick:
            print "clear"
            prev_stat = None

        state_info = replayer.update_state_log(prev_state, cur_state)
        state_logs.append(state_info)
        prev_state = state_info

        rsp_str = Replayer.build_action_response(state_info)
        print(rsp_str)

    print(len(state_logs))