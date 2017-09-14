# -*- coding: utf8 -*-
import collections

from baselines import logger
import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers
from baselines.common import Dataset, explained_variance, fmt_row, zipsame

import baselines.common.tf_util as U
from baselines import deepq
from baselines.common.mpi_adam import MpiAdam
from baselines.common.schedules import LinearSchedule
from baselines.deepq import ReplayBuffer
from train.line_input import Line_input
from train.line_ppo_model import LinePPOModel
from train.linemodel import LineModel
from baselines.common.mpi_moments import mpi_moments
from train.linemodel_dpn import LineModel_DQN
from util.rewardutil import RewardUtil
from util.stateutil import StateUtil

from baselines.common.mpi_moments import mpi_moments
from mpi4py import MPI
from collections import deque
import time

class PPO_CACHE:
    REWARD_RIVAL_DMG = 250

    def __init__(self, ob, ac, horizon=100):
        self.horizon = horizon

        # Initialize history arrays
        self.obs = np.array([ob for _ in range(horizon)])
        self.rews = np.zeros(horizon, 'float32')
        self.vpreds = np.zeros(horizon, 'float32')
        self.news = np.zeros(horizon, 'int32')
        self.acs = np.array([ac for _ in range(horizon)])
        self.prevacs = self.acs.copy()
        self.t = 0

        self.ep_rets = []
        self.ep_lens = []
        self.cur_ep_ret = 0
        self.cur_ep_len = 0

        self.lenbuffer = deque(maxlen=100)  # rolling buffer for episode lengths
        self.rewbuffer = deque(maxlen=100)  # rolling buffer for episode rewards
        self.episodes_so_far = 0
        self.timesteps_so_far = 0
        self.iters_so_far = 0
        self.tstart = time.time()

    def remember(self, ob, ac, vpred, new, rew, prev_new):
        if self.t > 0 and self.t % self.horizon == 0:
            # Be careful!!! if you change the downstream algorithm to aggregate
            # several of these batches, then be sure to do a deepcopy
            self.ep_rets = []
            self.ep_lens = []
        i = self.t % self.horizon
        self.obs[i] = ob
        self.vpreds[i] = vpred
        # 这里记录的new不是结果中的？
        self.news[i] = prev_new
        self.acs[i] = ac
        prev_act = self.acs[i-1]
        self.prevacs[i] = prev_act
        self.rews[i] = rew

        self.cur_ep_ret += rew
        self.cur_ep_len += 1

        if new:
            self.ep_rets.append(self.cur_ep_ret)
            self.ep_lens.append(self.cur_ep_len)
            self.cur_ep_ret = 0
            self.cur_ep_len = 0
        self.t += 1

    def output4replay(self, cur_new, next_vpred):
        if self.t > 0 and self.t % self.horizon == 0:
            return {"ob": self.obs, "rew": self.rews, "vpred": self.vpreds, "new": self.news,
             "ac": self.acs, "prevac": self.prevacs, "nextvpred": next_vpred * (1 - cur_new),
             "ep_rets": self.ep_rets, "ep_lens": self.ep_lens}
        else:
            return None