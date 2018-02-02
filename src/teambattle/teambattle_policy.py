from model.cmdaction import CmdAction
from model.posstateinfo import PosStateInfo
from model.skillcfginfo import SkillTargetEnum
from model.stateinfo import StateInfo
from teambattle.team_ppocache import TEAM_PPO_CACHE
from teambattle.teambattle_input import TeamBattleInput
from teambattle.teambattle_util import TeamBattleUtil
from train.cmdactionenum import CmdActionEnum
from util.equiputil import EquipUtil
from util.httputil import HttpUtil
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from time import gmtime, strftime
import numpy as np
from random import shuffle, randint


class TeamBattlePolicy:
    # 如果这个范围内没有英雄则会启动各种攻击小兵攻击塔策略
    RIVAL_TOWER_NEARBY_RADIUS = 10
    SAFE_RIVAL_HERO_DISTANCE = 11
    SKILL_RANGE_CHAERSI_SKILL3 = 2
    KEEP_AWAY_FROM_HERO_START_DISTANCE = 3

    def choose_action(state_info, selected_skill, hero):
        hero_name = hero
        hero_info = state_info.get_hero(hero_name)
        action_name = ""
        near_enemy_heroes = StateUtil.get_nearby_enemy_heros(state_info, hero_name)
        if near_enemy_heroes is not None:
            for enemy in near_enemy_heroes:
                if enemy.hp > 0 and enemy.hp / float(enemy.maxhp) <= 0.3 and \
                                        hero_info.hp / float(hero_info.maxhp) >= enemy.hp / float(
                            enemy.maxhp) + 0.1:
                    print("启动策略 如果对方英雄血量很低，且我方英雄血量较高, 从技能中选择 ", hero_name, selected_skill)
                    if selected_skill == 0:
                        action_name = "Attack"
                    else:
                        action_name = "Skill"

                    return TeamBattlePolicy.get_attack_hero_action(state_info, hero_name, enemy, selected_skill), action_name

                if hero_info.hp / float(hero_info.maxhp) <= 0.3 and \
                                        enemy.hp / float(enemy.maxhp) >= hero_info.hp / float(
                            hero_info.maxhp) + 0.2:
                    # 另外一个条件是双方应该目前有一定的距离
                    heros_distance = StateUtil.cal_distance(hero_info.pos, enemy.pos)
                    if heros_distance >= TeamBattlePolicy.KEEP_AWAY_FROM_HERO_START_DISTANCE:
                        print('策略选择', state_info.battleid, hero_name, '差距明显情况下不要接近对方英雄')
                        near_friend_heroes = StateUtil.get_nearby_friend_units(state_info, hero_name)
                        if near_friend_heroes is not None:
                            for friend in near_friend_heroes:
                                action_name = 'Move'
                                return TeamBattlePolicy.policy_move_friend(hero_info, friend) ,action_name
        return None ,None



    def get_attack_hero_action(state_info, hero_name, rival_hero, skill_id):
        action_idx = 10 * skill_id + 9
        if skill_id == 0:
            action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, rival_hero.hero_name, None, None, None, action_idx, None)
        else:
            tgtpos = rival_hero.pos
            hero = state_info.get_hero(hero_name)
            fwd = tgtpos.fwd(hero.pos)
            action = CmdAction(hero_name, CmdActionEnum.CAST, skill_id, rival_hero.hero_name, tgtpos, fwd, None, action_idx, None)
        return action

    def policy_move_friend(hero_info, friend_hero):
        if hero_info.team == 0:
            mov_idx = 6
        else:
            mov_idx = 0
        fwd = StateUtil.mov(mov_idx)
        PosStateInfo(hero_info.pos.x + fwd.x * 0.5, hero_info.pos.y + fwd.y * 0.5, hero_info.pos.z + fwd.z * 0.5)
        tgtpos = friend_hero.pos
        action = CmdAction(hero_info.hero_name, CmdActionEnum.MOVE, None, None, tgtpos, None, None, mov_idx, None)
        return action