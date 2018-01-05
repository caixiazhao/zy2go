# -*- coding: utf8 -*-


# 这个计算引擎的作用是，根据当前状态和下一步英雄的行动，计算这一帧的整个游戏状态
# 需要考虑
# 1. 英雄的位移距离
# 2. 英雄的物理伤害，技能伤害，技能范围
# 3. 各种buff造成的影响
# 4. 小兵和塔的伤害
# 其中很多数据都无法做到精确计算，这里只是起到一个预估的效果。理想中，等自由2剥离出一个游戏引擎之后，应该可以直接替换这部分逻辑
# TODO buff信息需要考虑时长，目前没有时长信息
from model.attackstateinfo import AttackStateInfo
from model.buffenum import BuffEnum
from model.buffinfo import BuffInfo
from model.posstateinfo import PosStateInfo
from train.cmdactionenum import CmdActionEnum
import copy

from util.stateutil import StateUtil


class PlayEngine:
    @staticmethod
    def play_step(state_info, heros, hero_actions):
        # 基本逻辑，如果英雄攻击了对方英雄，周围小兵会优先攻击英雄

        # 执行英雄行为
        for action in hero_actions:
            hero_info = state_info.get_hero(action.hero_name)
            PlayEngine.play_hero_action(state_info, action, hero_info)

        # 只考虑英雄附近的小兵
        played_units = []
        for hero_name in heros:
            hero_info = state_info.get_hero(hero_name)
            hero_action = PlayEngine.find_hero_action(hero_actions, hero_name)
            near_enemy_units = StateUtil.get_nearby_enemy_units(state_info, hero_name, StateUtil.LINE_MODEL_RADIUS)
            near_friend_units = StateUtil.get_nearby_friend_units(state_info, hero_name, StateUtil.LINE_MODEL_RADIUS)

            # 执行小兵行为
            for unit in near_enemy_units:
                if unit.unit_name not in played_units:
                    played_units.append(unit.unit_name)
                    state_info = PlayEngine.play_unit_action(state_info, unit, hero_info, hero_action, near_friend_units)

            for unit in near_friend_units:
                if unit.unit_name not in played_units:
                    played_units.append(unit.unit_name)
                    state_info = PlayEngine.play_unit_action(state_info, unit, hero_info, hero_action, near_enemy_units)

            # 执行塔的行为
            # 扩大塔的搜索范围
            nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(state_info, hero_name, StateUtil.LINE_MODEL_RADIUS + 5)
            if nearest_enemy_tower is not None and nearest_enemy_tower.unit_name not in played_units:
                played_units.append(nearest_enemy_tower.unit_name)
                state_info = PlayEngine.play_unit_action(state_info, nearest_enemy_tower, hero_info, hero_action, near_friend_units)

            # 更新Buff信息
            state_info = BuffInfo.update_unit_buffs(state_info, hero_name)

            # 更新血量每秒回血hprec
            if str(state_info.tick)[-3] == 0:
                for hero_name in heros:
                    hero_info = state_info.get_hero(hero_name)
                    hero_info.hp += hero_info.hprec

        hero_info1 = state_info.get_hero('27')
        hero_info2 = state_info.get_hero('28')
        return [state_info.tick, hero_info1.pos.to_string(), hero_info1.fwd.to_string(), hero_info1.hp], [hero_info2.pos.to_string(), hero_info2.fwd.to_string(), hero_info2.hp]

    @staticmethod
    def find_hero_action(hero_actions, hero_name):
        for action in hero_actions:
            if action.hero_name == hero_name:
                return action
        return None

    @staticmethod
    def play_unit_action(state_info, unit, hero_info, hero_action, near_enemy_units):
        #TODO 需要界定攻击英雄的小兵的范围
        # 最高优先级：如果英雄攻击了对方英雄，周围小兵会优先攻击英雄
        # 考虑攻击范围，当前默认都使用塔的攻击范围
        if PlayEngine.if_hero_attack_opponent(hero_action) \
                and StateUtil.cal_distance(hero_info.pos, unit.pos) <= StateUtil.TOWER_ATTACK_RADIUS:
            state_info = PlayEngine.play_attack(state_info, unit.unit_name, hero_action.hero_name)

        # 根据attack info来执行动作
        else:
            find_new_tgt = False
            att = state_info.get_attack_info(unit.unit_name)
            if att is not None:
                # 判断被攻击对象是否已经挂了
                defender = state_info.get_unit(att.defer)
                if defender is None or defender.hp <= 0:
                    find_new_tgt = True
                else:
                    state_info = PlayEngine.play_attack(state_info, unit.unit_name, att.defer)

            # 如果丢失对象，攻击最近的敌人
            # 为了节省计算量，我们只从英雄附近的小兵中寻找被攻击者，或者是英雄
            if att is None or find_new_tgt:
                tgt = PlayEngine.find_next_tgt(state_info, unit, near_enemy_units)
                if tgt is not None:
                    state_info = PlayEngine.play_attack(state_info, unit.unit_name, tgt)
        return state_info

    @staticmethod
    def find_next_tgt(state_info, unit, soldier_list):
        # 为了节省计算量，我们只从英雄附近的小兵中寻找被攻击者, 或者是英雄
        heros = StateUtil.get_heros_in_team(state_info, 1 - unit.team)
        hero = heros[0]
        min_dis = StateUtil.cal_distance2(hero.pos, unit.pos)

        tgt = hero.hero_name
        for soldier in soldier_list:
            dis = StateUtil.cal_distance2(soldier.pos, unit.pos)
            if dis < min_dis:
                tgt = soldier.unit_name
                min_dis = dis

        if min_dis <= StateUtil.TOWER_ATTACK_RADIUS * 1000:
            return tgt
        return None

    @staticmethod
    def play_hero_action(state_info, hero_action, hero_info):
        # 检查是否在眩晕状态
        buff_info = BuffInfo.if_unit_buff(state_info, hero_info.hero_name, BuffEnum.STUN)
        if buff_info is not None:
            return state_info

        # 检查英雄是否是移动
        # print('action', state_info.tick, hero_info.hero_name, hero_action.action, hero_action.skillid, hero_action.tgtid, hero_info.speed)
        if hero_action.action == CmdActionEnum.MOVE:
            hero_info.pos = PlayEngine.play_move(hero_info.pos, hero_action.fwd, hero_info)
            state_info.update_hero(hero_info)
        # 物理攻击的话，暂时只执行一次
        # 这里不考虑是否可以攻击到，默认都可以
        elif hero_action.action == CmdActionEnum.ATTACK:
            state_info = PlayEngine.play_attack(state_info, hero_action.hero_name, hero_action.tgtid)
        # 使用技能
        # 技能的范围和伤害误差会更大
        # 技能都不考虑飞行延迟
        elif hero_action.action == CmdActionEnum.CAST:
            state_info = PlayEngine.play_skill(state_info, hero_action)

        return state_info

    @staticmethod
    def play_skill(state_info, hero_action):
        # 目前只针对查尔斯
        #TODO 考虑技能等级，也会对伤害有影响
        hero_info = state_info.get_hero(hero_action.hero_name)
        if hero_info.cfg_id == '101':
            if hero_action.skillid == '1':
                # 飞镖技能伤害96 + 8*level + ?，范围8000， 宽度500
                # level用技能的等级代替
                #TODO 添加减速debuff
                dmg = 96 + 8 * hero_info.level
                tgt_units, tgt_heros = PlayEngine.find_skill_targets(state_info, hero_info, hero_action.tgtpos, 8000, 500, False)
                PlayEngine.update_tgt_hp(state_info, tgt_units, tgt_heros, dmg)
            elif hero_action.skillid == '2':
                # 突袭，跳跃范围伤害, 137 + 9*level + 50 * (skilllevel - 1)
                dmg = 137 + 9 * hero_info.level
                tgt_units, tgt_heros = PlayEngine.find_skill_targets(state_info, hero_info, hero_action.tgtpos, 6000, -1, True)
                PlayEngine.update_tgt_hp(state_info, tgt_units, tgt_heros, dmg)
            elif hero_action.skillid == '3':
                # 大招，对周围所有敌人造成伤害，231 + 10*level 范围3.5
                dmg = 240 + 10 * hero_info.level
                tgt_units, tgt_heros = PlayEngine.find_skill_targets(state_info, hero_info, hero_action.tgtpos, 3500, -1, True)
                PlayEngine.update_tgt_hp(state_info, tgt_units, tgt_heros, dmg)

        return state_info

    @staticmethod
    def update_tgt_hp(state_info, tgt_units, tgt_heros, dmg):
        # 更新单位血量
        for unit in tgt_units:
            unit.hp = max(unit.hp - dmg, 0)
            state_info.update_unit(unit)

        # 更新英雄血量
        for hero in tgt_heros:
            hero_dmg = PlayEngine.cal_hero_dmg(hero, dmg)
            hero.hp = max(hero.hp - hero_dmg, 0)
            state_info.update_hero(hero)

    # 暂时忽略穿透
    @staticmethod
    def cal_hero_dmg(hero_info, dmg):
        defend_value = PlayEngine.get_defend_value(hero_info.cfg_id, hero_info.level)
        defend_value = defend_value[0]
        dmg *= 1 - float(defend_value) / (defend_value + 100)
        return dmg

    @staticmethod
    def find_skill_targets(state_info, attacker_info, tgt_pos, skill_length, skill_width, is_circle):
        if not is_circle:
            # 首先满足直线距离应该小于技能长度
            tgt_unit_list = [unit for unit in state_info.units if StateUtil.cal_distance2(attacker_info.pos, unit.pos) <= skill_length and not StateUtil.if_unit_tower(unit.unit_name)]
            tgt_hero_list = [hero for hero in state_info.heros if StateUtil.cal_distance2(attacker_info.pos, hero.pos) <= skill_length and hero.hero_name != attacker_info.hero_name]

            # 需要旋转坐标系 x1 = xcosa + ysina, y1 = ycosa - xsina
            # 或者按比例计算最大最下z值（相当于坐标系上的x）
            tgt_units = []
            for unit in tgt_unit_list:
                mid_x = attacker_info.pos.z + StateUtil.cal_distance2(attacker_info.pos, unit.pos) / StateUtil.cal_distance2(attacker_info.pos, tgt_pos) * (tgt_pos.x-attacker_info.pos.x)
                if mid_x - skill_width/2 <= unit.pos.x <= mid_x + skill_width/2:
                    tgt_units.append(unit)

            tgt_heros = []
            for hero in tgt_hero_list:
                mid_x = attacker_info.pos.z + StateUtil.cal_distance2(attacker_info.pos, hero.pos) / StateUtil.cal_distance2(attacker_info.pos, tgt_pos) * (tgt_pos.x-attacker_info.pos.x)
                if mid_x - skill_width/2 <= hero.pos.x <= mid_x + skill_width/2:
                    tgt_heros.append(hero)
            return tgt_units, tgt_heros

        else:
            # 根据tgt_pos画圆，计算范围内的敌人
            # 攻击对象不是塔
            tgt_unit_list = [unit for unit in state_info.units if StateUtil.cal_distance2(tgt_pos, unit.pos) <= skill_length and not StateUtil.if_unit_tower(unit.unit_name)]
            tgt_hero_list = [hero for hero in state_info.heros if StateUtil.cal_distance2(tgt_pos, hero.pos) <= skill_length and hero.hero_name != attacker_info.hero_name]
            return tgt_unit_list, tgt_hero_list


    @staticmethod
    def play_attack(state_info, attacker, defender, time_second=0.5):
        attacker_info = state_info.get_hero(attacker) if StateUtil.if_unit_hero(attacker) else state_info.get_unit(attacker)
        defender_info = state_info.get_hero(defender) if StateUtil.if_unit_hero(defender) else state_info.get_unit(defender)

        #TODO 解决塔和小兵，还有英雄不同的攻击频率问题，有些攻击其实不是每次更新都需要触发的

        # 更新攻击信息，这个信息对下一帧的计算会起来指导作用
        # 如果已经存在一个，需要替换掉
        # 忽略技能id这个参数，因为这种情况下不会被使用到
        att = AttackStateInfo(attacker, defender, defender_info.pos, -1)
        state_info.update_attack_info(att)

        # 如果攻击者是小兵，为了简化，默认都可以攻击到英雄
        if StateUtil.if_unit_soldier(attacker_info.cfg_id) and StateUtil.if_unit_long_range_attack(attacker_info.cfg_id):
            # 更新位置信息
            attacker_info.pos = defender_info.pos
            state_info.update_unit(attacker_info)

        # 英雄攻击，需要考虑距离问题，还有追击的位移情况
        #TODO 这里的英雄位置，可能是移动之前的，也可能是移动之后的，其实需要分别处理。而且判断是否攻击到的条件太简单了
        elif StateUtil.if_unit_hero(attacker):
            dis = StateUtil.cal_distance2(attacker_info.pos, defender_info.pos)
            move_dis = attacker_info.speed * time_second
            if dis > move_dis:
                # 只移动，不攻击
                attacker_info.pos = PlayEngine.move_towards(attacker_info.pos, defender_info.pos, move_dis, dis)
                state_info.update_hero(attacker_info)
                return state_info
            else:
                attacker_info.pos = defender_info.pos
                state_info.update_hero(attacker_info)

        #TODO 计算最终伤害的公式很不清楚，需要后续核实。减伤比例为 防御/（防御+100）＝防御减伤，但是防御值怎么计算得来
        if StateUtil.if_unit_hero(defender):
            hero_cfg_id = defender_info.cfg_id
            # print('skill_level', defender_info.skill1_level, defender_info.skill2_level, defender_info.skill3_level)
            defend_value, mag_defend_value = PlayEngine.get_defend_value(hero_cfg_id, defender_info.level)
            dmg = attacker_info.att * defend_value / (defend_value + 100)
            defender_info.hp = max(defender_info.hp - dmg, 0)
            state_info.update_hero(defender_info)
        else:
            dmg = attacker_info.att
            defender_info.hp = max(defender_info.hp - dmg, 0)
            state_info.update_unit(defender_info)
        return state_info

    @staticmethod
    def play_move(pos, fwd, hero_info, time_second=0.5):
        # 不考虑不可到达等问题
        return PosStateInfo(pos.x + time_second * fwd.x * hero_info.speed / 1000, pos.y + time_second * fwd.y * hero_info.speed / 1000, pos.z + time_second * fwd.z * hero_info.speed / 1000)


    @staticmethod
    def copy_state_info(state_info):
        return copy.deepcopy(state_info)


    @staticmethod
    def get_defend_value(hero_cfg_id, level):
        # 对于查尔斯
        if hero_cfg_id == '101':
            return 34 + (level-1) * 2, 34 + (level-1)
        return 0

    @staticmethod
    def if_hero_attack_opponent(hero_action):
        if hero_action is None:
            return False
        if hero_action.tgtid is not None and StateUtil.if_unit_hero(hero_action.tgtid):
            return True
        return False

    @staticmethod
    def move_towards(start_pos, dest_pos, move_dis, distance):
        final_pos_x = start_pos.x + (dest_pos.x-start_pos.x) * move_dis / distance
        final_pos_z = start_pos.z + (dest_pos.y-start_pos.z) * move_dis / distance
        return PosStateInfo(final_pos_x, start_pos.y, final_pos_z)