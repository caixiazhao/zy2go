# -*- coding: utf8 -*-
import collections

import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers

import baselines.common.tf_util as U
from baselines import deepq
from baselines.common.schedules import LinearSchedule
from baselines.deepq import PrioritizedReplayBuffer
from baselines.deepq import ReplayBuffer
from train.cmdactionenum import CmdActionEnum
from train.line_input import Line_input
from train.linemodel import LineModel
from util.rewardutil import RewardUtil
from util.stateutil import StateUtil

class LineModel_DQN:
    REWARD_RIVAL_DMG = 250

    def __init__(self, statesize, actionsize, heros, update_target_period=100, scope="deepq", initial_p=1.0, final_p=0.02):
        self.act = None
        self.train = None
        self.update_target = None
        self.debug = None

        self.state_size = statesize
        self.action_size = actionsize  # 50=8*mov+10*attack+10*skill1+10*skill2+10*skill3+回城+hold
        self.memory = PrioritizedReplayBuffer(500000, alpha=0.6)
        self.gamma = 0.9  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.e_decay = .99
        self.e_min = 0.05
        self.learning_rate = 0.01
        self.heros = heros
        self.scope = scope
        self.model = self._build_model

        # todo:英雄1,2普攻距离为2，后续需修改
        self.att_dist = 2

        self.act_times = 0
        self.train_times = 0
        self.update_target_period = update_target_period

        self.exploration = LinearSchedule(schedule_timesteps=3000, initial_p=initial_p, final_p=final_p)

        self.battle_rewards = []
        self.loss = []

    def model(self, inpt, num_actions, scope, reuse=False):
        """This model takes as input an observation and returns values of all actions."""
        with tf.variable_scope(scope, reuse=reuse):
            out = tf.contrib.layers.flatten(inpt)
            out = tf.nn.l2_normalize(out, 1)
            out = layers.fully_connected(out, num_outputs=256, activation_fn=tf.nn.relu)
            out = layers.fully_connected(out, num_outputs=128, activation_fn=tf.nn.relu)
            out = layers.fully_connected(out, num_outputs=128, activation_fn=tf.nn.relu)
            out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
            out = tf.nn.l2_normalize(out, 1)
            return out

    # 返回总信息向量大小=2*70+9*3+16*7=279
    def model2(self, input, num_actions, scope, reuse=False):
        """This model takes as input an observation and returns values of all actions."""
        with tf.variable_scope(scope, reuse=reuse):
            # 拆分成，英雄0~139，敌方塔140~157，己方塔158~166，敌方小兵167~222，己方小兵223~278
            heroes = tf.contrib.layers.flatten(tf.slice(input, [0, 0, 0], [-1, -1, 140]))
            rival_towers = tf.contrib.layers.flatten(tf.slice(input, [0, 0, 140], [-1, -1, 18]))
            team_towers = tf.contrib.layers.flatten(tf.slice(input, [0, 0, 158], [-1, -1, 9]))
            rival_units = tf.contrib.layers.flatten(tf.slice(input, [0, 0, 167], [-1, -1, 56]))
            team_units = tf.contrib.layers.flatten(tf.slice(input, [0, 0, 223], [-1, -1, 56]))

            heroes_out = layers.fully_connected(heroes, num_outputs=64, activation_fn=tf.nn.relu)
            heroes_out = layers.fully_connected(heroes_out, num_outputs=128, activation_fn=tf.nn.relu)

            rival_towers_out = layers.fully_connected(rival_towers, num_outputs=8, activation_fn=tf.nn.relu)
            rival_towers_out = layers.fully_connected(rival_towers_out, num_outputs=16, activation_fn=tf.nn.relu)

            team_towers_out = layers.fully_connected(team_towers, num_outputs=4, activation_fn=tf.nn.relu)
            team_towers_out = layers.fully_connected(team_towers_out, num_outputs=8, activation_fn=tf.nn.relu)

            rival_units_out = layers.fully_connected(rival_units, num_outputs=32, activation_fn=tf.nn.relu)
            rival_units_out = layers.fully_connected(rival_units_out, num_outputs=64, activation_fn=tf.nn.relu)

            team_units_out = layers.fully_connected(team_units, num_outputs=16, activation_fn=tf.nn.relu)
            team_units_out = layers.fully_connected(team_units_out, num_outputs=32, activation_fn=tf.nn.relu)

            out = tf.concat([heroes_out, rival_towers_out, team_towers_out, rival_units_out, team_units_out], 1)
            out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.relu)
            out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
            out = tf.nn.l2_normalize(out, 1)
            return out

    @property
    def _build_model(self):
        sess = U.get_session()
        if sess is None:
            sess = U.make_session(8)
            sess.__enter__()
        self.act, self.train, self.update_target, self.debug = deepq.build_train(
            make_obs_ph=lambda name: U.BatchInput(shape=[2, self.state_size], name=name),
            q_func=self.model2,
            num_actions=self.action_size,
            optimizer=tf.train.AdamOptimizer(learning_rate=5e-4),
            scope=self.scope,
            double_q=True,
            param_noise=True
        )

        # 初始化tf环境
        U.initialize()
        self.update_target()

    def load(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.restore(sess, name)

    def save(self, name):
        saver = tf.train.Saver(var_list=tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.scope))
        sess = U.get_session()
        saver.save(sess, name)

    def remember(self, prev_state, cur_state, new_state):
        added = False
        for hero_name in self.heros:
            action = cur_state.get_hero_action(hero_name)
            if action is not None:
                selected_action_idx = action.output_index
                reward = action.reward

                # 暂时将1v1的rival_hero 定义为对面英雄
                for hero in cur_state.heros:
                    if hero.hero_name != hero_name:
                        rival_hero = hero.hero_name
                        break

                prev_state_input = Line_input(prev_state, hero_name, rival_hero).gen_line_input()

                cur_line_input = Line_input(cur_state, hero_name, rival_hero)
                cur_state_input = cur_line_input.gen_line_input()

                new_line_input = Line_input(new_state, hero_name, rival_hero)
                new_state_input = new_line_input.gen_line_input()

                done = 1 if new_state.get_hero(hero_name).hp <= 0 else 0

                # 构造一个禁用action的数组
                # 因为会对next_q的计算有影响（-1是其中最大值，所以改成暂时不屏蔽任何选择）
                acts = np.zeros(self.action_size, dtype=float).tolist()
                new_state_action_flags = acts
                # new_state_action_flags = LineModel.remove_unaval_actions(acts, new_state, hero_name, rival_hero)
                # new_state_action_flags = [-1000 if a == -1 else 0 for a in new_state_action_flags]

                self.memory.add(np.array([prev_state_input, cur_state_input]), selected_action_idx, reward,
                                         np.array([cur_state_input, new_state_input]), float(done), new_state_action_flags)
                added = True
                self.act_times += 1

                self.battle_rewards.append(reward)
                if done == 1:
                    print('')
                    print('')
                    print('hero', hero_name, "战斗总奖励", np.sum(self.battle_rewards))
                    print('')
                    print('')
                    self.battle_rewards = []
        return added

    def if_replay(self, learning_batch):
        if self.act_times > learning_batch:
            return True
        return False

    def get_memory_size(self):
        return self.act_times

    def replay(self, batch_size):
        batch_size = min(batch_size, len(self.memory))
        obses_t, actions, rewards, obses_tp1, dones, new_avails, weights, idxes = self.memory.sample(batch_size, beta=0.4)
        td_error, rew_t_ph, q_t_selected_target, q_t_selected = self.train(obses_t, actions, rewards, obses_tp1, dones, weights, new_avails)
        self.loss.append(np.mean(td_error))
        new_priorities = np.abs(td_error) + 1e-6
        self.memory.update_priorities(idxes, new_priorities)

        self.train_times += 1
        if self.train_times % self.update_target_period == 0:
            print('model', self.scope, 'td_loss', td_error, "rew_t_ph", rew_t_ph, "q_t_selected_target", q_t_selected_target, "q_t_selected",
                  q_t_selected)
            print('model', self.scope, 'loss_mean', np.mean(self.loss))
            self.update_target()

    def get_action(self, prev_state, state_info, hero_name, rival_hero):
        prev_state_input = Line_input(prev_state, hero_name, rival_hero).gen_line_input()

        line_input = Line_input(state_info, hero_name, rival_hero)
        state_input = line_input.gen_line_input()

        input_detail = ' '.join(str("%f" % float(act)) for act in state_input)
        print(input_detail)

        state_input=np.array([[prev_state_input, state_input]])
        explor_value = self.exploration.value(self.act_times)
        print("dqn model exploration value is ", explor_value)
        actions = self.act(state_input, update_eps=explor_value)
        # print("d0", d0, "d1", d1, "d2", d2, "d3", d3, "d4", d4, "d5", d5)
        # action_detail = ' '.join(str("%.4f" % float(act)) for act in list(actions[0]))

        action=LineModel.select_actions(actions,state_info,hero_name, rival_hero)

        # print ("replay detail: selected: %s \n    input array:%s \n    action array:%s\n\n" %
        #        (str(action.output_index), input_detail, action_detail))
        return action

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

    @staticmethod
    def cal_target_v3(state_infos, state_idx, hero_name, rival_hero_name, line_idx):
        # 只计算当前帧的得失，得失为金币获取情况 + 敌方血量变化
        # 获得小兵死亡情况, 根据小兵属性计算他们的金币情况
        cur_state = state_infos[state_idx]
        cur_hero = cur_state.get_hero(hero_name)
        act_info = cur_state.get_hero_action(hero_name)
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        rival_team = cur_rival_hero.team
        cur_hero = cur_state.get_hero(hero_name)
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        next_state = state_infos[state_idx + 1]
        next_hero = next_state.get_hero(hero_name)
        next_next_state = state_infos[state_idx + 2]
        next_next_hero = next_next_state.get_hero(hero_name)
        dead_units = StateUtil.get_dead_units_in_line(next_state, rival_team, line_idx)
        dead_golds = sum([StateUtil.get_unit_value(u.unit_name, u.cfg_id) for u in dead_units])
        dead_unit_str = (','.join([u.unit_name for u in dead_units]))

        # 如果英雄有小额金币变化，则忽略
        gold_delta = next_hero.gold - cur_hero.gold
        if gold_delta % 10 == 3 or gold_delta % 10 == 8 or gold_delta == int(dead_golds / 2) + 3:
            gold_delta -= 3

        # 暂时解决不了的是释放技能，延迟造成的金币获得

        # 忽略英雄死亡的奖励金，这部分金币在其他地方计算
        # 这里暂时将英雄获得金币清零了，因为如果英雄表现好（最后一击，会在后面有所加成）
        # TODO 这个金币奖励值应该是个变化值，目前取的是最小值
        prev_state_rival = state_infos[state_idx - 1].get_hero(rival_hero_name)
        if prev_state_rival.hp > 0 and cur_rival_hero.hp <= 0 and gold_delta >= 80 > dead_golds:
            print("敌方英雄死亡奖励，扣减")
            gold_delta = int(dead_golds / 2)

        # 计算对指定敌方英雄造成的伤害，计算接受的伤害
        # 伤害信息和击中信息都有延迟，在两帧之后（但是一般会出现在同一条信息中，偶尔也会出现在第二条中）
        # 扩大自己受到伤害的惩罚
        # 扩大对方低血量下受到伤害的奖励
        # 扩大攻击伤害的权重
        # TODO 防御型辅助型法术的定义，辅助法术不能乱放，否则惩罚
        dmg = StateUtil.get_attack_cast_dmg(cur_state, next_state, next_next_state, hero_name, rival_hero_name) / float(cur_rival_hero.maxhp)
        dmg *= 3 * cur_rival_hero.maxhp / float(cur_rival_hero.hp + cur_rival_hero.maxhp)

        # 估算玩家接收的伤害时候，我们考虑后两帧的伤害的平均值，因为有些伤害会有延迟，比如小兵和建筑的攻击，因为弹道和攻速，血量变化会有延迟
        self_hp_loss = (cur_hero.hp - next_next_hero.hp) / float(cur_hero.maxhp) / 2 if (
            cur_hero.hp >= next_hero.hp >= next_next_hero.hp) else 0
        self_hp_loss *= 3 * cur_hero.maxhp / float(cur_hero.hp + cur_hero.maxhp)
        dmg_delta = int((dmg - self_hp_loss) * LineModel.REWARD_RIVAL_DMG)

        hit_rival_tower_dmg_ratio = StateUtil.get_hit_rival_tower_dmg_ratio(cur_state, next_state, next_next_state, hero_name)

        # # 计算塔的被攻击情况
        # self_tower_hp_change, destroyed = StateUtil.get_tower_hp_change(cur_state, next_state, hero_name, line_idx, self_tower=True)
        # rival_tower_hp_change, _ = StateUtil.get_tower_hp_change(cur_state, next_state, hero_name, line_idx, self_tower=False)

        # 统计和更新变量
        print('reward debug info, hero: %s, max_gold: %s, gold_gain: %s, dmg: %s, hp_loss: %s, dmg_delta: %s, '
            'dead_units: %s, rival_tower: %s'
            % (hero_name, str(dead_golds), str(gold_delta), str(dmg), str(self_hp_loss), str(dmg_delta), dead_unit_str,
               hit_rival_tower_dmg_ratio))

        # 最大奖励是击杀小兵和塔的金币加上对方一条命血量的奖励
        # 最大惩罚是被对方造成了一条命伤害
        # 零分为获得了所有的死亡奖励
        reward = float(gold_delta + dmg_delta) / 100 + hit_rival_tower_dmg_ratio

        # 特殊情况处理
        # 鼓励攻击对方小兵
        if_hit_unit = next_next_state.if_hero_hit_any_unit(hero_name, rival_hero_name)
        if if_hit_unit is not None:
            print("物理攻击到了小兵", if_hit_unit)
            reward += 0.01

        # 撤退的话首先将惩罚值设置为-0.2吧
        # cur_state = state_infos[state_idx]
        # hero_action = cur_state.get_hero_action(hero_name)
        # if hero_action.output_index == 48:
        #     if float(cur_hero.hp) / cur_hero.maxhp > 0.7:
        #         print('高血量撤退')
        #         reward = -1
        #     else:
        #         print('撤退基础惩罚')
        #         reward = -0.2

        # # 特定英雄的大招必须要打到英雄才行
        # if_cast_ultimate_skill = RewardUtil.if_cast_skill(state_infos, state_idx, hero_name, 3)
        # if if_cast_ultimate_skill:
        #     if_skill_hit_rival = RewardUtil.if_skill_hit_hero(state_infos, state_idx, hero_name, 3, rival_hero_name)
        #     if not if_skill_hit_rival:
        #         print('特定英雄的大招必须要打到英雄才行')
        #         reward = -1
        #
        # # 是否离线太远
        # cur_state = state_infos[state_idx]
        # leave_line = RewardUtil.if_hero_leave_line(state_infos, state_idx, hero_name, line_idx)
        # if leave_line:
        #     print('离线太远')
        #     reward = -1
        #
        # # 暂时忽略模型选择立刻离开选择范围这种情况，让英雄可以在危险时候拉远一些距离
        # if RewardUtil.if_leave_linemodel_range(state_infos, state_idx, hero_name, line_idx):
        #     if hero_action.output_index != 48:
        #         print('离开模型范围，又不是撤退')
        #         reward = -1

        # 特殊奖励，放在最后面
        # 英雄击杀最后一击，直接最大奖励
        cur_state = state_infos[state_idx]
        cur_hero = cur_state.get_hero(hero_name)
        cur_rival_hero = cur_state.get_hero(rival_hero_name)
        next_state = state_infos[state_idx + 1]
        next_hero = next_state.get_hero(hero_name)
        next_rival = next_state.get_hero(rival_hero_name)
        if cur_rival_hero.hp > 0 and next_rival.hp <= 0:
            print('对线英雄%s死亡' % rival_hero_name)
            next_next_state = state_infos[state_idx + 2]
            dmg_hit_rival = next_next_state.get_hero_total_dmg(hero_name, rival_hero_name)
            if dmg_hit_rival > 0:
                print('英雄%s对对方造成了最后一击' % hero_name)
                reward = 1

        if cur_hero.hp > 0 and next_hero.hp <= 0:
            reward = -1
        return min(max(reward, -1), 1)
