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
from model.skillcfginfo import SkillCfgInfo
from model.stateinfo import StateInfo
from train.linemodel import LineModel
from util.jsonencoder import ComplexEncoder
from util.linetrainer import LineTrainer
from util.skillutil import SkillUtil
from util.stateutil import StateUtil
from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
from model.fwdstateinfo import FwdStateInfo
import math
from time import gmtime, strftime
from datetime import datetime

class Replayer:
    @staticmethod
    # 推测玩家在每一帧中的行为
    # 注：移动方向的推测怎么算
    # TODO 没有解决朝指定点释放的问题，action中的output_index没法指定。另外目前模型也学不会这个场景
    def guess_player_action(prev_state_info, state_info, hero_name):
        #针对每一帧，结合后一帧信息，判断英雄在该帧的有效操作
        #仅对于一对一线上模型有效
        #技能>攻击>走位
        #技能：检查cd和mp变化，hitstateinfo，attackstateinfo，dmgstateinifo，回推pos，fwd，tgt，selected
        #攻击：检查hit，damage，attack
        #检查pos变化

        for temphero in prev_state_info.heros:
            if temphero.hero_name==hero_name:
                hero_prev=temphero
            else:
                hero_rival_prev=temphero
        for temphero in state_info.heros:
            if temphero.hero_name==hero_name:
                hero_current=temphero
        if state_info.tick>508002:
            i=1
        if len(prev_state_info.attack_infos)!=0 : #有角色进行了攻击或回城
            for attack in prev_state_info.attack_infos:
                if attack.atker==int(hero_name): #英雄进行了攻击或回城
                    skill=attack.skill

                    # 看十位来决定技能id
                    skillid=int(attack.skill%100/10)
                    tgtid = str(attack.defer)
                    tgtpos=attack.tgtpos
                    if tgtid is None or tgtid == 'None':
                        # attackinfo里没有tgtid只有tgtpos
                        tgtid1=0
                    else:
                        #print("tgtid=")
                        #print(tgtid)
                        tgtid1=int(tgtid)
                    if attack.skill == 10000:#回城
                        action = CmdAction(hero_name, CmdActionEnum.CAST, 6, None, None, None, None, 48, None)
                        return action
                    if skillid == 0: #普攻，不会以自己为目标
                        if tgtid1<27 and tgtid1!= 0: #打塔
                            output_index=8
                        elif tgtid==hero_rival_prev.hero_name: #普通攻击敌方英雄
                            output_index=9
                        elif tgtid1!=0:#普通攻击敌方小兵
                            creeps=StateUtil.get_nearby_enemy_units(prev_state_info,hero_name)
                            n=len(creeps)
                            for i in range(n):
                                if creeps[i].unit_name==str(tgtid):
                                    output_index=i+10
                        elif tgtid1==0:#attacinfo里没有目标，从hit里找目标
                            tgtid=0
                            for hit in state_info.hit_infos:
                                if hit.atker==int(hero_name) and hit.skill==skill:
                                    tgtid = str(hit.tgt)
                                    if int(tgtid)<27: #打塔
                                        output_index=8
                                    elif tgtid==hero_rival_prev.hero_name:#敌方英雄
                                        output_index=9
                                    else:#小兵
                                        creeps=StateUtil.get_nearby_enemy_units(prev_state_info,hero_name)
                                        n=len(creeps)
                                        for i in range(n):
                                            if creeps[i].unit_name==tgtid:
                                                output_index=i+10
                            # 现在的技能应该没有那么高的延迟，如果需要后续信息后面可以多传几帧
                            # if tgtid==0:#这一帧没有对应的hit，在下一帧找
                            #     for hit in next_state_info.hit_infos:
                            #         if hit.atker == int(hero_name) and hit.skill == skill:
                            #             tgtid = str(hit.tgt)
                            #             if int(tgtid) < 27:  # 打塔
                            #                 output_index = 8
                            #             elif tgtid == hero_rival_current.hero_name:  # 敌方英雄
                            #                 output_index = 9
                            #             else:  # 小兵
                            #                 creeps = StateUtil.get_nearby_enemy_units(state_info, hero_name)
                            #                 n = len(creeps)
                            #                 for i in range(n):
                            #                     if creeps[i].unit_name == tgtid:
                            #                         output_index = i + 10
                            if tgtid==0:#任然没有hit，技能空放
                                if tgtpos !=None:
                                    #attackinfo里没有攻击目标id，只有坐标，根据位置找最近的目标作为输出
                                    [tgtid,output_index]=Replayer.get_closest_tgt(prev_state_info,hero_name,tgtpos,0)
                                    if output_index==-2:
                                        output_index=8
                                        #打塔
                                    elif output_index==-1:
                                        output_index=9
                                        #对方英雄
                                    else:
                                        output_index=output_index+9
                                else:#真的打空了
                                    action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49,
                                                       None)
                                    return action

                        action = CmdAction(hero_name, CmdActionEnum.ATTACK, 0, tgtid, tgtpos, None, None, output_index, None)
                        return action

                    else: #使用技能，不考虑以敌方塔为目标（若真以敌方塔为目标则暂时先不管吧，现在的两个英雄技能都对建筑无效）
                        if tgtid==hero_name: #or (tgtid=='0' and Replayer.skill_tag[skillid]==1):#对自身施法:部分技能无任何目标，tgt为0
                            tgtpos=hero_prev.pos
                            output_index=8+skillid*10
                        elif tgtid==hero_rival_prev.hero_name:#对敌方英雄施法
                            tgtpos=hero_rival_prev.pos
                            output_index=9+skillid*10
                        elif tgtid1>27:#对小兵施法
                            creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                            n = len(creeps)
                            for i in range(n):
                                if creeps[i].unit_name == str(tgtid):
                                    output_index = i + skillid*10+10
                        elif tgtid1==0:#attacinfo里没有目标，从hit里找目标
                            # todo::::
                            tgtid = 0
                            for hit in prev_state_info.hit_infos:
                                if hit.atker == int(hero_name) and hit.skill == skill:
                                    tgtid = str(hit.tgt)
                                    if tgtid == hero_rival_prev.hero_name:  # 敌方英雄
                                        output_index = 9+skillid*10
                                        action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                                           tgtpos, None, None, output_index, None)
                                        return action
                                else:  # 小兵
                                        creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                                        n = len(creeps)
                                        for i in range(n):
                                            if creeps[i].unit_name == tgtid:
                                                output_index = i + 10+skillid*10
                                                action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                                                   tgtpos, None, None, output_index, None)
                                                return action
                            if tgtid == 0:  # 这一帧没有对应的hit，在下一帧找
                                for hit in state_info.hit_infos:
                                    if hit.atker == int(hero_name) and hit.skill == skill:
                                        tgtid = str(hit.tgt)
                                        if tgtid == hero_rival_prev.hero_name:  # 敌方英雄
                                            output_index = 9 + skillid * 10
                                            action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                                               tgtpos, None, None, output_index, None)
                                            return action
                                    else:  # 小兵
                                            creeps = StateUtil.get_nearby_enemy_units(prev_state_info, hero_name)
                                            n = len(creeps)
                                            for i in range(n):
                                                if creeps[i].unit_name == tgtid:
                                                    output_index = i + 10 + skillid * 10
                                                    action = CmdAction(hero_name, CmdActionEnum.CAST, skillid, tgtid,
                                                                       tgtpos, None, None, output_index, None)
                                                    return action
                        if tgtid == 0:  # 任然没有hit，技能空放
                                if tgtpos != None:
                                    # attackinfo里没有攻击目标id，只有坐标，根据位置找最近的目标作为输出
                                    [tgtid, output_index] = Replayer.get_closest_tgt(prev_state_info, hero_name, tgtpos, 1)
                                    if output_index == 0:
                                        output_index = 8 + skillid * 10
                                        # 己方英雄或无指向
                                    elif output_index == -1:
                                        output_index = 9 + skillid * 10
                                        # 对方英雄
                                    else:
                                        output_index = output_index + skillid * 10 + 9
                                else:#真的技能空放了
                                    action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49,
                                                       None)
                                    return action
                        else:#对塔施法，模型中未考虑
                            action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                            return action
                        action=CmdAction(hero_name,CmdActionEnum.CAST,skillid,tgtid,tgtpos,None,None,output_index,None)
                        return action
                else:
                #英雄没有进攻也没有施法
                    if hero_current.pos.x!=hero_prev.pos.x or hero_current.pos.z!= hero_prev.pos.z or hero_current.pos.y!=hero_prev.pos.y:#移动
                        fwd = hero_current.pos.fwd(hero_prev.pos)
                        [fwd,output_index]=Replayer.get_closest_fwd(fwd)
                        action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None, output_index, None)
                        return action
                    else:#hold
                        action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                        return action
        else: #没有角色进行攻击或使用技能，英雄在移动或hold
            if hero_current.pos.x != hero_prev.pos.x or hero_current.pos.z != hero_prev.pos.z or hero_current.pos.y != hero_prev.pos.y:  # 移动
                fwd = hero_current.pos.fwd(hero_prev.pos)
                [fwd, output_index] = Replayer.get_closest_fwd(fwd)
                action = CmdAction(hero_name, CmdActionEnum.MOVE, None, None, None, fwd, None, output_index, None)
                return action
            else:  # hold
                action = CmdAction(hero_name, CmdActionEnum.HOLD, None, None, None, None, None, 49, None)
                return action

    @staticmethod
    def get_closest_tgt(state_info,hero_name,pos,skillslot):
        creeps=StateUtil.get_nearby_enemy_units(state_info,hero_name)
        min_distance=1000
        index=None
        #这是用作返回的 output_index

        m=len(creeps)
        for i in range(m):
            dist=StateUtil.cal_distance(pos,creeps[i].pos)
            if dist<min_distance:
                min_distance=dist
                index=i
                tgtid=creeps[i].unit_name
        if index!=None:
            index=index+1
        else:
            index=0
        #index=1~8代表当前传入的pos与小兵1~8最接近
        for hero in state_info.heros:
            dist=StateUtil.cal_distance(pos,hero.pos)
            if hero.hero_name==hero_name:
                if skillslot!=0 and dist < min_distance:
                    #普攻时目标不可为自己
                    min_distance=dist
                    index = 0
                    tgtid = None
            else:
                if dist<min_distance:
                    min_distance=dist
                    index=-1
                    tgtid=hero.hero_name
                #index=0代表无目标施法，index=-1代表向对方英雄施法
        if skillslot==0:
            #普攻时目标才能为塔
            tower=StateUtil.get_nearest_enemy_tower(state_info,hero_name)
            dist=StateUtil.cal_distance(pos,tower.pos)
            if dist<min_distance:
                min_distance=dist
                tgtid=tower.unit_name
                index=-2
                #-2指塔
        return [tgtid,index]


    # @staticmethod
    # def get_fwd(pos1, pos2):
    #     x = pos2.x - pos1.x
    #     y = pos2.y - pos1.y
    #     z = pos2.z - pos1.z
    #     a = (x * x + y * y + z * z) / 1000000
    #     x = x / math.sqrt(a)
    #     y = y / math.sqrt(a)
    #     z = z / math.sqrt(a)
    #     return FwdStateInfo(x, y, z)

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


def train_line_model(state_path, model_path, output_model_path):
    state_file = open(state_path, "r")
    model = LineModel(240, 50)
    model.load(model_path)

    lines = state_file.readlines()
    for line in lines:
        state_info = StateUtil.parse_state_log(line)
        if len(state_info.actions) > 0:
            #去掉最后几帧没有reward的情况
            flag=0
            for action in state_info.actions:
                if action.reward==None:
                    flag=flag+1
            if flag==0:
                model.remember(state_info)
    for i in range(5):
        model.replay(30)
        print ("___________________________________ train ___________________________________")
    model.save('line_model_' + str(datetime.now()).replace(' ', '').replace(':', '') + '.model')


# 根据包含了模型决策的state日志，继续计算我方英雄的行为以及双方的奖励值
def cal_state_log_action_reward(state_path, output_path):
    state_file = open(state_path, "r")
    output = open(output_path, 'w')
    lines = state_file.readlines()

    state_logs = []
    prev_state = None

    for line in lines:
        if prev_state is not None and int(prev_state.tick) >= 240504:
            i = 1

        cur_state = StateUtil.parse_state_log(line)

        if cur_state.tick == StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state = None
        elif prev_state is not None and prev_state.tick >= cur_state.tick:
            print ("clear")
            prev_state = None

        # 玩家action
        if prev_state is not None:
            hero = prev_state.get_hero("27")
            line_index = 1
            near_enemy_heroes = StateUtil.get_nearby_enemy_heros(prev_state, hero.hero_name,
                                                                 StateUtil.LINE_MODEL_RADIUS)
            near_enemy_units = StateUtil.get_nearby_enemy_units(prev_state, hero.hero_name, StateUtil.LINE_MODEL_RADIUS)
            nearest_enemy_tower = StateUtil.get_nearest_enemy_tower(prev_state, hero.hero_name,
                                                                    StateUtil.LINE_MODEL_RADIUS)
            near_enemy_units_in_line = StateUtil.get_units_in_line(near_enemy_units, line_index)
            nearest_enemy_tower_in_line = StateUtil.get_units_in_line([nearest_enemy_tower], line_index)
            if len(near_enemy_heroes) != 0 or len(near_enemy_units_in_line) != 0 or len(
                    nearest_enemy_tower_in_line) != 0:
                player_action = Replayer.guess_player_action(prev_state, cur_state, "27")
                action_str = StateUtil.build_command(player_action)
                print('玩家行为分析：' + str(action_str) + ' tick:' + str(prev_state.tick) + ' prev_pos: ' +
                      hero.pos.to_string() + ', cur_pos: ' + cur_state.get_hero(hero.hero_name).pos.to_string())
                prev_state.add_action(player_action)
        if prev_state is not None:
            state_logs.append(prev_state)

        prev_state = cur_state

    if prev_state is not None:
        state_logs.append(prev_state)

    # 测试计算奖励值
    state_logs_with_reward = LineModel.update_rewards(state_logs)
    for state_with_reward in state_logs_with_reward:
        # 将结果记录到文件
        if state_with_reward.tick>60522:
            i=1
        state_encode = state_with_reward.encode()
        state_json = JSON.dumps(state_encode)
        output.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + state_json + "\n")
        output.flush()

    print(len(state_logs))


# 从自由2客户端发送的JSON数据中得到模型选择的Action，
# 注意，如果要准确还原模型当时的选择，需要将随机系数设为0
def replay_battle_log(log_path, state_path, hero_names, model_path=None, save_model_path=None):
    path = log_path
    file = open(path, "r")
    state_file = open(state_path, 'w')
    lines = file.readlines()

    state_logs = []
    prev_state = None
    model = LineModel(240, 50)
    if model_path is not None:
        model.load(model_path)
    if save_model_path  is not None:
        model.save(save_model_path)

    line_trainer = LineTrainer()
    for line in lines:
        if prev_state is not None and int(prev_state.tick) > 248556:
            i = 1

        cur_state = StateUtil.parse_state_log(line)
        if cur_state.tick == StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state = None
        elif prev_state is not None and prev_state.tick >= cur_state.tick:
            print ("clear")
            prev_state = None
        state_info = StateUtil.update_state_log(prev_state, cur_state)

        # 测试对线模型
        rsp_str = line_trainer.build_response(state_info, prev_state, model, hero_names)
        print(rsp_str)
        prev_state = state_info
        state_logs.append(state_info)

    # 测试计算奖励值
    for state in state_logs:
        # 将结果记录到文件
        state_encode = state.encode()
        state_json = JSON.dumps(state_encode)
        state_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + state_json + "\n")
        state_file.flush()
    print(len(state_logs))

# def test1(state_path):
#     state_file = open(state_path, "r")
#
#     lines = state_file.readlines()
#
#     for line in lines:
#         state_info = StateUtil.parse_state_log(line)
#         if len(state_info.actions)>0:
#             for action in state_info.actions :
#                 if action.reward==None:
#                     print(action.encode())
#                     print(state_info.tick)
#                     print(state_info.encode())



if __name__ == "__main__":
    # train_line_model('/Users/sky4star/Github/zy2go/battle_logs/battlestate1.log',
    #                  '/Users/sky4star/Github/zy2go/src/server/line_model_2017-08-11141336.087441.model')
    #replay_battle_log('/Users/sky4star/Github/zy2go/battle_logs/autobattle3.log',
    #                  '/Users/sky4star/Github/zy2go/src/server/line_model_2017-08-14185336.317081.model')
    
    replay_battle_log('/Users/sky4star/Github/zy2go/src/server/model_2017-08-17134722.152043/httpd.log',
                      '/Users/sky4star/Github/zy2go/src/server/model_2017-08-17134722.152043/pve_state.log',
                      ['28'],
                      '/Users/sky4star/Github/zy2go/src/server/model_2017-08-17134722.152043/line_model.model',
                      None)
    #                    '/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/line_model.model')
    # cal_state_log_action_reward('/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/pve_state_test.log',
    #                             '/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/state_with_reward_test.log')
    # train_line_model('/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/state_with_reward_test.log',
    #                  '/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/line_model_test.model',
    #                  '/Users/sky4star/Github/zy2go/src/server/model_2017-08-16152038.500300/replayed_line_model_test.model')
