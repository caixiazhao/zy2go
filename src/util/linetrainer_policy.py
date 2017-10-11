#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 给模型添加一些固定套路，在训练中随机选择，希望模型可以学习到这些正确的处理问题方式
# 主要目的是加速模型的学习。另外有些行为模式（比如对方低血时候追击，附近没哟敌方英雄时候尽量快的推线等）似乎很难学习到
from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from train.cmdactionenum import CmdActionEnum
from util.replayer import Replayer
from util.stateutil import StateUtil
from random import randint


class LineTrainerPolicy:
    SAFE_RIVAL_HERO_DISTANCE = 14

    @staticmethod
    def choose_action(state_info, action_ratios, hero_name, rival_hero, rival_near_units, rival_near_tower,
                      near_friend_units):
        hero_info = state_info.get_hero(hero_name)
        rival_hero_info = state_info.get_hero(rival_hero)

        # 如果附近没有敌方英雄，而且不在塔下
        # 攻击敌方小兵
        action = LineTrainerPolicy.policy_attack_rival_unit(hero_info, rival_hero_info, state_info, hero_name,
                                                            rival_near_units, rival_near_tower)
        if action is not None:
            print("启动策略 如果附近没有敌方英雄，而且不在塔下，攻击敌方小兵 " + hero_name)
            return action

        # 如果附近没有地方英雄，在敌方塔下，且有小兵掩护
        if rival_near_tower is not None and len(near_friend_units) > 0:
            units_in_tower_range = LineTrainerPolicy.units_in_tower_range(near_friend_units, rival_near_tower)
            if StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos) >= LineTrainerPolicy.SAFE_RIVAL_HERO_DISTANCE and \
                    rival_near_tower is not None and \
                    units_in_tower_range > 0:
                # 被塔攻击的情况下后撤
                if state_info.if_unit_attack_hero(rival_near_tower.unit_name, hero_name):
                    print("启动策略 被塔攻击的情况下后撤 " + hero_name)
                    return LineTrainerPolicy.policy_move_retreat(hero_info)

                # 有敌方小兵先打小兵
                if len(rival_near_units) >= 0:
                    action = LineTrainerPolicy.policy_attack_rival_unit(hero_info, rival_hero_info, state_info, hero_name, rival_near_units, rival_near_tower)
                    if action is not None:
                        print("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，有敌方小兵先打小兵 " + hero_name)
                        return action

                # 掩护充足的情况下攻击对方塔
                if units_in_tower_range >= 2:
                    print("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，掩护充足的情况下攻击对方塔 " + hero_name)
                    return LineTrainerPolicy.get_attack_tower_action(hero_name, hero_info, rival_near_tower)

                # 不足的情况下后撤（如果在塔的攻击范围内）
                if units_in_tower_range <= 1 and StateUtil.cal_distance(hero_info.pos, rival_near_tower.pos) <= StateUtil.TOWER_ATTACK_RADIUS:
                    print("启动策略 如果附近没有地方英雄，在敌方塔下，且有小兵掩护，不足的情况下后撤（如果在塔的攻击范围内） " + hero_name)
                    return LineTrainerPolicy.policy_move_retreat(hero_info)

        #TODO 如果对方英雄血量很低，且不在塔下，且我方英雄血量较高
        if rival_hero_info.hp/float(rival_hero_info.maxhp) <= 0.3 and \
           hero_info.hp/float(hero_info.maxhp) >= rival_hero_info.hp/float(rival_hero_info.maxhp) + 0.1 and \
           rival_near_tower is None:
            # 随机从技能中选择
            avail_skills = []
            for i in range(4):
                action_id = 10 * i + 9
                if action_ratios[action_id] > -1:
                    avail_skills.append(i)
            if len(avail_skills) > 0:
                skill_id = randint(0, len(avail_skills)-1)
                print("启动策略 如果对方英雄血量很低，且不在塔下，且我方英雄血量较高, 随机从技能中选择 " + hero_name)
                return LineTrainerPolicy.get_attack_hero_action(state_info, hero_name, rival_hero, skill_id)

        # 大招的使用
        return None

    @staticmethod
    def units_in_tower_range(units, tower):
        num = 0
        for unit in units:
            if StateUtil.cal_distance(unit.pos, tower.pos) <= StateUtil.TOWER_ATTACK_RADIUS:
                num += 1
        return num

    @staticmethod
    def policy_attack_rival_unit(hero_info, rival_hero_info, state_info, hero_name, rival_near_units, rival_near_tower):
        # 如果附近没有敌方英雄，而且不在塔下
        # 攻击敌方小兵
        if StateUtil.cal_distance(hero_info.pos, rival_hero_info.pos) >= LineTrainerPolicy.SAFE_RIVAL_HERO_DISTANCE and \
                        rival_near_tower is None:
            # 优先攻击快没有血的
            for unit in rival_near_units:
                if unit.hp <= 100:
                    action = LineTrainerPolicy.get_attack_unit_action(state_info, hero_name, unit.unit_name, 0)
                    return action

            # 如果敌方小兵在攻击自己，优先攻击
            for unit in rival_near_units:
                att = state_info.if_unit_attack_hero(unit.unit_name, hero_name)
                if att is not None:
                    # 优先物理攻击
                    action = LineTrainerPolicy.get_attack_unit_action(state_info, hero_name, unit.unit_name, 0)
                    return action

            # 物理攻击，不攻击血量较少的，留在补刀
            for unit in rival_near_units:
                if unit.hp > 250:
                    action = LineTrainerPolicy.get_attack_unit_action(state_info, hero_name, unit.unit_name, 0)
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
        if StateUtil.cal_distance(hero_info.pos, tower_unit.pos) > StateUtil.ATTACK_UNIT_RADIUS:
            fwd = tower_unit.pos.fwd(hero_info.pos)
            [fwd, output_index] = Replayer.get_closest_fwd(fwd)
            action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None, output_index, None)
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
        if skill_id >= 1:
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

