# -*- coding: utf8 -*-
import collections

import numpy as np
import time


class PPO_CACHE2:
    REWARD_RIVAL_DMG = 250

    def __init__(self, horizon=100):
        self.horizon = horizon

        # Initialize history arrays
        self.obs = []
        self.rews = []
        self.vpreds = []
        self.news = []
        self.acs = []
        self.prevacs = []
        self.nextnew = 0
        self.t = 0

        self.ep_rets = []
        self.ep_lens = []
        self.cur_ep_ret = 0
        self.cur_ep_len = 0

        # self.lenbuffer = deque(maxlen=100)  # rolling buffer for episode lengths
        # self.rewbuffer = deque(maxlen=100)  # rolling buffer for episode rewards
        self.episodes_so_far = 0
        self.timesteps_so_far = 0
        self.iters_so_far = 0
        self.tstart = time.time()

    def get_prev_new(self):
        # remember中的new会变成下一条的prev_new
        return self.nextnew

    def change_last(self, new, rew):
        self.rews[-1] = rew
        self.nextnew = new

    def isempty(self):
        return len(self.obs) == 0

    def clear_cache(self):
        self.ep_rets = []
        self.ep_lens = []
        self.obs = []
        self.rews = []
        self.vpreds = []
        self.news = []
        self.acs = []
        self.prevacs = []
        self.nextnew = 0

    def remember(self, ob, ac, vpred, new, rew, prev_new):
        self.obs.append(ob)
        self.vpreds.append(vpred)
        # 这里记录的new不是结果中的？
        self.news.append(prev_new)
        self.acs.append(ac)
        prev_act = self.acs[-2] if len(self.acs) > 1 else ac
        self.prevacs.append(prev_act)
        self.rews.append(rew)
        self.nextnew = new

        self.cur_ep_ret += rew
        self.cur_ep_len += 1

        if new:
            self.ep_rets.append(self.cur_ep_ret)
            self.ep_lens.append(self.cur_ep_len)
            self.cur_ep_ret = 0
            self.cur_ep_len = 0
        self.t += 1

    def output4replay__(self, cur_new, next_vpred):
        batch_size = len(self.rews)
        if self.t > 0 and cur_new == 1 and len(self.obs) > 0:
            # print("训练数据长度 " + str(len(self.obs)))
            return {"ob": np.array(self.obs), "rew": np.array(self.rews),
               "vpred": np.array(self.vpreds), "new": np.array(self.news),
               "ac": np.array(self.acs), "prevac": np.array(self.prevacs),
               "nextvpred": next_vpred * (1 - cur_new),
               "ep_rets": self.ep_rets, "ep_lens": self.ep_lens}, batch_size

        elif self.t > 0 and cur_new == 1 and len(self.obs) == 0:
            # TODO 是不是有更优雅的方式
            print('真的出现了new但是训练数据为空的情况')
        else:
            return None, batch_size


    def output4replay(self, cur_new, next_vpred):
        batch_size = len(self.rews)
        if self.t > 0 and cur_new == 1 and len(self.obs) > 0:
            # print("训练数据长度 " + str(len(self.obs)))
            return {"ob":self.obs, "rew": self.rews,
               "vpred": self.vpreds, "new": self.news,
               "ac": self.acs, "prevac": self.prevacs,
               "nextvpred": next_vpred * (1 - cur_new),
               "ep_rets": self.ep_rets, "ep_lens": self.ep_lens
            }, batch_size

        elif self.t > 0 and cur_new == 1 and len(self.obs) == 0:
            # TODO 是不是有更优雅的方式
            print('真的出现了new但是训练数据为空的情况')
        else:
            return None, batch_size