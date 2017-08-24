#!/usr/bin/env python
# -*- coding: utf-8 -*-
from train.cmdactionenum import CmdActionEnum
from util.stateutil import StateUtil


class RewardUtil:

    def __init__(self):
        pass

    @staticmethod
    def if_cast_skill(state_infos, state_idx, hero_name, skillid):
        cur_state = state_infos[state_idx]
        cur_hero_action = cur_state.get_hero_action(hero_name)
        if cur_hero_action is not None and cur_hero_action.action == CmdActionEnum.CAST and int(
                cur_hero_action.skillid) == skillid:
            return True
        return False

    @staticmethod
    def if_skill_hit_hero(state_infos, state_idx, hero_name, skillid, rival_hero_name):
        # 稳妥起见，这里查看后几帧的伤害情况。
        for i in range(1, 3):
            state_info = state_infos[state_idx + i]
            for hit_info in state_info.hit_infos:
                if hit_info.atker == hero_name and hit_info.tgt == rival_hero_name:
                    # 识别技能编号
                    skill_idx = int(hit_info.skill)%100/10
                    if skill_idx == skillid:
                        return True
        return False


    @staticmethod
    def if_hero_dead(state_infos, state_idx, state_num, hero_name):
        for i in range(1, state_num+1):
            state_info = state_infos[state_idx + i]
            hero_info = state_info.get_hero(hero_name)
            if hero_info.hp <= 0:
                return True
        return False

    @staticmethod
    def if_hit_by_tower(state_infos, state_idx, state_num, hero_name):
        for i in range(state_num+1):
            # hit 有延迟
            state_info = state_infos[state_idx + i + 1]
            hit_names = state_info.get_hero_be_attacked_info(hero_name)
            for unit_name in hit_names:
                if StateUtil.if_unit_tower(unit_name):
                    return True
        return False

    @staticmethod
    def if_leave_linemodel_range(state_infos, state_idx, hero_name, line_index):
        if state_idx > 0:
            prev_state = state_infos[state_idx - 1]
            cur_state = state_infos[state_idx]
            next_state = state_infos[state_idx + 1]
            next_next_state = state_infos[state_idx + 2]

            # 进入模型选择区域后，下1~2帧立刻离开模型选择区域的，这种情况需要避免
            prev_hero_action = prev_state.get_hero_action(hero_name)
            cur_hero_action = cur_state.get_hero_action(hero_name)
            next_hero_action = next_state.get_hero_action(hero_name)
            next_next_hero_action = next_next_state.get_hero_action(hero_name)

            # 只有当前帧玩家有行动，且是移动，则我们给予一个差评
            # TODO 如果更严谨我们应该首先判断之前是不是在回城状态中，然后被打断了
            if prev_hero_action is None and cur_hero_action is not None and next_hero_action is None:
                return True
            elif prev_hero_action is None and cur_hero_action is not None and next_hero_action is not None and next_next_hero_action is None:
                return True
        return False

    @staticmethod
    def if_hero_leave_line(state_infos, state_idx, hero_name, line_index):
        if state_idx > 0:
            prev_state = state_infos[state_idx - 1]
            cur_state = state_infos[state_idx]

            # 离线太远就进行惩罚
            prev_hero = prev_state.get_hero(hero_name)
            cur_hero = cur_state.get_hero(hero_name)
            prev_in_line = StateUtil.if_in_line(prev_hero, line_index, 4000)
            cur_in_line = StateUtil.if_in_line(cur_hero, line_index, 4000)
            if prev_in_line >= 0 and cur_in_line == -1:
                return True
        return False

    # 是否在高血量时候回城
    @staticmethod
    def if_return_town_high_hp(state_infos, state_idx, hero_name, hp_ratio):
        cur_state = state_infos[state_idx]
        cur_hero = cur_state.get_hero(hero_name)
        cur_hero_action = cur_state.get_hero_action(hero_name)
        if cur_hero_action is not None and cur_hero_action.action == CmdActionEnum.CAST and int(
                cur_hero_action.skillid) == 6:
            if float(cur_hero.hp) / cur_hero.maxhp >= hp_ratio:
                return True
        return False

    # 是否回城被打断
    @staticmethod
    def if_return_town_break(state_infos, state_idx, hero_name):
        go_town_break = False
        cur_state = state_infos[state_idx]
        cur_hero = cur_state.get_hero(hero_name)
        cur_hero_action = cur_state.get_hero_action(hero_name)
        if cur_hero_action is not None and cur_hero_action.action == CmdActionEnum.CAST and int(
                cur_hero_action.skillid) == 6:
            # 开始回城，这时候需要检查后面一系列帧有没有进行其它的操作，以及有没有减血（被打断的情况）
            for i in range(1, 10):
                next_state = state_infos[state_idx + i]
                next_hero = next_state.get_hero(hero_name)
                next_hero_action = next_state.get_hero_action(hero_name)
                if next_hero_action is None or cur_hero_action.action != CmdActionEnum.CAST or int(
                        cur_hero_action.skillid) == 6:
                    go_town_break = True
                    break
                elif next_hero.hp < cur_hero.hp:
                    go_town_break = True
                    break
        return go_town_break
