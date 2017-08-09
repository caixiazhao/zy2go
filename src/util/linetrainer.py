#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 对线模型训练中控制英雄(们)的行为

import json as JSON

from hero_strategy.actionenum import ActionEnum
from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
from util.stateutil import StateUtil


class LineTrainer:
    def __init__(self):
        self.hero_strategy = {}

    # 双方英雄集中到中路中间区域，进行对线
    # 一方英雄回城之后，负责等他满血后回到对战区
    def build_hero_response(self, state_info, line_model, hero_name):
        #battle_id = state_info.battleid
        #tick = state_info.tick

        action_strs = []
        for hero in state_info.heros:
            if hero.hero_name==hero_name:
                break

        # 如果有可以升级的技能，直接选择第一个升级
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            update_str = StateUtil.build_action_command(hero.hero_name, 'UPDATE', {'skillid': str(skills[0])})
            action_strs.append(update_str)
            #todo: 需要把升级append到actions吗？（对于模型会保存action信息到状态帧中）

        if StateUtil.if_hero_at_basement(hero) and hero.hp == hero.maxhp:
            self.hero_strategy[hero.hero_name] = ActionEnum.line_1

        # 开始根据策略决定当前的行动
        # 对线情况下，首先拿到兵线，朝最前方的兵线移动
        # 如果周围有危险（敌方单位）则启动对线模型
        near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        near_enemy_tower = StateUtil.get_nearby_enemy_units(state_info, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
        if len(near_enemy_heroes) == 0 and len(near_enemy_units) == 0 and len(near_enemy_tower) == 0:
            # 跟兵线
            if hero.hero_name in self.hero_strategy and self.hero_strategy[hero.hero_name] == ActionEnum.line_1:
                solider_lines = StateUtil.get_solider_lines(state_info, 1, hero.team)
                if len(solider_lines) == 0:
                    action_str = StateUtil.build_action_command(hero.hero_name, 'HOLD', {})
                    #todo: 需不需要reward
                    action_strs.append(action_str)
                    #todo:这边需要给state.actions append 对应的 action 不？
                else:
                    # 得到最前方的兵线位置
                    front_point = solider_lines[-1]
                    print('front_point, team:%s, line:%s, wave:%s, units:%s' % (front_point.team_id, front_point.line_index, len(solider_lines), len(front_point.units)))
                    move_action = CmdAction(hero.hero_name, CmdActionEnum.MOVE, None, None, front_point.pos, None, None, None, None)
                    #todo:需不需要reward
                    action_str = StateUtil.build_command(move_action)
                    # action_str = StateUtil.build_action_command(hero.hero_name, 'MOVE', {'pos': '( 5000, -80, 0)'})
                    action_strs.append(action_str)
                    #todo:这里也是actions.append(action)的问题
        else:
            # 使用模型进行决策
            print('line model decides')
            rival_hero = '28' if hero.hero_name == '27' else '27'
            action = line_model.get_action(state_info, hero.hero_name, rival_hero)
            #todo：这里没有reward
            action_str = StateUtil.build_command(action)
            action_strs.append(action_str)

            # 保存action信息到状态帧中
            state_info.actions.append(action)

        #rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        #rsp_str = JSON.dumps(rsp_obj)
        #return rsp_str
        return action_strs

    def build_EVE_response(self,state_info, line_model):
        #完成之前的 build_heros_response() 的功能
        battle_id = state_info.battleid
        tick = state_info.tick
        action_strs=[]
        for hero in state_info.heros:
            action=self.build_hero_response(state_info,line_model,hero.hero_name)
            action_strs=action_strs+action
        rsp_obj={"ID": battle_id, "tick":tick, "cmd":action_strs}
        rsp_str=JSON.dump(rsp_obj)
        return rsp_str



    def build_PVE_response(self,state_info, line_model):
        # 仅生成敌方英雄的action，不对己方英雄做任何指令
        battle_id = state_info.battleid
        tick = state_info.tick
        action_strs = []

        action = self.build_hero_response(state_info, line_model, "28")
        action_strs = action_strs + action
        rsp_obj = {"ID": battle_id, "tick": tick, "cmd": action_strs}
        rsp_str = JSON.dump(rsp_obj)
        return rsp_str

