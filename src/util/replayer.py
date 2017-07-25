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

from hero_strategy.actionenum import ActionEnum
from hero_strategy.herostrategy import HeroStrategy
from hero_strategy.strategyaction import StrategyAction
from hero_strategy.strategyrecords import StrategyRecords
from src.model.stateinfo import StateInfo


class Replayer:
    @staticmethod
    def parse_state_log(json_str):
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
        for state_info in state_infos:
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
                        sa = StrategyAction(hero.hero_name, state_info.tick, hero.pos, ActionEnum.fight, target)
                        strg_records.add_hero_action(sa)
                    else:
                        target = state_info.get_hero(att.defer)
                        if target is not None:
                            sa = StrategyAction(hero.hero_name, state_info.tick, hero.pos, ActionEnum.fight, target)
                            strg_records.add_hero_action(sa)

                # 检查可视信息变化情况，如果从对方不可视变成了可视，之后的行为决定了是战斗还是撤退
                # 如果是静立不动超过一段时间，且之后发生了战斗可以认为是在等待时机
                if prev_state is not None:
                    prev_hero = prev_state.get_hero(hero.hero_name)
                    cur_hero = state_info.get_hero(hero.hero_name)
                    if prev_state.vis2 != cur_hero.vis2:
                        prev_vis = StrategyAction(prev_hero.hero_name, prev_state.tick, prev_hero.pos, ActionEnum.vis_change, prev_hero.vis2)
                        cur_vis = StrategyAction(cur_hero.hero_name)



            prev_state = state_info








if __name__ == "__main__":
    path = "/Users/sky4star/Github/zy2go/battle_logs/6442537685409333250.log"
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
        cur_state = replayer.parse_state_log(line)
        merged_state = replayer.update_state_log(prev_state, cur_state)
        state_logs.append(merged_state)
        prev_state = merged_state

    print state_logs.count()