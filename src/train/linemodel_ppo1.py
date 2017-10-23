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
import random


class LineModel_PPO1:
    REWARD_RIVAL_DMG = 250

    def __init__(self, statesize, actionsize, hero, ob, ac,
                 policy_func=None,
                 update_target_period=100, scope="ppo1", schedule_timesteps=10000, initial_p=0, final_p=0,
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

        self.exploration = LinearSchedule(schedule_timesteps=schedule_timesteps, initial_p=initial_p, final_p=final_p)
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

            var_list = self.pi.get_trainable_variables()

            # more debug info
            debug_atarg = atarg
            pi_ac = self.pi.pd.logp(ac)
            opi_ac = self.oldpi.pd.logp(ac)
            vpred = U.mean(self.pi.vpred)
            pi_pd = U.mean(self.pi.pd.flatparam())
            opi_pd = self.oldpi.pd.flatparam()[0]
            kl_oldnew = kloldnew[0]
            grads = tf.gradients(total_loss, var_list)

            losses = [pol_surr, pol_entpen, vf_loss, meankl, meanent]
            debugs = [debug_atarg, pi_ac, opi_ac, vpred, pi_pd, opi_pd, kl_oldnew, total_loss]

            self.lossandgrad = U.function([ob, ac, atarg, ret, lrmult], losses + debugs + [var_list, grads] + [U.flatgrad(total_loss, var_list)])
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
            self.rews[i] = reward
            self.t += 1

            self.cur_ep_ret += reward
            self.cur_ep_len += 1
            if new:
                self.ep_rets.append(self.cur_ep_ret)
                self.ep_lens.append(self.cur_ep_len)
                self.cur_ep_ret = 0
                self.cur_ep_len = 0

    def get_memory_size(self):
        return self.iters_so_far

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
    def replay(self, seg, batch_type):
        print(self.scope + " training")

        if self.schedule == 'constant':
            cur_lrmult = 1.0
        elif self.schedule == 'linear':
            cur_lrmult = max(1.0 - float(self.timesteps_so_far) / self.max_timesteps, 0)

        self.add_vtarg_and_adv(seg, self.gamma, self.lam)

        print(seg)

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
            # 完整的拿所有行为
            batch_size = self.optim_batchsize if batch_type == 0 else d.n
            # for batch in d.iterate_once(self.optim_batchsize): 这是给原始分段ppo的
            for batch in d.iterate_once(batch_size):
                # print("ob", batch["ob"], "ac", batch["ac"], "atarg", batch["atarg"], "vtarg", batch["vtarg"])
                *newlosses, debug_atarg, pi_ac, opi_ac, vpred, pi_pd, opi_pd, kl_oldnew, total_loss, var_list, grads, g = \
                    self.lossandgrad(batch["ob"], batch["ac"], batch["atarg"], batch["vtarg"], cur_lrmult)
                # print("debug_atarg", debug_atarg, "pi_ac", pi_ac, "opi_ac", opi_ac, "vpred", vpred, "pi_pd", pi_pd,
                #       "opi_pd", opi_pd, "kl_oldnew", kl_oldnew, "var_mean", np.mean(g), "total_loss", total_loss)
                if np.isnan(np.mean(g)):
                    debug = 1
                    print('output nan, ignore it!')
                else:
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
        last_rew = self.rewbuffer[-1] if len(self.rewbuffer) > 0 else 0
        logger.record_tabular("LastRew", last_rew)
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
        logger.record_tabular("IterSoFar", self.iters_so_far)
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
        explor_value = self.exploration.value(self.act_times)
        # print("ppo1 model exploration value is ", explor_value)
        actions, vpred = self.pi.act(stochastic=stochastic, update_eps=explor_value, ob=state_input)
        actions = np.array([actions])

        action = LineModel.select_actions(actions, state_info, hero_name, rival_hero)
        action.vpred = vpred

        # 需要返回一个已经标注了不可用行为的（逻辑有点冗余）
        action_ratios = list(actions[0])
        action_ratios_masked = LineModel.remove_unaval_actions(action_ratios, state_info, hero_name, rival_hero)

        # print ("replay detail: selected: %s \n    input array:%s \n    action array:%s\n\n" %
        #        (str(action.output_index), input_detail, action_detail))
        return action, explor_value, action_ratios_masked

    @staticmethod
    # 只使用当前帧（做决定帧）+下一帧来计算奖惩，目的是在游戏结束时候可以计算所有之前行为的奖惩，不会因为需要延迟n下而没法计算
    # 另外最核心的是，ppo本身就不要要求奖惩值是根据上一个行动来得到的
    def cal_target_ppo(prev_state, cur_state, next_state, hero_name, rival_hero_name, line_idx):
        # 只计算当前帧的得失，得失为金币获取情况 + 敌方血量变化
        # 获得小兵死亡情况, 根据小兵属性计算他们的金币情况
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        rival_team = cur_rival_hero.team
        cur_hero = cur_state.get_hero(hero_name)
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        next_hero = next_state.get_hero(hero_name)
        next_rival_hero = next_state.get_hero(rival_hero_name)
        # 找到英雄附近死亡的敌方小兵
        dead_units = StateUtil.get_dead_units_in_line(next_state, rival_team, line_idx, cur_hero, StateUtil.GOLD_GAIN_RADIUS)
        dead_golds = sum([StateUtil.get_unit_value(u.unit_name, u.cfg_id) for u in dead_units])
        dead_unit_str = (','.join([u.unit_name for u in dead_units]))

        # 如果英雄有小额金币变化，则忽略
        gold_delta = next_hero.gold - cur_hero.gold
        if gold_delta % 10 == 3 or gold_delta % 10 == 8 or gold_delta == int(dead_golds / 2) + 3:
            gold_delta -= 3

        # 很难判断英雄的最后一击，所以我们计算金币变化，超过死亡单位一半的金币作为英雄获得金币
        gold_delta = gold_delta * 2 - dead_golds
        if gold_delta < 0:
            print('获得击杀金币不应该小于零', cur_state.tick, 'dead_units', dead_unit_str, 'gold_gain', (next_hero.gold - cur_hero.gold))
            gold_delta = 0

        if dead_golds > 0:
            print('dead_gold', dead_golds, 'delta_gold', gold_delta, "hero", hero_name, "tick", cur_state.tick)

        # 计算对指定敌方英雄造成的伤害，计算接受的伤害
        # 伤害信息和击中信息都有延迟，在两帧之后（但是一般会出现在同一条信息中，偶尔也会出现在第二条中）
        # 这里只计算下一帧中英雄对对方造成的伤害
        # 扩大自己受到伤害的惩罚
        # 扩大对方低血量下受到伤害的奖励
        # 扩大攻击伤害的权重
        # TODO 防御型辅助型法术的定义，辅助法术不能乱放，否则惩罚
        dmg = next_state.get_hero_total_dmg(hero_name, rival_hero_name) / float(cur_rival_hero.maxhp)
        dmg *= 3 * cur_rival_hero.maxhp / float(cur_rival_hero.hp + cur_rival_hero.maxhp)

        # 估算玩家接收的伤害时候，只考虑下一帧中的变化，像塔的攻击需要飞行所有有延迟这种情况这里不需要考虑
        self_hp_loss = (cur_hero.hp - next_hero.hp) / float(cur_hero.maxhp) / 2 if (
            cur_hero.hp >= next_hero.hp >= next_hero.hp) else 0
        self_hp_loss *= 3 * cur_hero.maxhp / float(cur_hero.hp + cur_hero.maxhp)
        dmg_delta = int((dmg - self_hp_loss) * LineModel.REWARD_RIVAL_DMG)

        # 统计和更新变量
        # print('reward debug info, hero: %s, max_gold: %s, gold_gain: %s, dmg: %s, hp_loss: %s, dmg_delta: %s, '
        #       'dead_units: %s'
        #       % (
        #       hero_name, str(dead_golds), str(gold_delta), str(dmg), str(self_hp_loss), str(dmg_delta), dead_unit_str))

        # 最大奖励是击杀小兵和塔的金币加上对方一条命血量的奖励
        # 最大惩罚是被对方造成了一条命伤害
        # 零分为获得了所有的死亡奖励
        reward = float(gold_delta + dmg_delta) / 100

        # 特殊情况处理
        # 鼓励攻击对方小兵,塔
        if_hit_unit = next_state.if_hero_hit_any_unit(hero_name, rival_hero_name)
        if if_hit_unit is not None:
            # print("物理攻击到了小兵", if_hit_unit)
            reward += 0.01
        if_hit_tower = next_state.if_hero_hit_tower(hero_name)
        if if_hit_tower is not None:
            # print("物理攻击到了塔", if_hit_tower)
            reward += 0.01

        # 将所有奖励缩小
        final_reward = reward / 10
        final_reward = min(max(final_reward, -1), 1)

        # 特殊奖励，放在最后面
        # 英雄击杀最后一击，直接最大奖励(因为gamma的存在，扩大这个惩罚）
        if cur_rival_hero.hp > 0 and next_rival_hero.hp <= 0:
            # print('对线英雄%s死亡' % rival_hero_name)
            dmg_hit_rival = next_state.get_hero_total_dmg(hero_name, rival_hero_name)
            if dmg_hit_rival > 0:
                # print('英雄%s对对方造成了最后一击' % hero_name)
                final_reward = 1
                if cur_hero.hp > 0 and next_hero.hp <= 0:
                    final_reward = 0
        elif cur_hero.hp > 0 and next_hero.hp <= 0:
            print('英雄死亡')
            final_reward = -5
        return final_reward

    @staticmethod
    # 只使用当前帧（做决定帧）+下一帧来计算奖惩，目的是在游戏结束时候可以计算所有之前行为的奖惩，不会因为需要延迟n下而没法计算
    # 另外最核心的是，ppo本身就不要要求奖惩值是根据上一个行动来得到的
    def cal_target_ppo_2(prev_state, cur_state, next_state, hero_name, rival_hero_name, line_idx):
        # 只计算当前帧的得失，得失为金币获取情况 + 敌方血量变化
        # 获得小兵死亡情况, 根据小兵属性计算他们的金币情况
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        rival_team = cur_rival_hero.team
        cur_hero = cur_state.get_hero(hero_name)
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        next_hero = next_state.get_hero(hero_name)
        next_rival_hero = next_state.get_hero(rival_hero_name)
        # 找到英雄附近死亡的敌方小兵
        dead_units = StateUtil.get_dead_units_in_line(next_state, rival_team, line_idx, cur_hero,
                                                      StateUtil.GOLD_GAIN_RADIUS)
        dead_golds = sum([StateUtil.get_unit_value(u.unit_name, u.cfg_id) for u in dead_units])
        dead_unit_str = (','.join([u.unit_name for u in dead_units]))

        # 如果英雄有小额金币变化，则忽略
        gold_delta = next_hero.gold - cur_hero.gold
        if gold_delta % 10 == 3 or gold_delta % 10 == 8 or gold_delta == int(dead_golds / 2) + 3:
            gold_delta -= 3

        # 很难判断英雄的最后一击，所以我们计算金币变化，超过死亡单位一半的金币作为英雄获得金币
        gold_delta = gold_delta * 2 - dead_golds
        if gold_delta < 0:
            print('获得击杀金币不应该小于零', cur_state.tick, 'dead_units', dead_unit_str, 'gold_gain',
                  (next_hero.gold - cur_hero.gold))
            gold_delta = 0

        if dead_golds > 0:
            print('dead_gold', dead_golds, 'delta_gold', gold_delta, "hero", hero_name, "tick", cur_state.tick)

        reward = float(gold_delta) / 100

        # 将所有奖励缩小
        final_reward = reward / 100
        final_reward = min(max(final_reward, -1), 1)

        # 特殊奖励，放在最后面
        # 英雄击杀最后一击，直接最大奖励(因为gamma的存在，扩大这个惩罚）
        if cur_rival_hero.hp > 0 and next_rival_hero.hp <= 0:
            # print('对线英雄%s死亡' % rival_hero_name)
            dmg_hit_rival = next_state.get_hero_total_dmg(hero_name, rival_hero_name)
            if dmg_hit_rival > 0:
                # print('英雄%s对对方造成了最后一击' % hero_name)
                final_reward = 1
                if cur_hero.hp > 0 and next_hero.hp <= 0:
                    final_reward = 0
        elif cur_hero.hp > 0 and next_hero.hp <= 0:
            print('英雄死亡')
            final_reward = -1
        return final_reward
