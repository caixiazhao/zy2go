#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json as JSON
from time import gmtime, strftime
from datetime import datetime

from train.line_ppo_model import LinePPOModel
from train.linemodel import LineModel
from train.linemodel_dpn import LineModel_DQN
from train.linemodel_ppo1 import LineModel_PPO1
from util.linetrainer import LineTrainer
from util.linetrainer_ppo import LineTrainerPPO
from util.ppocache import PPO_CACHE
from util.replayer import Replayer
from util.stateutil import StateUtil
from baselines.common import set_global_seeds
import numpy as np

def test_line_trainer_ppo(raw_log_path, model1_path, model2_path, real_hero=None):
    set_global_seeds(2000)
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()

    ob_size = 183
    act_size = 49
    ob = np.zeros(ob_size, dtype=float).tolist()
    ac = np.zeros(act_size, dtype=float).tolist()
    model1_hero = '27'
    model2_hero = '28'
    # model_1 = None
    # model1_cache = None
    model_1 = LineModel_PPO1(ob_size, act_size, model1_hero, ob, ac, LinePPOModel, scope="model1",
                             schedule_timesteps=2, initial_p=1, final_p=0)
    model1_cache = PPO_CACHE(ob, 1, horizon=64)
    # model_2 = None
    # model2_cache = None
    model_2 = LineModel_PPO1(ob_size, act_size, model2_hero, ob, ac, LinePPOModel, scope="model2",
                             schedule_timesteps=2, initial_p=1, final_p=0)
    model2_cache = PPO_CACHE(ob, 1, horizon=64)

    date_str = str(datetime.now()).replace(' ', '').replace(':', '')
    save_dir = '/Users/sky4star/Github/zy2go/battle_logs/model_' + date_str
    os.makedirs(save_dir)

    # 创建模型，决定有几个模型，以及是否有真人玩家
    # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
    if model1_path is not None:
        model_1.load(model1_path)
    model1_save_header = save_dir + '/line_model_1_v'

    if model2_path is not None:
        model_2.load(model2_path)
    model2_save_header = save_dir + '/line_model_2_v'

    line_trainer = LineTrainerPPO(save_dir, model1_hero, model_1, model1_save_header, model1_cache,
        model2_hero, model_2, model2_save_header, model2_cache, real_hero=real_hero, enable_policy=True)

    for i in range(10):
        for line in lines:
            json_str = line[23:]
            rsp_str = line_trainer.train_line_model(json_str)
            print('返回结果: ' + rsp_str)
    line_trainer.save_models()


def train_line_model_ppo():
    return


def test_line_trainer(raw_log_path, model1_path, model2_path, initial_p, final_p):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    line_trainer = LineTrainer(model1_heros=['27'], model2_heros=['28'], real_heros=None,
                               model1_path=model1_path,
                               model2_path=model2_path,
                               initial_p=initial_p, final_p=final_p)
    for line in lines:
        json_str = line[23:]
        rsp_str = line_trainer.train_line_model(json_str)
        print('返回结果: ' + rsp_str)


def train_line_model(state_path, model_path, scope, output_model_path, heros):
    state_file = open(state_path, "r")
    model = LineModel_DQN(279, 48, heros, scope=scope)
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
                next_state_info = StateUtil.parse_state_log(lines[idx+1])
                model.get_action(prev_state_info, state_info, '27', '28')

                added = model.remember(prev_state_info, state_info, next_state_info)
                if added:
                    # 需要手动添加
                    model.act_times += 1
                    model1_memory_len = model.get_memory_size()
                    if model.if_replay(64):
                        # print ('开始模型训练')
                        model.replay(64)
                        if model1_memory_len > 0 and model1_memory_len % 1000 == 0:
                            save_dir = output_model_path + str(model.get_memory_size())
                            os.makedirs(save_dir)
                            model.save(save_dir + '/model')
    # model.replay(100, False)
    # model.save(output_model_path)

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
    model = LineModel(279, 48, hero_names)
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
    # test_line_trainer('/Users/sky4star/Github/zy2go/battle_logs/model_2017-09-08152540.975239/raw.log',
    #                   None,
    #                   None,
                      # '/Users/sky4star/Github/zy2go/battle_logs/model_2017-09-01180534.681934/line_model_2_v51/model',
                      # '/Users/sky4star/Github/zy2go/battle_logs/model_2017-09-01180534.681934/line_model_2_v52/model',
                      # initial_p=0, final_p=0)
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
    # train_line_model('/Users/sky4star/Downloads/state_reward.log',
    #                  None, "linemodel1",
    #                  '/Users/sky4star/Github/zy2go/battle_logs/test/server0911/linetrainer_1_v',
    #                  ['27'])
    test_line_trainer_ppo('/Users/sky4star/Github/zy2go/battle_logs/model_2017-10-11170324.808673/raw.log',
                          None,
                          None,
                          None)