# -*- coding: utf8 -*-


# 这个计算引擎的作用是，根据当前状态和下一步英雄的行动，计算这一帧的整个游戏状态
# 需要考虑
# 1. 英雄的位移距离
# 2. 英雄的物理伤害，技能伤害，技能范围
# 3. 各种buff造成的影响
# 4. 小兵和塔的伤害
# 其中很多数据都无法做到精确计算，这里只是起到一个预估的效果。理想中，等自由2剥离出一个游戏引擎之后，应该可以直接替换这部分逻辑
# TODO buff信息需要考虑时长，目前没有时长信息
from model.buffenum import BuffEnum
from model.buffinfo import BuffInfo
from model.posstateinfo import PosStateInfo
from train.cmdactionenum import CmdActionEnum
import copy

from util.stateutil import StateUtil


class PlayEngine:
    @staticmethod
    def play_step(state_info, hero_actions):
        # 基本逻辑，如果英雄攻击了对方英雄，周围小兵会优先攻击英雄

        # 执行英雄行为

        # 执行小兵行为

        # 执行塔的行为

        # 更新Buff信息



    @staticmethod
    def play_hero_action(state_info, hero_info, hero_action):
        # 检查是否在眩晕状态
        buff_info = BuffInfo.if_unit_buff(state_info, hero_info.hero_name, BuffEnum.STUN)
        if buff_info is not None:
            return state_info

        # 检查英雄是否是移动
        if hero_action.action == CmdActionEnum.MOVE:
            hero_info.pos = PlayEngine.play_move(hero_info.pos, hero_action.fwd)
            state_info.update_hero(hero_info)
        # 物理攻击的话，暂时只执行一次
        # 这里不考虑是否可以攻击到，默认都可以
        elif hero_action.action == CmdActionEnum.ATTACK:
            state_info = PlayEngine.play_attack(state_info, hero_action.hero_name, hero_action.tgtid)
        # 使用技能
        # 技能的范围和伤害误差会更大
        # 技能都不考虑飞行延迟


    @staticmethod
    def play_skill(state_info, hero_action):
        # 目前只针对查尔斯
        hero_info = state_info.get_hero(hero_action.hero_name)
        if hero_info.cfg_id == '101':
            if hero_action.skillid == 1:
                # 飞镖技能伤害96+8*level，范围8000， 宽度500


    @staticmethod
    def find_skill_targets(state_info, attacker_info, tgt_pos, skill_length, skill_width, is_circle):
        if not is_circle:
            # 首先满足直线距离应该小于技能长度
            tgt_unit_list = [unit for unit in state_info.units if StateUtil.cal_distance2(attacker_info.pos, unit.pos) <= skill_length]
            tgt_hero_list = [hero for hero in state_info.heros if StateUtil.cal_distance2(attacker_info.pos, hero.pos) <= skill_length and hero.hero_name != attacker_info.hero_name]

            # 需要旋转坐标系 x1 = xcosa + ysina, y1 = ycosa - xsina
            # 或者按比例计算最大最下z值（相当于坐标系上的x）
            tgt_units = []
            for unit in tgt_unit_list:
                mid_x = attacker_info.pos.z + StateUtil.cal_distance2(attacker_info.pos, unit.pos) / StateUtil.cal_distance2(attacker_info.pos, tgt_pos) * (tgt_pos-attacker_info)
                if mid_x - skill_width/2 <= unit.x <= mid_x + skill_width/2:
                    tgt_units.append(unit)

            tgt_heros = []
            for hero in tgt_hero_list:
                mid_x = attacker_info.pos.z + StateUtil.cal_distance2(attacker_info.pos, hero.pos) / StateUtil.cal_distance2(attacker_info.pos, tgt_pos) * (tgt_pos-attacker_info)
                if mid_x - skill_width/2 <= hero.x <= mid_x + skill_width/2:
                    tgt_heros.append(hero)
            return tgt_units, tgt_heros

        else:
            # 根据tgt_pos


    @staticmethod
    def play_attack(state_info, attacker, defender):
        attacker_info = state_info.get_hero(attacker) if StateUtil.if_unit_hero(attacker) else state_info.get_unit(attacker)
        defender_info = state_info.get_hero(defender) if StateUtil.if_unit_hero(defender) else state_info.get_unit(defender)

        #TODO 计算最终伤害的公式很不清楚，需要后续核实。减伤比例为 防御/（防御+100）＝防御减伤，但是防御值怎么计算得来
        #TODO 只知道，一个技能打在小兵身上伤害会比打在英雄身上高很多
        if StateUtil.if_unit_hero(defender):
            hero_cfg_id = defender_info.cfg_id
            defend_value, mag_defend_value = PlayEngine.get_defend_value(hero_cfg_id, defender_info.level)
            dmg = attacker_info.attack * defend_value / (defend_value + 100)
            defender_info.hp = min(defender_info.hp - dmg, 0)
            state_info.update_hero(defender_info)
        else:
            dmg = attacker_info.attack
            defender_info.hp = min(defender_info.hp - dmg, 0)
            state_info.update_unit(defender_info)
        return state_info

    @staticmethod
    def play_move(pos, fwd, time_second=0.5):
        # 不考虑不可到达等问题
        return PosStateInfo(pos.x + time_second*fwd.x, pos.y + time_second*fwd.y, pos.z + time_second*fwd.z)


    @staticmethod
    def copy_state_info(state_info):
        return copy.deepcopy(state_info)


    @staticmethod
    def get_defend_value(hero_cfg_id, level):
        # 对于查尔斯
        if hero_cfg_id == '101':
            return 34 + (level-1) * 2, 34 + (level - 1)
        return None

