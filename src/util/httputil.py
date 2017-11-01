from datetime import datetime
import os

from baselines.common import set_global_seeds
from train.line_ppo_model import LinePPOModel
from train.linemodel_dpn import LineModel_DQN
from train.linemodel_ppo1 import LineModel_PPO1
import numpy as np


class HttpUtil:
    @staticmethod
    def get_save_root_path():
        date_str = str(datetime.now()).replace(' ', '').replace(':', '')
        save_dir = '/Users/sky4star/Github/zy2go/battle_logs/model_' + date_str  # /data/battle_logs/model_ for server
        os.makedirs(save_dir)
        return save_dir

    @staticmethod
    def build_models_ppo(save_dir, model1_path=None, model2_path=None, schedule_timesteps=10000,
                         model1_initial_p=1.0, model1_final_p=0.02, model1_gamma=0.99,
                         model2_initial_p=1.0, model2_final_p=0.02, model2_gamma=0.99):
        ob_size = 183
        act_size = 49
        ob = np.zeros(ob_size, dtype=float).tolist()
        ac = np.zeros(act_size, dtype=float).tolist()
        model1_hero = '27'
        model2_hero = '28'
        model_1 = LineModel_PPO1(ob_size, act_size, model1_hero, ob, ac, LinePPOModel, gamma=model1_gamma,
                            scope="model1", schedule_timesteps=schedule_timesteps, initial_p=model1_initial_p, final_p=model1_final_p)
        model_2 = LineModel_PPO1(ob_size, act_size, model2_hero, ob, ac, LinePPOModel,  gamma=model2_gamma,
                            scope="model2", schedule_timesteps=schedule_timesteps, initial_p=model2_initial_p, final_p=model2_final_p)

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        if model1_path is not None:
            model_1.load(model1_path)
        model1_save_header = save_dir + '/line_model_1_v'

        if model2_path is not None:
            model_2.load(model2_path)
        model2_save_header = save_dir + '/line_model_2_v'

        return model_1, model1_save_header, model_2, model2_save_header

    # 两个模型用来相互对战，分别训练
    @staticmethod
    def build_models(model1_path=None, model2_path=None, initial_p=1.0, final_p=0.02):
        # 创建存储文件路径
        date_str = str(datetime.now()).replace(' ', '').replace(':', '')
        save_dir = '/data/battle_logs/model_' + date_str
        os.makedirs(save_dir)

        # 创建模型，决定有几个模型，以及是否有真人玩家
        # 模型需要指定学习的英雄，这里我们学习用该模型计算的英雄加上真人（如果存在），注意克隆数组
        model_1 = LineModel_DQN(279, 48, ['27'], scope="linemodel1", initial_p=initial_p, final_p=final_p)
        if model1_path is not None:
            model_1.load(model1_path)
        model1_save_header = save_dir + '/line_model_1_v'

        model_2 = LineModel_DQN(279, 48, ['28'], scope="linemodel2", initial_p=initial_p, final_p=final_p)
        if model2_path is not None:
            model_2.load(model2_path)
        model2_save_header = save_dir + '/line_model_2_v'

        return save_dir, model_1, model1_save_header, model_2, model2_save_header