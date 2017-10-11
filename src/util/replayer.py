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
import math

from hero_strategy.actionenum import ActionEnum
from hero_strategy.herostrategy import HeroStrategy
from hero_strategy.strategyaction import StrategyAction
from hero_strategy.strategyrecords import StrategyRecords
from model.cmdaction import CmdAction
from model.skillcfginfo import SkillTargetEnum
from train.cmdactionenum import CmdActionEnum
from util.skillutil import SkillUtil
from util.stateutil import StateUtil


class Replayer:
    @staticmethod
    # 推测玩家在每一帧中的行为
    # 注：移动方向的推测怎么算
    # 计算逻辑应该是，查看下一帧中的attackinfo，其中记录的是当前帧玩家的行动。
    # 这里计算的是prev_state_info中的玩家行为，也就是根据prev_state_info来计算当前状况，从state_info得到玩家在之前的实际行为，
    # 然后根据next_state来找到hitinfo
    # TODO 没有解决朝指定点释放的问题，action中的output_index没法指定。另外目前模型也学不会这个场景
    def guess_player_action(prev_state_info, state_info, next_state_info, next_next_state_info, hero_name, rival_hero_name):
        #针对每一帧，结合后一帧信息，判断英雄在该帧的有效操作
        #仅对于一对一线上模型有效
        #技能>攻击>走位
        #技能：检查cd和mp变化，hitstateinfo，attackstateinfo，dmgstateinifo，回推pos，fwd，tgt，selected
        #攻击：检查hit，damage，attack
        #检查pos变化

        prev_hero = prev_state_info.get_hero(hero_name)
        prev_viral_hero = prev_state_info.get_hero(rival_hero_name)
        current_hero = state_info.get_hero(hero_name)

        hero_attack_info = state_info.get_hero_attack_info(hero_name)
        if hero_attack_info is not None:
            skill = hero_attack_info.skill

            # 看十位来决定技能id
            skillid = int(hero_attack_info.skill % 100 / 10)
            tgtid = int(hero_attack_info.defer) if (hero_attack_info.defer is not None and hero_attack_info.defer != 'None') else 0
            tgtpos = hero_attack_info.tgtpos

            # 回城
            if hero_attack_info.skill == 10000:
                action = CmdAction(hero_name, CmdActionEnum.CAST, 6, None, None, None, None, 49, None)
                return action
            # 普攻，不会以自己为目标
            output_idx = None
            if skillid == 0:
                # 打塔
                if StateUtil.if_unit_tower(tgtid):
                    output_idx = 8
                # 普通攻击敌方英雄
                elif tgtid == prev_viral_hero.hero_name:  # 普通攻击敌方英雄
                    output_idx = 9
                # 普通攻击敌方小兵
                elif tgtid != 0:
                    creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                    n = len(creeps)
                    for i in range(n):
                        if creeps[i].unit_name == str(tgtid):
                            output_idx = i + 10
                # attacinfo里没有目标，从hit里找目标
                elif tgtid == 0:
                    # hitinfo 和 dmginfo都有延迟，尤其是超远距离的攻击技能
                    hit_infos = state_info.get_hero_hit_with_skill(hero_name, skill)
                    hit_infos.extend(next_state_info.get_hero_hit_with_skill(hero_name, skill))
                    if len(hit_infos) > 0:
                        # 首先检查是否敌方英雄被击中，这种优先级最高
                        if rival_hero_name in [hit.tgt for hit in hit_infos]:
                            output_idx = 9
                        else:
                            # 找到被攻击者中血量最少的，认为是目标对象
                            tgtid_list = [state_info.get_obj(hit.tgt) for hit in hit_infos]
                            tgt_unit = min(tgtid_list, key=lambda x: x.hp)

                            if StateUtil.if_unit_tower(tgt_unit.unit_name):
                                output_idx = 8
                            else:
                                # 从英雄附近的小兵中，检索它的编号
                                # 注：极端情况下有可能丢失，比如在这0.5秒钟内，英雄接近了小兵并进行了攻击
                                # 扩大搜索的范围
                                creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name,
                                                                          max_distance=StateUtil.ATTACK_HERO_RADIUS+2)
                                for i in range(len(creeps)):
                                    if creeps[i].unit_name == tgtid:
                                        output_idx = i + 10
                if output_idx is not None:
                    action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, tgtpos, None, None,
                                       output_idx, None)
                    return action
            # 使用技能，不考虑以敌方塔为目标（若真以敌方塔为目标则暂时先不管吧，现在的两个英雄技能都对建筑无效）
            # TODO 暂时忽略技能为方向/范围型并且放空的情况(部分技能无任何目标，tgt为0)。这种情况下应该会有个pos记录释放点，后续可以考虑如何学习
            else:
                # 对自身施法
                if tgtid == int(hero_name):  # or (tgtid=='0' and Replayer.skill_tag[skillid]==1):
                    tgtpos = prev_hero.pos
                    output_idx = 8 + skillid * 10
                # 对敌方英雄施法
                elif tgtid == int(rival_hero_name):
                    tgtpos = prev_viral_hero.pos
                    output_idx = 9 + skillid * 10
                # 对小兵施法
                elif tgtid != 0 and not StateUtil.if_unit_tower(tgtid):
                    creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                    n = len(creeps)
                    for i in range(n):
                        if creeps[i].unit_name == str(tgtid):
                            output_idx = i + skillid * 10 + 10
                # attacinfo里没有目标，从hit里找目标
                elif tgtid == 0:
                    # 远程技能的伤害延迟可能会比较长
                    hit_infos = state_info.get_hero_hit_with_skill(hero_name, skill)
                    hit_infos.extend(next_state_info.get_hero_hit_with_skill(hero_name, skill))
                    hit_infos.extend(next_next_state_info.get_hero_hit_with_skill(hero_name, skill))

                    if len(hit_infos) > 0:
                        # 首先检查是否敌方英雄被击中，这种优先级最高
                        if rival_hero_name in [hit.tgt for hit in hit_infos]:
                            tgtid = rival_hero_name
                            output_idx = 9 + skillid * 10
                        else:
                            # 找到被攻击者中血量最少的，认为是目标对象
                            tgtid_list = [state_info.get_obj(hit.tgt) for hit in hit_infos]
                            tgt_unit = min(tgtid_list, key=lambda x: x.hp)

                            # 从英雄附近的小兵中，检索它的编号
                            # 注：极端情况下有可能丢失，比如在这0.5秒钟内，英雄接近了小兵并进行了攻击
                            creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                            for i in range(len(creeps)):
                                if creeps[i].unit_name == tgt_unit.unit_name:
                                    tgtid = creeps[i].unit_name
                                    output_idx = i + 10 + skillid * 10

                # 组装结果
                if output_idx is not None:
                    action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                       tgtpos, None, None, output_idx, None)
                    return action
                # 任然没有hit，技能空放
                if tgtid == 0:
                    # attackinfo里没有攻击目标id，只有坐标，根据位置找最近的目标作为输出
                    if tgtpos != None:
                        search_radius = 1
                        # 首先寻找目标为对方英雄, 目前，如果在范围内有敌人英雄，选第一个作为主目标
                        nearby_rival_heros = StateUtil.get_nearby_enemy_heros(prev_state_info, hero_name, search_radius)
                        if len(nearby_rival_heros) > 0:
                            tgtid = nearby_rival_heros[0].hero_name
                            output_idx = 9 + skillid * 10
                        else:
                            # 其次检查是否可以释放给自己
                            skill_info = SkillUtil.get_skill_info(prev_hero.cfg_id, skillid)
                            if skill_info is not None:
                                if skill_info.cast_target != SkillTargetEnum.rival:
                                    tgtid = hero_name
                                    output_idx = 8 + skillid * 10
                                # 最后检查是否可以释放给小兵
                                else:
                                    nearby_soldiers = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name, search_radius)
                                    if len(nearby_soldiers) > 0:
                                        target_unit = min(nearby_soldiers, key=lambda u: u.hp)
                                        for i in range(len(nearby_soldiers)):
                                            if nearby_soldiers[i].unit_name == target_unit.unit_name:
                                                tgtid = nearby_soldiers[i].unit_name
                                                output_idx = i + 10 + skillid * 10
                    # 组装结果
                    if output_idx is not None:
                        action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                           tgtpos, None, None, output_idx, None)
                        return action
                    else:  # 真的技能空放了
                        action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, prev_hero.pos, None, None, 48,
                                           None)
                        return action
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, prev_hero.pos, None, None, 48, None)
                return action
        # 没有角色进行攻击或使用技能，英雄在移动或hold
        if current_hero.pos.x != prev_hero.pos.x or current_hero.pos.z != prev_hero.pos.z or current_hero.pos.y != prev_hero.pos.y:  # 移动
            fwd = current_hero.pos.fwd(prev_hero.pos)
            [fwd, output_index] = Replayer.get_closest_fwd(fwd)
            action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None, output_index, None)
            return action
        else:  # hold
            action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, prev_hero.pos, None, None, 48, None)
            return action

    @staticmethod
    def get_closest_fwd(fwd):
        maxcos=-1
        output_index=0
        output_fwd=fwd
        for i in range(8):
            fwd1=StateUtil.mov(i)
            a=fwd.x*fwd.x+fwd.z*fwd.z
            b=fwd1.x*fwd1.x+fwd1.z*fwd1.z
            cos=(fwd.x*fwd1.x+fwd.z*fwd1.z)/(math.sqrt(a)*math.sqrt(b))
            if cos>maxcos:
                maxcos=cos
                output_index=i
                output_fwd=fwd1
        return [output_fwd, output_index]

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