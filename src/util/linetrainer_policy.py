#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 给模型添加一些固定套路，在训练中随机选择，希望模型可以学习到这些正确的处理问题方式
# 主要目的是加速模型的学习。另外有些行为模式（比如对方低血时候追击，附近没哟敌方英雄时候尽量快的推线等）似乎很难学习到
import math

from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from train.cmdactionenum import CmdActionEnum
from train.linemodel import LineModel
from util.replayer import Replayer
from util.stateutil import StateUtil
from random import randint

from common import cf as C

def LOG__(*l):
    if C.LOG['LINEMODEL_POLICY_ALL']:
        print(*l)

class LineTrainerPolicy:
    # 如果这个范围内没有英雄则会启动各种攻击小兵攻击塔策略
    RIVAL_TOWER_NEARBY_RADIUS = 10
    SAFE_RIVAL_HERO_DISTANCE = 11
    SKILL_RANGE_CHAERSI_SKILL3 = 2
    KEEP_AWAY_FROM_HERO_START_DISTANCE = 3

    @staticmethod
    def choose_action(state_info, action_ratios, hero_name, rival_hero, rival_near_units,
                      near_friend_units):
        hero_info = state_info.get_hero(hero_name)
        rival_hero_info = state_info.get_hero(rival_hero)

        original_max_q = max(action_ratios)
        original_selected = action_ratios.index(original_max_q)

        #TODO 注意这里的逻辑是只限于第一个塔的
        rival_near_tower = StateUtil.get_first_tower(state_info, rival_hero_info)
        rival_tower_distance = StateUtil.cal_distance(hero_info.pos, rival_near_tower.pos)

        # 如果附近没有敌方英雄，而且不在塔下
        # 攻击敌方小兵
        action = LineTrainerPolicy.policy_attack_rival_unit(hero_info, rival_hero_info, state_info, hero_name,
                                                            rival_near_units, rival_near_tower, near_friend_units)
        if action is not None:
            return action

        # 如果在塔附近，且周围没有友军，也没有敌方英雄，则直接撤退
        # 如果友方只剩下一个小兵，有一点点血，也开始撤退
        if rival_tower_distance <= LineTrainerPolicy.RIVAL_TOWER_NEARBY_RADIUS:
            if len(near_friend_units) == 0 or (len(near_friend_units) == 1 and near_friend_units[0].hp/float(near_friend_units[0].maxhp) <= 0.5):
                if rival_hero_info.hp <= 0 or StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos) >= LineTrainerPolicy.SAFE_RIVAL_HERO_DISTANCE:
                    LOG__("启动策略 有敌方塔且己方掩护不足时候撤退 " + hero_name)
                    return LineTrainerPolicy.policy_move_retreat(hero_info)

        # 如果附近没有敌方英雄，在敌方塔下，且有小兵掩护
        if rival_tower_distance <= LineTrainerPolicy.RIVAL_TOWER_NEARBY_RADIUS and len(near_friend_units) > 0:
            units_in_tower_range = LineTrainerPolicy.units_in_tower_range(near_friend_units, rival_near_tower.pos)
            if (rival_hero_info.hp <= 0 or StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos) >= LineTrainerPolicy.SAFE_RIVAL_HERO_DISTANCE) and \
                    rival_near_tower is not None and \
                    units_in_tower_range > 0:
                # 被塔攻击的情况下后撤
                if state_info.if_unit_attack_hero(rival_near_tower.unit_name, hero_name):
                    LOG__("启动策略 被塔攻击的情况下后撤 " + hero_name)
                    return LineTrainerPolicy.policy_move_retreat(hero_info)

                # 有敌方小兵先打小兵
                if len(rival_near_units) > 0:
                    action = LineTrainerPolicy.policy_attack_rival_unit(hero_info, rival_hero_info, state_info,
                                                    hero_name, rival_near_units, rival_near_tower, near_friend_units)
                    if action is not None:
                        LOG__("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，有敌方小兵先打小兵 " + hero_name)
                        return action

                # 掩护充足的情况下攻击对方塔
                if units_in_tower_range >= 2:
                    LOG__("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，掩护充足的情况下攻击对方塔 " + hero_name)
                    return LineTrainerPolicy.get_attack_tower_action(hero_name, hero_info, rival_near_tower)

                # 不足的情况下后撤（如果在塔的攻击范围内）
                if units_in_tower_range <= 2 and StateUtil.cal_distance(hero_info.pos, rival_near_tower.pos) <= StateUtil.TOWER_ATTACK_RADIUS:
                    LOG__("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，不足的情况下后撤（如果在塔的攻击范围内） " + hero_name)
                    return LineTrainerPolicy.policy_move_retreat(hero_info)

        #TODO 超低血量下撤退

        # 如果对方英雄血量高，且差距明显，不要接近对方英雄
        if hero_info.hp/float(hero_info.maxhp) <= 0.3 and \
           rival_hero_info.hp/float(rival_hero_info.maxhp) >= hero_info.hp/float(hero_info.maxhp) + 0.2:
            # 另外一个条件是双方应该目前有一定的距离
            heros_distance = StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos)
            if heros_distance >= LineTrainerPolicy.KEEP_AWAY_FROM_HERO_START_DISTANCE:
                LOG__('策略选择', state_info.battleid, hero_name, '差距明显情况下不要接近对方英雄')
                action_ratios = LineTrainerPolicy.keep_away_from(state_info, hero_info, rival_hero_info, action_ratios,
                                                                 rival_hero_info.pos, heros_distance)

        # 不应该贸然进入对方的塔下
        # 在一个扩大的范围下进行侦查
        if rival_tower_distance <= LineTrainerPolicy.RIVAL_TOWER_NEARBY_RADIUS+4:
            units_in_tower_range = LineTrainerPolicy.units_in_tower_range(near_friend_units, rival_near_tower.pos)
            if units_in_tower_range <= 2:
                LOG__('策略选择', state_info.battleid, hero_name, '检测会不会贸然进入对方的塔下')
                action_ratios = LineTrainerPolicy.keep_away_from(state_info, hero_info, rival_hero_info, action_ratios,
                                                                 rival_near_tower.pos, StateUtil.TOWER_ATTACK_RADIUS)

        # 大招的使用
        # 对于查尔斯，如果周围没有敌人则不应该使用大招
        action_ratios = LineTrainerPolicy.use_skill3_correctly(state_info, hero_info, rival_hero_info, rival_near_units, action_ratios)

        # 如果对方英雄血量很低，且不在塔下，且我方英雄血量较高
        if rival_hero_info.hp > 0 and rival_hero_info.hp / float(rival_hero_info.maxhp) <= 0.3 and \
           hero_info.hp / float(hero_info.maxhp) >= rival_hero_info.hp / float(
           rival_hero_info.maxhp) + 0.1 and \
           rival_tower_distance > LineTrainerPolicy.RIVAL_TOWER_NEARBY_RADIUS:
            # 选择模型分数较高的行为
            selected_skill = -1
            skill_score = -1
            LOG__('启动策略, 如果对方英雄血量很低，且不在塔下，且我方英雄血量较高, ', state_info.battleid, hero_name, rival_tower_distance)
            for i in range(4):
                action_id = 10 * i + 9
                if action_ratios[action_id] > skill_score:
                    skill_score = action_ratios[action_id]
                    selected_skill = i
            if selected_skill >= 0:
                LOG__("启动策略 如果对方英雄血量很低，且不在塔下，且我方英雄血量较高, 从技能中选择 ", hero_name, selected_skill, skill_score)
                return LineTrainerPolicy.get_attack_hero_action(state_info, hero_name, rival_hero, selected_skill)

        current_max_q = max(action_ratios)
        current_selected = action_ratios.index(current_max_q)
        if original_max_q != current_max_q:
            LOG__('策略选择', state_info.battleid, hero_name, '策略改变', original_selected, current_selected)
            if current_max_q == -1:
                return LineTrainerPolicy.policy_move_retreat(hero_info)
            else:
                return LineModel.select_actions(action_ratios, state_info, hero_name, rival_hero)
        return None

    @staticmethod
    def use_skill3_correctly(state_info, hero_info, rival_hero_info, rival_near_units, action_ratios):
        if hero_info.cfg_id == '101':
            rival_hero_dis = StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos)
            if rival_hero_dis > LineTrainerPolicy.SKILL_RANGE_CHAERSI_SKILL3:
                if LineTrainerPolicy.units_in_range(rival_near_units, hero_info.pos,
                                                    LineTrainerPolicy.SKILL_RANGE_CHAERSI_SKILL3) == 0:
                    LOG__('策略选择', state_info.battleid, hero_info.hero_name, '查尔斯大招不应该在没人的时候使用')
                    for i in range(38, 48):
                        action_ratios[i] = -1
        return action_ratios

    @staticmethod
    def keep_away_from(state_info, hero_info, rival_hero_info, action_ratios, danger_pos, danger_radius):
        changed = False
        maxQ = max(action_ratios)
        selected = action_ratios.index(maxQ)
        if maxQ == -1:
            return action_ratios
        for selected in range(len(action_ratios)):
            if action_ratios[selected] == -1:
                continue
            if selected < 8:
                fwd = StateUtil.mov(selected)
                tgtpos = PosStateInfo(hero_info.pos.x + fwd.x * 0.5 * hero_info.speed / 1000, hero_info.pos.y + fwd.y * 0.5 * hero_info.speed / 1000,
                                      hero_info.pos.z + fwd.z * 0.5 * hero_info.speed / 1000)
                if StateUtil.cal_distance(tgtpos, danger_pos) <= danger_radius:
                    LOG__('策略选择', state_info.battleid, hero_info.hero_name, '移动方向会进入危险区域', hero_info.pos.to_string(),
                          tgtpos.to_string())
                    action_ratios[selected] = -1
            elif selected < 18:  # 对敌英雄，塔，敌小兵1~8使用普攻， 针对近战英雄的检测
                if selected == 8:  # 敌方塔
                    LOG__('策略选择', state_info.battleid, hero_info.hero_name, '不要去攻击塔')
                    action_ratios[selected] = -1
                elif selected == 9:  # 敌方英雄
                    if StateUtil.cal_distance(rival_hero_info.pos, danger_pos) <= danger_radius:
                        LOG__('策略选择', state_info.battleid, hero_info.hero_name, '不要去近身攻击塔范围内的英雄')
                        action_ratios[selected] = -1
                else:  # 小兵
                    creeps = StateUtil.get_nearby_enemy_units(state_info, hero_info.hero_name)
                    n = selected - 10
                    tgt = creeps[n]
                    if StateUtil.cal_distance(tgt.pos, danger_pos) <= danger_radius:
                        LOG__('策略选择', state_info.battleid, hero_info.hero_name, '不要去近身攻击塔范围内的小兵')
                        action_ratios[selected] = -1
            elif hero_info.cfg_id == '101' and 28 <= selected < 38:  # 专门针对查尔斯的跳跃技能
                skillid = int((selected - 18) / 10 + 1)
                [tgtid, tgtpos] = LineModel.choose_skill_target(selected - 18 - (skillid - 1) * 10,
                                                                state_info, skillid,
                                                                hero_info.hero_name, hero_info.pos, rival_hero_info.hero_name)
                if tgtpos is not None:
                    if StateUtil.cal_distance(tgtpos, danger_pos) <= danger_radius:
                        LOG__('策略选择', state_info.battleid, hero_info.hero_name, '跳跃技能在朝着塔下的目标')
                        action_ratios[selected] = -1
        return action_ratios

    @staticmethod
    def units_in_range(units, pos, distance):
        num = 0
        for unit in units:
            if StateUtil.cal_distance(unit.pos, pos) <= distance:
                num += 1
        return num

    @staticmethod
    def units_in_tower_range(units, target_pos):
        num = 0
        for unit in units:
            if StateUtil.cal_distance(unit.pos, target_pos) <= StateUtil.TOWER_ATTACK_RADIUS:
                num += 1
        return num

    @staticmethod
    def policy_attack_rival_unit(hero_info, rival_hero_info, state_info, hero_name, rival_near_units, rival_near_tower,
                                 near_friend_units):
        # 如果附近没有敌方英雄，而且不在塔下，且有己方小兵
        # 攻击敌方小兵
        if (rival_hero_info.hp <= 0 or StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos) >= LineTrainerPolicy.SAFE_RIVAL_HERO_DISTANCE) and \
                        rival_near_tower is None and len(near_friend_units) > 0:
            # 优先攻击快没有血的
            for unit in rival_near_units:
                if unit.hp <= hero_info.att - 20:
                    action = LineTrainerPolicy.get_attack_unit_action(state_info, hero_name, unit.unit_name, 0)
                    LOG__("启动策略 如果附近没有敌方英雄，而且不在塔下，补兵 " + hero_name)
                    return action

            # 如果敌方小兵在攻击自己，后撤到己方的小兵后面
            for unit in rival_near_units:
                att = state_info.if_unit_attack_hero(unit.unit_name, hero_name)
                if att is not None:
                    # 优先物理攻击
                    retreat = LineTrainerPolicy.policy_move_retreat(hero_info)
                    LOG__("启动策略 被小兵攻击的情况下后撤 " + hero_name)
                    return retreat

            # 物理攻击，不攻击血量较少的，留给补刀
            # 选择距离较近的（离己方塔）
            rival_near_units_sorted = list(rival_near_units)
            basement_pos = StateUtil.get_basement(hero_info)
            rival_near_units_sorted.sort(key=lambda u: math.fabs(basement_pos.x - u.pos.x), reverse=False)
            for unit in rival_near_units_sorted:
                if unit.hp > hero_info.att * 3:
                    action = LineTrainerPolicy.get_attack_unit_action(state_info, hero_name, unit.unit_name, 0)
                    LOG__("启动策略 如果附近没有敌方英雄，而且不在塔下，攻击敌方小兵 " + hero_name)
                    return action
        return None

    @staticmethod
    def policy_move_retreat(hero_info):
        if hero_info.team == 0:
            mov_idx = 6
        else:
            mov_idx = 0
        fwd = StateUtil.mov(mov_idx)
        tgtpos = PosStateInfo(hero_info.pos.x + fwd.x * 15, hero_info.pos.y + fwd.y * 15, hero_info.pos.z + fwd.z * 15)
        action = CmdAction(hero_info.hero_name, CmdActionEnum.MOVE, None, None, tgtpos, None, None, mov_idx, None)
        return action

    @staticmethod
    def get_attack_tower_action(hero_name, hero_info, tower_unit):
        # 因为目前模型中侦测塔的范围较大，可能出现攻击不到塔的情况
        # 所以需要先接近塔
        # 使用tgtpos，而不是fwd。move命令中fwd坐标系比较奇怪
        if StateUtil.cal_distance(hero_info.pos, tower_unit.pos) > StateUtil.ATTACK_UNIT_RADIUS:
            fwd = tower_unit.pos.fwd(hero_info.pos)
            [fwd, output_index] = Replayer.get_closest_fwd(fwd)
            tgtpos = PosStateInfo(hero_info.pos.x + fwd.x * 15, hero_info.pos.y + fwd.y * 15,
                                  hero_info.pos.z + fwd.z * 15)
            LOG__("朝塔移动，", hero_name, "hero_pos", hero_info.pos.to_string(), "tower_pos", tower_unit.pos.to_string(),
                  "fwd", fwd.to_string(), "output_index", output_index)
            action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, tgtpos, None, None, output_index, None)
        else:
            action_idx = 11
            action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tower_unit.unit_name, None, None, None, action_idx, None)
        return action

    @staticmethod
    def get_self_cast_action(state_info, hero_name, rival_hero_name, skill_id):
        action_idx = 10 * skill_id + 8
        hero = state_info.get_hero(hero_name)
        tgtpos = hero.pos
        fwd = tgtpos.fwd(hero.pos)
        action = CmdAction(hero_name, CmdActionEnum.CAST, skill_id, rival_hero_name, tgtpos, fwd, None, action_idx, None)
        return action

    @staticmethod
    def get_attack_hero_action(state_info, hero_name, rival_hero_name, skill_id):
        action_idx = 10 * skill_id + 9
        if skill_id == 0:
            action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, rival_hero_name, None, None, None, action_idx, None)
        else:
            tgtpos = state_info.get_hero(rival_hero_name).pos
            hero = state_info.get_hero(hero_name)
            fwd = tgtpos.fwd(hero.pos)
            action = CmdAction(hero_name, CmdActionEnum.CAST, skill_id, rival_hero_name, tgtpos, fwd, None, action_idx, None)
        return action


    @staticmethod
    def get_attack_unit_action(state_info, hero_name, unit_name, skill_id):
        creeps = StateUtil.get_nearby_enemy_units(state_info, hero_name)
        unit_idx = [c.unit_name for c in creeps].index(unit_name)
        action_idx = unit_idx + 10 * skill_id + 10
        if skill_id >= 1:
            action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, unit_name, None, None, None, action_idx, None)
        else:
            tgtpos = creeps[unit_idx].pos
            hero = state_info.get_hero(hero_name)
            fwd = tgtpos.fwd(hero.pos)
            action = CmdAction(hero_name, CmdActionEnum.CAST, skill_id, unit_name, tgtpos, fwd, None, action_idx, None)
        return action

