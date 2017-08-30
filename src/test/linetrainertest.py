#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json as JSON
from time import gmtime, strftime
from train.linemodel import LineModel
from util.linetrainer import LineTrainer
from util.replayer import Replayer
from util.stateutil import StateUtil
import baselines.common.tf_util as U


def test_line_trainer(raw_log_path, model1_path):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    line_trainer = LineTrainer(model1_heros=['27'], model2_heros=['28'], real_heros=None,
                               model1_path=model1_path,
                               model2_path=None)
    for line in lines:
        json_str = line[23:]
        rsp_str = line_trainer.train_line_model(json_str)
        print('返回结果: ' + rsp_str)


def train_line_model(state_path, model_path, output_model_path, heros):
    state_file = open(state_path, "r")
    model = LineModel(279, 50, heros)
    if model_path is not None:
        model.load(model_path)

    lines = state_file.readlines()
    for idx in range(len(lines)):
        state_info = StateUtil.parse_state_log(lines[idx])
        if len(state_info.actions) > 0:
            # 去掉最后几帧没有reward的情况
            flag = 0
            for action in state_info.actions:
                if action.reward == None:
                    flag = flag + 1
            if flag == 0:
                prev_state_info = StateUtil.parse_state_log(lines[idx-1])
                model.remember(state_info, prev_state_info)
    print("model memory size: " + str(len(model.memory)))
    for i in range(1):
        model.replay(5000, True, output_model_path + "_graph_" + str(i))
        print ("___________________________________ train ___________________________________")
    # 输出一部分对比数据
    model.replay(100, False)
    model.save(output_model_path)

# 根据包含了模型决策的state日志，继续计算我方英雄的行为以及双方的奖励值
def guess_action_cal_reward(state_path, output_path):
    state_file = open(state_path, "r")
    output = open(output_path, 'w')
    lines = state_file.readlines()

    state_logs = []
    prev_state = None

    for line in lines:
        cur_state = StateUtil.parse_state_log(line)
        if cur_state.tick == StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state = None
        elif prev_state is not None and prev_state.tick >= cur_state.tick:
            print ("clear")
            prev_state = None
        if prev_state is not None:
            state_logs.append(prev_state)
        prev_state = cur_state

    if prev_state is not None:
        state_logs.append(prev_state)

    # 猜测玩家行为
    for idx in range(1, len(state_logs)-1):
        prev_state = state_logs[idx-1]
        cur_state = state_logs[idx]
        next_state = state_logs[idx+1]

        if cur_state.tick >= 55044:
            db = 1

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
            player_action = Replayer.guess_player_action(prev_state, cur_state, next_state, "27", "28")
            action_str = StateUtil.build_command(player_action)
            print('玩家行为分析：' + str(action_str) + ' tick:' + str(prev_state.tick) + ' prev_pos: ' +
                  hero.pos.to_string() + ', cur_pos: ' + cur_state.get_hero(hero.hero_name).pos.to_string())
            prev_state.add_action(player_action)

    # 测试计算奖励值
    state_logs_with_reward = LineModel.update_rewards(state_logs)
    for state_with_reward in state_logs_with_reward:
        # 将结果记录到文件
        state_encode = state_with_reward.encode()
        state_json = JSON.dumps(state_encode)
        output.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + state_json + "\n")
        output.flush()

    print(len(state_logs))


def cal_state_log_action_reward(state_path, output_path):
    state_file = open(state_path, "r")
    output = open(output_path, 'w')
    lines = state_file.readlines()

    state_logs = []
    prev_state = None

    for line in lines:
        cur_state = StateUtil.parse_state_log(line)
        if cur_state.tick == StateUtil.TICK_PER_STATE:
            print("clear")
            prev_state = None
        elif prev_state is not None and prev_state.tick >= cur_state.tick:
            print ("clear")
            prev_state = None
        if prev_state is not None:
            state_logs.append(prev_state)
        prev_state = cur_state

    if prev_state is not None:
        state_logs.append(prev_state)

    # 测试计算奖励值
    state_logs_with_reward = LineModel.update_rewards(state_logs)

    for state_with_reward in state_logs_with_reward:
        # 将结果记录到文件
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
    model = LineModel(279, 50, hero_names)
    if model_path is not None:
        model.load(model_path)
    if save_model_path is not None:
        model.save(save_model_path)

    line_trainer = LineTrainer(hero_names)
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

if __name__ == "__main__":
    with U.make_session(8):
        test_line_trainer('/Users/sky4star/Github/zy2go/battle_logs/model_2017-08-25100407.804318-long/raw.log',
                         None)
    # replay_battle_log('C:/Users/YangLei/Documents/GitHub/zy2go/src/server/model_2017-08-17010052.525523/httpd.log',
    #                   'C:/Users/YangLei/Documents/GitHub/zy2go/src/server/model_2017-08-17010052.525523/pve_state_test.log',
    #                   ['28'], None, None)
    #                   None,
    #                   '/Users/sky4star/Github/zy2go/src/server/model_2017-08-17134722.152043/line_model.model',
                      # None)
    #                    '/Users/sky4star/Github/zy2go/src/server/model_2017-08-17134722.152043/line_model.model')
    # guess_action_cal_reward('/Users/sky4star/Github/zy2go/data/merged_state_0825.log',
    #                             '/Users/sky4star/Github/zy2go/data/merged_state_with_rewards_0825.log')
    # cal_state_log_action_reward('/Users/sky4star/Github/zy2go/data/merged_state_0825.log',
    #                             '/Users/sky4star/Github/zy2go/data/merged_state_with_reward_0828.log')
    # train_line_model('/Users/sky4star/Github/zy2go/data/merged_state_with_reward_0828.log',
    #                  None,
    #                  '/Users/sky4star/Github/zy2go/battle_logs/test/line_model_1_trained_0828_test',
    #                  ['27'])
