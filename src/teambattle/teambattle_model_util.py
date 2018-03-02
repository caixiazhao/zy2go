#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import time
import pickle
import tensorflow as tf
import baselines.common.tf_util as U
import requests
from common import cf as C
from teambattle.teambattle_util import TeamBattleUtil
from teambattle.teambattletrainer import TeamBattleTrainer
from train.line_ppo_model import LinePPOModel
from train.linemodel_ppo1 import LineModel_PPO1
from util.httputil import HttpUtil
from util.stateutil import StateUtil

def push_data(battle_id, hero_name, generation_id, data):
    url = 'http://127.0.0.1:8780/data/%d/%d/%s' % (
        generation_id, battle_id, hero_name)
    r = requests.get(url, data=data)
    return r.text

def fetch_model_weights():
    url = 'http://127.0.0.1:%d/data/model' % (C.GATEWAY_PORT)
    r = requests.get(url)

    # 读取结果应该是generation_id, weight_maps
    print(r.content)
    content = pickle.loads(r.content)
    generation_id = list(content.keys())[0]
    weight_maps = list(content.values())[0]
    return generation_id, weight_maps

class TeamBattleModelUtil:
    def build_model_ppo(self, ob_size, act_size, save_dir, model_hero, model_path=None, schedule_timesteps=10000,
                         model_initial_p=1.0, model_final_p=0.02, model_gamma=0.99):
        ob = np.zeros(ob_size, dtype=float).tolist()
        ac = np.zeros(act_size, dtype=float).tolist()
        print(model_hero, "已启动")
        model = LineModel_PPO1(ob_size, act_size, model_hero, ob, ac, LinePPOModel, gamma=model_gamma,
                            scope=model_hero, schedule_timesteps=schedule_timesteps, initial_p=model_initial_p, final_p=model_final_p)

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        if model_path is not None:
            print("load model", model_path, "model_hero", model_hero)
            model.load(model_path)
        model_save_header = save_dir + '/' + model_hero + '_'

        # # 使用Ray的方式来得到和赋予权重信息
        # weight = model.variables.get_weights()
        # print("weight", weight)
        # # model.variables.set_weights(weight)
        #
        # import pickle
        # bytes = pickle.dumps(weight)
        # new_weight = pickle.loads(bytes)
        # model.variables.set_weights(new_weight)
        #
        # # 输出权重信息
        # tvars = tf.trainable_variables()
        # tvars_vals = U.get_session().run(tvars)
        # for var, val in zip(tvars, tvars_vals):
        #     print(var.name, val)

        return model, model_save_header

    def __init__(self, ob_size, act_size, hero_names, battle_num, save_root, save_batch, schedule_timesteps,
                         model_initial_p, model_final_p, gamma, model_path_pattern=None):
        # 启动所有的模型
        self.battle_num = battle_num
        self.save_batch = save_batch
        self.model_map = {}
        self.train_data_map = {}
        self.clear_cache_signals = []
        self.hero_names = hero_names
        self.generation_id = 0

        for hero_name in hero_names:
            # 准备模型
            model_path = None
            if model_path_pattern is not None:
                model_path = model_path_pattern.format(hero_name)

            model, save_header = self.build_model_ppo(ob_size, act_size, save_root, hero_name, model_path, schedule_timesteps, model_initial_p, model_final_p, gamma)
            self.model_map[hero_name] = (model, save_header)

            # 准备训练集的存储
            battle_data_map = {}
            self.train_data_map[hero_name] = battle_data_map

    def get_action_list(self, battle_id, hero_name, state_input):
        model, _ = self.model_map[hero_name]
        actions_list, explor_value, vpred = model.get_action(state_input)

        # 判断是否已经切换了模型版本，应该清空之前的行为缓存
        clear_cache = False
        if battle_id in self.clear_cache_signals:
            self.clear_cache_signals.remove(battle_id)
            clear_cache = True

        return list(actions_list[0]), explor_value, vpred, clear_cache

    def if_save_model(self, model, save_header, save_batch):
        # 训练之后检查是否保存
        replay_time = model.iters_so_far
        if replay_time % save_batch == 0:
            save_path = save_header + str(replay_time) + '/model'
            print("save model", save_path)
            model.save(save_path)

    # 计算模型的奖励情况
    # 团战情况下的奖励情况非常单一
    # 英雄杀死其它英雄，奖励，同时队友也有奖励（存活的队友）
    # 英雄被击杀，惩罚
    # 己方英雄死亡，其它英雄也要受到惩罚（存活的队友）
    # 扩大死亡奖励，缩小团战结果奖励
    #TODO 击杀的判定需要仔细审核，暂定规则为英雄死亡当帧，hit信息指向该英雄的攻击者都奖励
    def cal_rewards(self, prev_state_info, state_info, next_state_info, battle_heroes, prev_dead_heroes):

        # 首先对所有参展人员，设置初始奖励值
        for hero_name in battle_heroes:
            state_info.add_rewards(hero_name, 0)

        # 更新奖励值
        left_heroes = list(battle_heroes)
        all_dead_heroes = list(prev_dead_heroes)
        for hero_name in battle_heroes:
            dead = StateUtil.if_hero_dead(state_info, next_state_info, hero_name)
            if dead == 1:
                # 死亡者惩罚
                reward = state_info.get_or_insert_reward(hero_name)
                print("battle_id", state_info.battleid, "hero_name", hero_name, "cal_rewards", "死亡者惩罚", "tick", state_info.tick)
                reward -= 10
                state_info.add_rewards(hero_name, reward)

                # 死亡者，存活的队友接受惩罚
                dead_hero_teamers, dead_hero_opponents = TeamBattleUtil.get_friend_opponent_heros(battle_heroes, hero_name)
                for team_member in dead_hero_teamers:
                    reward = state_info.get_or_insert_reward(team_member)
                    reward -= 2
                    state_info.add_rewards(team_member, reward)
                    print("battle_id", state_info.battleid, "hero_name", team_member, "cal_rewards", "死亡者队友惩罚", "tick", state_info.tick)

                # 攻击者奖励
                attackers = next_state_info.get_hero_be_attacked_info(hero_name)
                for attacker in attackers:
                    reward = state_info.get_or_insert_reward(attacker)
                    reward += 10
                    state_info.add_rewards(attacker, reward)
                    print("battle_id", state_info.battleid, "hero_name", attacker, "cal_rewards", "攻击者奖励", "tick", state_info.tick, "死亡英雄", hero_name)

                # 攻击者，存活的队友接受奖励
                for opponent in dead_hero_opponents:
                    if opponent not in attackers:
                        reward = state_info.get_or_insert_reward(opponent)
                        reward += 2
                        state_info.add_rewards(opponent, reward)
                        print("battle_id", state_info.battleid, "hero_name", opponent, "cal_rewards", "攻击者队友奖励",
                                "tick", state_info.tick)

                # 从存活英雄中删除
                left_heroes.remove(hero_name)
                all_dead_heroes.append(hero_name)

        # 检查是否战斗结束
        #TODO 这里的逻辑是有问题的
        all_in_team = TeamBattleUtil.all_in_one_team(left_heroes)
        win = 0
        # 胜利判断中需要确认阵亡英雄+战斗英雄应该数量是全员
        if all_in_team != -1 and (len(left_heroes) + len(all_dead_heroes)) == len(self.hero_names):
            win = 1
        #     for hero in left_heroes:
        #         reward = state_info.get_or_insert_reward(hero)
        #         reward += 10
        #         state_info.add_rewards(hero, reward)
        #
        #     #TODO 要不要给赢的队伍中死亡的人团战胜利奖励，给多少
        #     for hero in all_dead_heroes:
        #         # 这里目前认为所有没有参战的英雄都是
        #         if hero not in battle_heroes:
        #             if TeamBattleUtil.get_hero_team(hero) == all_in_team:
        #                 reward = state_info.get_or_insert_reward(hero)
        #                 reward += 5
        #                 state_info.add_rewards(hero, reward)
        #             # 失败的团队给予惩罚
        #             else:
        #                 reward = state_info.get_or_insert_reward(hero)
        #                 if reward is None:
        #                     reward = 0
        #                     hero_act = state_info.get_action(hero)
        #                     print("Error", 'battle_id', 'cal_reward', state_info.battle_id, hero_act.hero_name, hero_act.action,
        #                           hero_act.skillid)
        #                 reward -= 10
        #                 state_info.add_rewards(hero, reward)
        return state_info, win, all_in_team, left_heroes

    def set_train_data(self, hero_name, battle_id, o4r, generation_id):
        # o4r['battle_id'] = (server_id - 1) * 100 + battle_id
        o4r['battle_id'] = battle_id
        o4r['generation_id'] = generation_id
        o4r['hero_name'] = hero_name

        o4rdata = pickle.dumps(o4r)

        print('%s push-data %d g:%d m:%s - %d' % (
            time.strftime('%H:%M:%S'),
            battle_id,
            generation_id,
            hero_name,
            len(o4rdata)))

        r = push_data(battle_id, hero_name,
                      generation_id, o4rdata)

        gateway_generation_id = int(r)

        # 添加一个清空缓存信息给每场战斗
        for battle_id in range(1, self.battle_num + 1):
            if battle_id not in self.clear_cache_signals:
                self.clear_cache_signals.append(battle_id)

        if C.generation_id == gateway_generation_id:
            return

        if C.LOG['GENERATION_UPDATE']:
            print('%s generation update P3 %d - process %d:%d' % (
                time.strftime('%H:%M:%S'),
                battle_id,
                C.generation_id, gateway_generation_id))
        C.generation_id = gateway_generation_id

        return

    def do_real_train(self, o4rs, hero_name):
        if o4rs is None:
            print('hero_name', hero_name, "训练数据异常")
        else:
            print('model', hero_name, 'begin to train')
            model, model_save_header = self.model_map[hero_name]
            model.replay(o4rs, 0)
            self.if_save_model(model, model_save_header, self.save_batch)

    def get_model_weights(self):
        model_weights = {}
        # 把变量转成list类型
        for hero_name in self.hero_names:
            model, _ = self.model_map[hero_name]
            weight = model.variables.get_weights()
            model_weights[hero_name] = weight
        return self.generation_id, model_weights

    def set_model_weights(self, generation_id):
        # 确保不会因为请求超时 无法获得模型变量，更新模型
        try:
            new_generation_id, model_weights = fetch_model_weights()
            if int(new_generation_id) != generation_id:
                print('set_model_weights', 'found generation id not same', generation_id, new_generation_id)
            if len(model_weights.values()) == len(self.hero_names):
                for hero_name in self.hero_names:
                    model, _ = self.model_map[hero_name]
                    model_weight = model_weights[hero_name]
                    model.variables.set_weights(model_weight)
                self.generation_id = generation_id
                print('set_model_weights', 'set new model weights')
            else:
                print('set_model_weights', 'found model weight size not match', len(model_weights.values()))
        except Exception as ex:
            print(ex)
            return 0





