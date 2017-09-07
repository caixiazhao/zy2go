import gym
import itertools
import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers

import baselines.common.tf_util as U

from baselines import logger
from baselines import deepq
from baselines.deepq.replay_buffer import ReplayBuffer, PrioritizedReplayBuffer
from baselines.common.schedules import LinearSchedule


def model(inpt, num_actions, scope, reuse=False):
    """This model takes as input an observation and returns values of all actions."""
    with tf.variable_scope(scope, reuse=reuse):
        out = inpt
        out = tf.nn.l2_normalize(out, 1)
        # out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.tanh)
        # out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
        out = layers.fully_connected(out, num_outputs=512, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=256, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=256, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
        # out = layers.layer_norm(out, center=True, scale=True)
        return out


if __name__ == '__main__':
    with U.make_session(8):
        # Create the environment
        env = gym.make("CartPole-v0")
        # Create all the functions necessary to train the model
        act, train, update_target, debug = deepq.build_train(
            make_obs_ph=lambda name: U.BatchInput(env.observation_space.shape, name=name),
            q_func=model,
            num_actions=env.action_space.n,
            optimizer=tf.train.AdamOptimizer(learning_rate=5e-4),
            param_noise=False
        )
        # Create the replay buffer
        replay_buffer = PrioritizedReplayBuffer(50000, alpha=0.6)
        # Create the schedule for exploration starting from 1 (every action is random) down to
        # 0.02 (98% of actions are selected according to values predicted by the model).
        exploration = LinearSchedule(schedule_timesteps=10000, initial_p=1.0, final_p=0.02)

        # Initialize the parameters and copy them to the target network.
        U.initialize()
        update_target()

        tvars = tf.trainable_variables()
        tvars_vals = U.get_session().run(tvars)

        for var, val in zip(tvars, tvars_vals):
            print(var.name, val)

        episode_rewards = [0.0]
        loss_array = []
        obs = env.reset()
        for t in itertools.count():
            # Take action and update exploration to the newest value
            action = act(obs[None], update_eps=exploration.value(t))[0]
            # print(action)
            action = list(action)
            maxQ = max(action)
            selected = action.index(maxQ)
            new_obs, rew, done, _ = env.step(selected)
            # Store transition in the replay buffer.
            avail = np.zeros(env.action_space.n, dtype=float).tolist()
            replay_buffer.add(obs, selected, rew, new_obs, float(done), avail)
            obs = new_obs

            episode_rewards[-1] += rew
            if done:
                obs = env.reset()
                episode_rewards.append(0)

            is_solved = t > 100 and np.mean(episode_rewards[-101:-1]) >= 200
            td_error, rew_t_ph, q_t_selected_target, q_t_selected = -1, -1, -1, -1
            if is_solved:
                # Show off the result
                env.render()
            else:
                # Minimize the error in Bellman's equation on a batch sampled from replay buffer.
                if t > 1000:
                    obses_t, actions, rewards, obses_tp1, dones, avail, weights, idxes = replay_buffer.sample(32, beta=0.4)
                    td_error, rew_t_ph, q_t_selected_target, q_t_selected = train(obses_t, actions, rewards, obses_tp1, dones, weights, avail)
                    loss_array.append(np.mean(td_error))
                    new_priorities = np.abs(td_error) + 1e-6
                    replay_buffer.update_priorities(idxes, new_priorities)
                # Update target network periodically.
                if t % 1000 == 0:
                    update_target()

            if done and len(episode_rewards) % 10 == 0:
                logger.record_tabular("steps", t)
                logger.record_tabular("episodes", len(episode_rewards))
                logger.record_tabular("mean episode reward", round(np.mean(episode_rewards[-101:-1]), 1))
                logger.record_tabular("% time spent exploring", int(100 * exploration.value(t)))
                logger.record_tabular("loss", np.mean(loss_array[-101:-1]))
                logger.dump_tabular()

                print('td_loss', td_error, "rew_t_ph", rew_t_ph, "q_t_selected_target", q_t_selected_target,
                  "q_t_selected", q_t_selected)
