#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
from util.stateutil import StateUtil
# import sys
#
# import imp
# imp.reload(sys)
# #python 3 version
# #reload(sys)
# sys.setdefaultencoding('utf8')

class LineTrainer:
    TOWN_HP_THRESHOLD = 0.3

    def __init__(self):
        self.hero_strategy = {}

    # 双方英雄集中到中路中间区域，进行对线
    # 一方英雄回城之后，负责等他满血后回到对战区
    def build_response(self, state_info, prev_state_info, line_model, hero_names=None):

        battle_id = state_info.battleid
        tick = state_info.tick
        action_strs=[]

        if hero_names is None:
            hero_names = [hero.hero_name for hero in state_info.heros]
        for hero_name in hero_names:
            hero = state_info.get_hero(hero_name)

            # 如果有可以升级的技能，直接选择第一个升级
            skills = StateUtil.get_skills_can_upgrade(hero)
            if len(skills) > 0:
                update_str = StateUtil.build_action_command(hero.hero_name, 'UPDATE', {'skillid': str(skills[0])})
                action_strs.append(update_str)

            # 检查周围状况
            near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
            near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
            nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)

            # 回城相关逻辑
            # 如果在回城中且没有被打断则继续回城，什么也不用返回
            if prev_state_info is not None:
                prev_hero = prev_state_info.get_hero(hero.hero_name)
                if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing and prev_hero.hp <= hero.hp \
                        and not StateUtil.if_hero_at_basement(hero):
                    print('回城中，继续回城')
                    continue

            # 处在少血状态是，且周围没有地方单位的情况下选择回城
            if len(near_enemy_heroes) == 0 and len(near_enemy_units) == 0 and nearest_enemy_tower is None:
                if hero.hp/float(hero.maxhp) < LineTrainer.TOWN_HP_THRESHOLD:
                    print('策略层：回城')
                    # 检查英雄当前状态，如果在回城但是上一帧中受到了伤害，则将状态设置为正在回城，开始回城
                    if self.hero_strategy[hero.hero_name] == ActionEnum.town_ing:
                        if prev_hero.hp > hero.hp:
                            town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, None, None, None, None, None, None)
                            action_str = StateUtil.build_command(town_action)
                            action_strs.append(action_str)
                    # 检查英雄当前状态，如果不在回城，则将状态设置为正在回城，开始回城
                    elif self.hero_strategy[hero.hero_name] != ActionEnum.town_ing:
                        self.hero_strategy[hero.hero_name] = ActionEnum.town_ing
                        town_action = CmdAction(hero.hero_name, CmdActionEnum.CAST, 6, None, None, None, None, None, None)
                        action_str = StateUtil.build_command(town_action)
                        action_strs.append(action_str)

                    # 无论上面怎么操作，玩家下面的动作应该都是在回城中，所以跳过其它的操作
                    continue

            # 处在泉水之中的时候设置策略层为吃线
            if StateUtil.if_hero_at_basement(hero):
                if hero.hp < hero.maxhp:
                    continue

            # 开始根据策略决定当前的行动
            # 对线情况下，首先拿到兵线，朝最前方的兵线移动
            # 如果周围有危险（敌方单位）则启动对线模型
            # 如果周围有小兵或者塔，需要他们都是在指定线上的小兵或者塔
            line_index = 1
            near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
            nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)
            if len(near_enemy_heroes) == 0 and len(near_enemy_units_in_line) == 0 and len(nearest_enemy_tower_in_line) == 0:
                self.hero_strategy[hero.hero_name] = ActionEnum.line_1
                print("策略层：因为附近没有指定兵线的敌人所以开始吃线")
                # 跟兵线
                front_soldier = StateUtil.get_frontest_soldier_in_line(state_info, line_index, hero.team)
                if front_soldier is None:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'HOLD', {})
                    action_strs.append(action_str)
                else:
                    # 得到最前方的兵线位置
                    move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, front_soldier.pos, None, None, None, None)
                    action_str = StateUtil.build_command(move_action)
                    action_strs.append(action_str)
            else:
                # 使用模型进行决策
                self.hero_strategy[hero.hero_name] = ActionEnum.line_model
                enemies = []
                enemies.extend((hero.hero_name for hero in near_enemy_heroes))
                enemies.extend((unit.unit_name for unit in near_enemy_units))
                if nearest_enemy_tower is not None:
                    enemies.append(nearest_enemy_tower.unit_name)
                print('对线模型决策，因为周围有敌人：' + ' ,'.join(enemies))

                # 目前对线只涉及到两名英雄
                rival_hero = '28' if hero.hero_name == '27' else '27'
                action = line_model.get_action(state_info, hero.hero_name, rival_hero)
                action_str = StateUtil.build_command(action)
                action_strs.append(action_str)

                # 如果是要求英雄施法回城，更新英雄状态，这里涉及到后续多帧是否等待回城结束
                if action.action == CmdActionEnum.CAST and action.skillid == 6:
                    print("英雄$s释放了回城" % hero_name)
                    self.hero_strategy[hero.hero_name] = ActionEnum.town_ing

                # 保存action信息到状态帧中
                state_info.actions.append(action)
        rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

