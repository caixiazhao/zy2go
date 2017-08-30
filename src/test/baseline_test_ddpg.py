import gym
import tensorflow as tf

import itertools
import numpy as np
import tensorflow as tf
import tensorflow.contrib.layers as layers

import baselines.common.tf_util as U
import random

from baselines import logger
from baselines import deepq
from baselines.ddpg.ddpg import DDPG
from baselines.ddpg.memory import Memory
from baselines.ddpg.models import Critic, Actor
from baselines.ddpg.noise import AdaptiveParamNoiseSpec
from baselines.deepq.replay_buffer import ReplayBuffer
from baselines.common.schedules import LinearSchedule

def model(inpt, num_actions, scope, reuse=False):
    """This model takes as input an observation and returns values of all actions."""
    with tf.variable_scope(scope, reuse=reuse):
        out = inpt
        out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.tanh)
        out = layers.fully_connected(out, num_outputs=64, activation_fn=tf.nn.tanh)
        out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
        return out


def main():
    with U.single_threaded_session() as sess:
        batch_size = 64
        current_noise_type = 'adaptive-param_0.2'
        _, stddev = current_noise_type.split('_')
        param_noise = AdaptiveParamNoiseSpec(initial_stddev=float(stddev), desired_action_stddev=float(stddev))
        param_noise_adaption_interval = 2
        env = gym.make("Pendulum-v0")

        nb_actions = env.action_space.shape[-1]
        layer_norm = True

        # Configure components.
        memory = Memory(limit=int(1e6), action_shape=env.action_space.shape,
                        observation_shape=env.observation_space.shape)
        critic = Critic(layer_norm=layer_norm)
        actor = Actor(nb_actions, layer_norm=layer_norm)

        # Seed everything to make things reproducible.
        seed = int(1000000 * np.random.rand())
        logger.info('seed={}, logdir={}'.format(seed, logger.get_dir()))
        tf.set_random_seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        env.seed(seed)

        max_action = env.action_space.high
        logger.info('scaling actions by {} before executing in env'.format(max_action))
        agent = DDPG(actor, critic, memory, env.observation_space.shape, env.action_space.shape,
                     batch_size=batch_size, param_noise=param_noise)
        logger.info('Using agent with the following configuration:')
        logger.info(str(agent.__dict__.items()))

        # Prepare everything.
        agent.initialize(sess)
        sess.graph.finalize()
        agent.reset()
        obs = env.reset()
        for t in itertools.count():
            episode_rewards = []
            done = False
            while not done:
                env.render()

                # Take action and update exploration to the newest value
                action, q = agent.pi(obs, apply_noise=True, compute_Q=True)
                new_obs, rew, done, _ = env.step(max_action * action)

                # Book-keeping.
                agent.store_transition(obs, action, rew, new_obs, done)
                obs = new_obs

                episode_rewards.append(rew)
                if done:
                    agent.reset()
                    obs = env.reset()

            nb_train_steps = 100
            epoch_adaptive_distances = []
            epoch_critic_losses = []
            epoch_actor_losses = []
            for t_train in range(nb_train_steps):
                # Adapt param noise, if necessary.
                if memory.nb_entries >= batch_size and t % param_noise_adaption_interval == 0:
                    distance = agent.adapt_param_noise()
                    epoch_adaptive_distances.append(distance)

                cl, al = agent.train()
                epoch_critic_losses.append(cl)
                epoch_actor_losses.append(al)
                agent.update_target_net()

            if t % 10 == 0:
                logger.record_tabular("steps", t)
                logger.record_tabular("episodes", len(episode_rewards))
                logger.record_tabular("mean episode reward", round(np.mean(episode_rewards), 1))
                logger.record_tabular('train/loss_actor', round(np.mean(epoch_actor_losses)))
                logger.record_tabular('train/loss_critic', round(np.mean(epoch_critic_losses)))
                logger.record_tabular('train/param_noise_distance', round(np.mean(epoch_adaptive_distances)))
                logger.dump_tabular()


if __name__ == "__main__":
    main()