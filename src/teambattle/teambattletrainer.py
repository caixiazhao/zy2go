#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as JSON

# 5v5团战控制器
# 需要完成以下任务
#   战斗开始升级英雄到指定级别，购买指定道具
#   两边英雄达到指定位置，目前可以先指定为中路河道
#   设置一个战斗范围，只有死亡和撤退可以脱离战斗范围（如何执行撤退？）
#   战斗中由模型给出每个英雄的行为
#   计算双方战斗得分

#   首先尝试的方案：
#   输入考虑添加其它人的行为
from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from model.stateinfo import StateInfo
from train.cmdactionenum import CmdActionEnum
from util.equiputil import EquipUtil
from util.httputil import HttpUtil
from util.stateutil import StateUtil
from random import randint
from time import gmtime, strftime


class TeamBattleTrainer:

    BATTLE_POINT_X = 0
    BATTLE_POINT_Z = -30000

    def __init__(self, battle_id):
        self.battle_id = battle_id
        save_dir = HttpUtil.get_save_root_path()
        self.state_cache = []
        self.heros = ['27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
        self.raw_log_file = open(save_dir + '/raw_' + str(battle_id) + '.log', 'w')

    def save_raw_log(self, raw_log_str):
        self.raw_log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + raw_log_str + "\n")
        self.raw_log_file.flush()

    def build_response(self, raw_state_str):
        print(raw_state_str)
        prev_state_info = self.state_cache[-1] if len(self.state_cache) > 0 else None
        response_strs = []

        # 解析客户端发送的请求
        obj = JSON.loads(raw_state_str)
        raw_state_info = StateInfo.decode(obj)
        state_info = StateUtil.update_state_log(prev_state_info, raw_state_info)

        # 重开时候会有以下报文  {"wldstatic":{"ID":9051},"wldruntime":{"State":0}}
        if raw_state_info.tick == -1:
            return {"ID": raw_state_info.battleid, "tick": -1}

        # 战斗前准备工作
        if len(self.state_cache) == 0:
            # 第一帧的时候，添加金钱和等级
            for hero in self.heros:
                add_gold_cmd = CmdAction(hero, CmdActionEnum.ADDGOLD, None, None, None, None, None, None, None)
                add_gold_cmd.gold = 5000
                add_gold_str = StateUtil.build_command(add_gold_cmd)
                response_strs.append(add_gold_str)

                add_lv_cmd = CmdAction(hero, CmdActionEnum.ADDLV, None, None, None, None, None, None, None)
                add_lv_cmd.lv = 10
                add_lv_str = StateUtil.build_command(add_lv_cmd)
                response_strs.append(add_lv_str)
        elif len(self.state_cache) > 1:
            # 第二帧时候开始，升级技能，购买装备，这个操作可能会持续好几帧
            for hero in self.heros:
                upgrade_cmd = self.upgrade_skills(state_info, hero)
                if upgrade_cmd is not None:
                    response_strs.append(upgrade_cmd)

                buy_cmd = self.buy_equip(state_info, hero)
                if buy_cmd is not None:
                    response_strs.append(buy_cmd)

        for hero in self.heros:
            # 启动模型规则为周围有敌方英雄
            near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero, StateUtil.LINE_MODEL_RADIUS)
            if len(near_enemy_heroes) == 0:
                # 移动到团站点附近，添加部分随机
                rdm_delta_x = randint(0, 1000)
                rdm_delta_z = randint(0, 1000)
                tgt_pos = PosStateInfo(TeamBattleTrainer.BATTLE_POINT_X + rdm_delta_x, 0, TeamBattleTrainer.BATTLE_POINT_Z + rdm_delta_z)
                move_action = CmdAction(hero, CmdActionEnum.MOVE, None, None, tgt_pos, None, None, None, None)
                mov_cmd_str = StateUtil.build_command(move_action)
                response_strs.append(mov_cmd_str)
            # else:
                # 启动模型决策

        # 添加记录到缓存中
        self.state_cache.append(state_info)

        # 返回结果给游戏端
        rsp_obj = {"ID": state_info.battleid, "tick": state_info.tick, "cmd": response_strs}
        rsp_str = JSON.dumps(rsp_obj)
        return rsp_str

    # def get_model_actions(self, state_info, hero):

    def upgrade_skills(self, state_info, hero_name):

        # 决定是否购买道具
        buy_action = EquipUtil.buy_equip(state_info, hero_name)
        if buy_action is not None:
            buy_str = StateUtil.build_command(buy_action)
            return buy_str

    def buy_equip(self, state_info, hero_name):
        # 如果有可以升级的技能，优先升级技能3
        hero = state_info.get_hero(hero_name)
        skills = StateUtil.get_skills_can_upgrade(hero)
        if len(skills) > 0:
            skillid = 3 if 3 in skills else skills[0]
            update_cmd = CmdAction(hero.hero_name, CmdActionEnum.UPDATE, skillid, None, None, None, None, None, None)
            update_str = StateUtil.build_command(update_cmd)
            return update_str




