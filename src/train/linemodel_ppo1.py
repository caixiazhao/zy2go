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
from train.line_input_lite import Line_Input_Lite
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


class LineModel_PPO1:
    REWARD_RIVAL_DMG = 250

    def __init__(self, statesize, actionsize, hero, ob, ac,
                 policy_func=None,
                 update_target_period=100, scope="ppo1", initial_p=1.0, final_p=0.02,
                 gamma=0.99, lam=0.95,
                 optim_epochs=4, optim_stepsize=1e-3, optim_batchsize=64,  # optimization hypers
                 schedule='linear', max_timesteps=40e6
                 ):
        self.act = None
        self.train = None
        self.update_target = None
        self.debug = None

        self.state_size = statesize
        self.action_size = actionsize  # 50=8*mov+10*attack+10*skill1+10*skill2+10*skill3+回城+hold
        self.gamma = gamma  # discount rate
        self.lam = lam
        self.hero = hero
        self.scope = scope

        # todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist = 2

        self.act_times = 0
        self.train_times = 0
        self.update_target_period = update_target_period

        self.exploration = LinearSchedule(schedule_timesteps=5000, initial_p=initial_p, final_p=final_p)

        # Initialize history arrays
        self.obs = np.array([ob for _ in range(update_target_period)])
        self.rews = np.zeros(update_target_period, 'float32')
        self.vpreds = np.zeros(update_target_period, 'float32')
        self.news = np.zeros(update_target_period, 'int32')
        self.acs = np.array([ac for _ in range(update_target_period)])
        self.prevacs = self.acs.copy()
        self.schedule = schedule
        self.max_timesteps = max_timesteps
        self.t = 0

        self.optim_epochs = optim_epochs
        self.optim_stepsize = optim_stepsize
        self.optim_batchsize = optim_batchsize

        self.ep_rets = []
        self.ep_lens = []
        self.cur_ep_ret = 0
        self.cur_ep_len = 0

        self.lenbuffer = deque(maxlen=100)  # rolling buffer for episode lengths
        self.rewbuffer = deque(maxlen=100)  # rolling buffer for episode rewards
        self.episodes_so_far = 0
        self.timesteps_so_far = 0
        self.iters_so_far = 0

        policy_func = LinePPOModel if LinePPOModel is None else policy_func
        self._build_model(input_space=statesize, action_size=actionsize, policy_func=policy_func)

        self.tstart = time.time()

    def _build_model(self, input_space, action_size, policy_func,
                     clip_param=0.2, entcoeff=0.01,  # clipping parameter epsilon, entropy coeff
                     adam_epsilon=1e-5):
        sess = U.get_session()
        if sess is None:
            sess = U.make_session(8)
            sess.__enter__()

        # Setup losses and stuff
        # ----------------------------------------
        with tf.variable_scope(self.scope):
            self.pi = policy_func("pi", input_space, action_size)  # Construct network for new policy
            self.oldpi = policy_func("oldpi", input_space, action_size)  # Network for old policy
            atarg = tf.placeholder(dtype=tf.float32, shape=[None])  # Target advantage function (if applicable)
            ret = tf.placeholder(dtype=tf.float32, shape=[None])  # Empirical return

            lrmult = tf.placeholder(name='lrmult', dtype=tf.float32,
                                    shape=[])  # learning rate multiplier, updated with schedule
            clip_param = clip_param * lrmult  # Annealed cliping parameter epislon

            ob = U.get_placeholder_cached(name="ob")
            ac = self.pi.pdtype.sample_placeholder([None])

            kloldnew = self.oldpi.pd.kl(self.pi.pd)
            ent = self.pi.pd.entropy()
            meankl = U.mean(kloldnew)
            meanent = U.mean(ent)
            pol_entpen = (-entcoeff) * meanent

            ratio = tf.exp(self.pi.pd.logp(ac) - self.oldpi.pd.logp(ac))  # pnew / pold
            surr1 = ratio * atarg  # surrogate from conservative policy iteration
            surr2 = U.clip(ratio, 1.0 - clip_param, 1.0 + clip_param) * atarg  #
            pol_surr = - U.mean(tf.minimum(surr1, surr2))  # PPO's pessimistic surrogate (L^CLIP)
            vf_loss = U.mean(tf.square(self.pi.vpred - ret))
            total_loss = pol_surr + pol_entpen + vf_loss
            losses = [pol_surr, pol_entpen, vf_loss, meankl, meanent]

            var_list = self.pi.get_trainable_variables()
            self.lossandgrad = U.function([ob, ac, atarg, ret, lrmult], losses + [U.flatgrad(total_loss, var_list)])
            self.adam = MpiAdam(var_list, epsilon=adam_epsilon)

            self.assign_old_eq_new = U.function([], [], updates=[tf.assign(oldv, newv)
                                                            for (oldv, newv) in
                                                            zipsame(self.oldpi.get_variables(), self.pi.get_variables())])
            self.compute_losses = U.function([ob, ac, atarg, ret, lrmult], losses)

            U.initialize()
            self.adam.sync()

    def load(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.restore(sess, name)

    def save(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.save(sess, name)

    def gen_input(self, cur_state, hero_name, rival_hero):
        cur_line_input = Line_Input_Lite(cur_state, hero_name, rival_hero)
        cur_state_input = cur_line_input.gen_line_input()
        return cur_state_input

    def remember(self, cur_state, new_state, vpred, prevac):
        hero_name = self.hero
        action = cur_state.get_hero_action(hero_name)
        if action is not None:
            selected_action_idx = action.output_index
            reward = action.reward

            # 暂时将1v1的rival_hero 定义为对面英雄
            for hero in cur_state.heros:
                if hero.hero_name != hero_name:
                    rival_hero = hero.hero_name
                    break

            cur_line_input = Line_Input_Lite(cur_state, hero_name, rival_hero)
            cur_state_input = cur_line_input.gen_line_input()

            new_line_input = Line_Input_Lite(new_state, hero_name, rival_hero)
            new_state_input = new_line_input.gen_line_input()

            new = True if new_state.get_hero(hero_name).hp <= 0 else False

            i = self.t % self.update_target_period
            self.obs[i] = cur_state_input
            self.vpreds[i] = vpred
            self.news[i] = new
            self.acs[i] = selected_action_idx
            self.prevacs[i] = prevac
            self.t += 1
            self.rews[i] = reward

            self.cur_ep_ret += reward
            self.cur_ep_len += 1
            if new:
                self.ep_rets.append(self.cur_ep_ret)
                self.ep_lens.append(self.cur_ep_len)
                self.cur_ep_ret = 0
                self.cur_ep_len = 0

    def if_replay(self):
        if self.t >= self.update_target_period:
            return True
        if self.news[-1]:
            return True
        return False

    def get_memory_size(self):
        return self.t

    def add_vtarg_and_adv(self, seg, gamma, lam):
        """
        Compute target value using TD(lambda) estimator, and advantage with GAE(lambda)
        """
        new = np.append(seg["new"],
                        0)  # last element is only used for last vtarg, but we already zeroed it if last new = 1
        vpred = np.append(seg["vpred"], seg["nextvpred"])
        T = len(seg["rew"])
        seg["adv"] = gaelam = np.empty(T, 'float32')
        rew = seg["rew"]
        lastgaelam = 0
        for t in reversed(range(T)):
            nonterminal = 1 - new[t + 1]
            delta = rew[t] + gamma * vpred[t + 1] * nonterminal - vpred[t]
            gaelam[t] = lastgaelam = delta + gamma * lam * nonterminal * lastgaelam
            # print('gaelam', gaelam[t], 'rew', rew[t], 'vpred_t+1', vpred[t+1], 'vpred_t', vpred[t])
        seg["tdlamret"] = seg["adv"] + seg["vpred"]

    # 需要下一次行动的vpred，所以需要在执行完一次act之后计算是否replay
    def replay(self, seg):
        if self.schedule == 'constant':
            cur_lrmult = 1.0
        elif self.schedule == 'linear':
            cur_lrmult = max(1.0 - float(self.timesteps_so_far) / self.max_timesteps, 0)

        self.add_vtarg_and_adv(seg, self.gamma, self.lam)

        # print(seg)

        # ob, ac, atarg, ret, td1ret = map(np.concatenate, (obs, acs, atargs, rets, td1rets))
        ob, ac, atarg, tdlamret = seg["ob"], seg["ac"], seg["adv"], seg["tdlamret"]
        vpredbefore = seg["vpred"]  # predicted value function before udpate
        atarg = (atarg - atarg.mean()) / atarg.std()  # standardized advantage function estimate
        d = Dataset(dict(ob=ob, ac=ac, atarg=atarg, vtarg=tdlamret), shuffle=not self.pi.recurrent)

        if hasattr(self.pi, "ob_rms"): self.pi.ob_rms.update(ob)  # update running mean/std for policy

        self.assign_old_eq_new()  # set old parameter values to new parameter values
        logger.log("Optimizing...")
        loss_names = ["pol_surr", "pol_entpen", "vf_loss", "kl", "ent"]
        logger.log(fmt_row(13, loss_names))
        # Here we do a bunch of optimization epochs over the data
        for _ in range(self.optim_epochs):
            losses = []  # list of tuples, each of which gives the loss for a minibatch
            for batch in d.iterate_once(self.optim_batchsize):
                # print("ob", batch["ob"], "ac", batch["ac"], "atarg", batch["atarg"], "vtarg", batch["vtarg"])
                *newlosses, g = self.lossandgrad(batch["ob"], batch["ac"], batch["atarg"], batch["vtarg"], cur_lrmult)
                self.adam.update(g, self.optim_stepsize * cur_lrmult)
                losses.append(newlosses)
            logger.log(fmt_row(13, np.mean(losses, axis=0)))

        logger.log("Evaluating losses...")
        losses = []
        for batch in d.iterate_once(self.optim_batchsize):
            newlosses = self.compute_losses(batch["ob"], batch["ac"], batch["atarg"], batch["vtarg"], cur_lrmult)
            losses.append(newlosses)
        meanlosses, _, _ = mpi_moments(losses, axis=0)
        logger.log(fmt_row(13, meanlosses))
        for (lossval, name) in zipsame(meanlosses, loss_names):
            logger.record_tabular("loss_" + name, lossval)
        logger.record_tabular("ev_tdlam_before", explained_variance(vpredbefore, tdlamret))
        lrlocal = (seg["ep_lens"], seg["ep_rets"])  # local values
        listoflrpairs = MPI.COMM_WORLD.allgather(lrlocal)  # list of tuples
        lens, rews = map(self.flatten_lists, zip(*listoflrpairs))
        self.lenbuffer.extend(lens)
        self.rewbuffer.extend(rews)
        logger.record_tabular("LastLen", 0 if len(self.lenbuffer) <= 0 else self.lenbuffer[-1])
        logger.record_tabular("EpLenMean", np.mean(self.lenbuffer))
        logger.record_tabular("EpRewMean", np.mean(self.rewbuffer))
        logger.record_tabular("EpThisIter", len(lens))
        self.episodes_so_far += len(lens)
        self.timesteps_so_far += sum(lens)
        self.iters_so_far += 1
        logger.record_tabular("EpisodesSoFar", self.episodes_so_far)
        logger.record_tabular("TimestepsSoFar", self.timesteps_so_far)
        logger.record_tabular("TimeElapsed", time.time() - self.tstart)
        if MPI.COMM_WORLD.Get_rank() == 0:
            logger.dump_tabular()

    def flatten_lists(self, listoflists):
        return [el for list_ in listoflists for el in list_]

    def get_action(self, state_info, hero_name, rival_hero):
        self.act_times += 1

        line_input = Line_Input_Lite(state_info, hero_name, rival_hero)
        state_input = line_input.gen_line_input()
        state_input = np.array(state_input)

        # input_detail = ' '.join(str("%f" % float(act)) for act in state_input)
        # print(input_detail)

        stochastic = True
        actions, vpred = self.pi.act(stochastic, state_input)
        actions = np.array([actions])

        action = LineModel.select_actions(actions, state_info, hero_name, rival_hero)
        action.vpred = vpred

        # print ("replay detail: selected: %s \n    input array:%s \n    action array:%s\n\n" %
        #        (str(action.output_index), input_detail, action_detail))
        return action

    @staticmethod
    def get_reward(state_infos, state_index, hero_name, rival_hero, line_idx):
        return LineModel_DQN.cal_target_v3(state_infos, state_index, hero_name, rival_hero, line_idx)

    @staticmethod
    def update_state_rewards(state_infos, state_index, hero_names=None):
        state_info = state_infos[state_index]
        line_idx = 1
        if hero_names is None:
            hero_names = [h.hero_name for h in state_info.heros]
        for hero_name in hero_names:
            # TODO 这些参数应该是传入的
            # 只有有Action的玩家才评估行为打分
            hero_action = state_info.get_hero_action(hero_name)
            if hero_action is not None:
                rival_hero_name = '27' if hero_name == '28' else '28'
                reward = LineModel_DQN.cal_target_v3(state_infos, state_index, hero_name, rival_hero_name, line_idx)
                state_info.add_rewards(hero_name, reward)
        return state_info
