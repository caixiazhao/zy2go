#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from train.line_ppo_model import LinePPOModel
from train.linemodel_ppo1 import LineModel_PPO1
from util.httputil import HttpUtil


class TeamBattleModelUtil:
    def build_model_ppo(self, save_dir, model_hero, model_path=None, schedule_timesteps=10000,
                         model_initial_p=1.0, model_final_p=0.02, model_gamma=0.99):
        ob_size = 890
        act_size = 28
        ob = np.zeros(ob_size, dtype=float).tolist()
        ac = np.zeros(act_size, dtype=float).tolist()
        print(model_hero)
        model = LineModel_PPO1(ob_size, act_size, model_hero, ob, ac, LinePPOModel, gamma=model_gamma,
                            scope=model_hero, schedule_timesteps=schedule_timesteps, initial_p=model_initial_p, final_p=model_final_p)

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        if model_path is not None:
            model.load(model_path)
        model_save_header = save_dir + '/' + model_hero

        return model, model_save_header

    def __init__(self, hero_names, battle_num, save_batch):
        # 启动所有的模型
        save_root = HttpUtil.get_save_root_path()
        self.battle_num = battle_num
        self.save_batch = save_batch
        self.model_map = {}
        self.train_data_map = {}
        for hero_name in hero_names:
            # 准备模型
            model, save_header = self.build_model_ppo(save_root, hero_name, None)
            self.model_map[hero_name] = (model, save_header)

            # 准备训练集的存储
            battle_data_map = {}
            self.train_data_map[hero_name] = battle_data_map

    def get_action_list(self, hero_name, state_input):
        model, _ = self.model_map[hero_name]
        actions_list, explor_value, vpred = model.get_action(state_input)
        return list(actions_list[0]), explor_value, vpred

    def if_save_model(self, model, save_header, save_batch):
        # 训练之后检查是否保存
        replay_time = model.iters_so_far
        if replay_time % save_batch == 0:
            model.save(save_header + str(replay_time) + '/model')

    def set_train_data(self, hero_name, battle_id, o4r, batch_size):
        self.train_data_map[hero_name][battle_id] = o4r
        if len(self.train_data_map[hero_name]) == self.battle_num:
            print('model', hero_name, 'begin to train')
            model, model_save_header = self.model_map[hero_name]
            model.replay(self.train_data_map[hero_name].values(), batch_size)
            self.train_data_map[hero_name].clear()
            self.if_save_model(model, model_save_header, self.save_batch)




