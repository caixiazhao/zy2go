"""
solving pendulum using actor-critic model
"""

import gym
import numpy as np
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Input, Lambda
from keras.layers.merge import Add, Multiply
from keras.optimizers import Adam
import keras.backend as K

import tensorflow as tf

import random
from collections import deque


# determines how to assign values to each state, i.e. takes the state
# and action (two-input model) and determines the corresponding value
class ActorCritic:
    def __init__(self, env, sess):
        self.env = env
        self.sess = sess

        self.learning_rate = 0.001
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = .995
        self.gamma = .95
        self.tau = .125

        # ===================================================================== #
        #                               Actor Model                             #
        # Chain rule: find the gradient of chaging the actor network params in  #
        # getting closest to the final value network predictions, i.e. de/dA    #
        # Calculate de/dA as = de/dC * dC/dA, where e is error, C critic, A act #
        # ===================================================================== #

        self.memory = deque(maxlen=2000)
        self.actor_state_input, self.actor_model = self.create_actor_model()
        _, self.target_actor_model = self.create_actor_model()

        self.actor_critic_grad = tf.placeholder(tf.float32,
                                                [None, self.env.action_space.shape[
                                                    0]])  # where we will feed de/dC (from critic)

        actor_model_weights = self.actor_model.trainable_weights
        self.actor_grads = tf.gradients(self.actor_model.output,
                                        actor_model_weights, -self.actor_critic_grad)  # dC/dA (from actor)
        grads = zip(self.actor_grads, actor_model_weights)
        self.optimize = tf.train.AdamOptimizer(self.learning_rate).apply_gradients(grads)

        # ===================================================================== #
        #                              Critic Model                             #
        # ===================================================================== #

        self.critic_state_input, self.critic_action_input, \
        self.critic_model = self.create_critic_model()
        _, _, self.target_critic_model = self.create_critic_model()

        self.critic_grads = tf.gradients(self.critic_model.output,
                                         self.critic_action_input)  # where we calcaulte de/dC for feeding above

        # Initialize for later gradient calculations
        self.sess.run(tf.initialize_all_variables())

    # ========================================================================= #
    #                              Model Definitions                            #
    # ========================================================================= #

    def create_actor_model(self):
        state_input = Input(shape=self.env.observation_space.shape)
        h1 = Dense(24, activation='relu')(state_input)
        h2 = Dense(48, activation='relu')(h1)
        h3 = Dense(24, activation='relu')(h2)
        output = Dense(self.env.action_space.shape[0], activation='tanh')(h3)
        output = Lambda(lambda x: 2 * x, output_shape=(1,))(output)  # Since the output range is -2 to 2

        model = Model(input=state_input, output=output)
        adam = Adam(lr=0.001)
        model.compile(loss="mse", optimizer=adam)
        return state_input, model

    def create_critic_model(self):
        state_input = Input(shape=self.env.observation_space.shape)
        state_h1 = Dense(24, activation='relu')(state_input)
        state_h2 = Dense(48)(state_h1)

        action_input = Input(shape=self.env.action_space.shape)
        action_h1 = Dense(48)(action_input)

        merged = Add()([state_h2, action_h1])
        merged_h1 = Dense(24, activation='relu')(merged)
        output = Dense(1, activation='linear')(merged_h1)
        model = Model(input=[state_input, action_input], output=output)

        adam = Adam(lr=0.001)
        model.compile(loss="mse", optimizer=adam)
        return state_input, action_input, model

    # ========================================================================= #
    #                               Model Training                              #
    # ========================================================================= #

    def remember(self, cur_state, action, reward, new_state, done):
        self.memory.append([cur_state[0], action[0], reward[0], new_state[0], done])

    def gradients(self, states, actions):
        return self.sess.run(self.critic_grads, feed_dict={
            self.critic_state_input: states,
            self.critic_action_input: actions
        })[0]

    def _train_actor(self, samples):
        cur_states = np.asarray([e[0] for e in samples])
        predicted_actions = self.actor_model.predict(cur_states)
        grads = self.gradients(cur_states, predicted_actions)

        self.sess.run(self.optimize, feed_dict={
            self.actor_state_input: cur_states,
            self.actor_critic_grad: grads
        })

    def _train_critic(self, samples):
        cur_states = np.asarray([e[0] for e in samples])
        actions = np.asarray([e[1] for e in samples])
        rewards = np.asarray([e[2] for e in samples])
        new_states = np.asarray([e[3] for e in samples])
        dones = np.asarray([e[4] for e in samples])
        target_new_states = self.target_actor_model.predict(new_states)
        target_q_values = self.target_critic_model.predict([new_states, target_new_states])

        for k in range(len(samples)):
            if not dones[k]:
                rewards[k] += self.gamma * target_q_values[k]

        loss = self.critic_model.train_on_batch([cur_states, actions], rewards)

        return loss

    def train(self):
        batch_size = 32
        if len(self.memory) < batch_size:
            return 0

        samples = random.sample(self.memory, batch_size)
        loss = self._train_critic(samples)
        self._train_actor(samples)
        self.update_target()
        return loss

    # ========================================================================= #
    #                         Target Model Updating                             #
    # ========================================================================= #

    def _update_actor_target(self):
        actor_model_weights = self.actor_model.get_weights()
        actor_target_weights = self.target_actor_model.get_weights()
        for i in xrange(len(actor_model_weights)):
            actor_target_weights[i] = self.tau * actor_model_weights[i] + (1 - self.tau) * actor_target_weights[i]
        self.target_actor_model.set_weights(actor_target_weights)

    def _update_critic_target(self):
        critic_weights = self.critic_model.get_weights()
        critic_target_weights = self.target_critic_model.get_weights()
        for i in xrange(len(critic_weights)):
            critic_target_weights[i] = self.tau * critic_weights[i] + (1 - self.tau) * critic_target_weights[i]
        self.target_critic_model.set_weights(critic_target_weights)

    def update_target(self):
        self._update_actor_target()
        self._update_critic_target()

    # ========================================================================= #
    #                              Model Predictions                            #
    # ========================================================================= #

    def act(self, cur_state):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        # if random.random() < 0.2:
        if np.random.rand() <= self.epsilon:
            print("random")
            return self.env.action_space.sample()
        return self.actor_model.predict(cur_state)


def main():
    sess = tf.Session()
    K.set_session(sess)
    env = gym.make("Pendulum-v0")
    actor_critic = ActorCritic(env, sess)

    num_trials = 0
    trial_len = 10000

    cur_state = env.reset()
    action = env.action_space.sample()
    while True:
        step = 0
        loss = 0
        total_reward = 0
        while True:
            env.render()
            cur_state = cur_state.reshape((1, env.observation_space.shape[0]))
            action = actor_critic.act(cur_state)
            action = action.reshape((1, env.action_space.shape[0]))

            new_state, reward, done, _ = env.step(action)
            new_state = new_state.reshape((1, env.observation_space.shape[0]))

            actor_critic.remember(cur_state, action, reward, new_state, done)
            loss += actor_critic.train()
            total_reward += reward[0]

            print("num_trials", num_trials, "step", step, "action", action, "total_reward", total_reward, "loss", loss)

            cur_state = new_state
            step += 1

            if done:
                num_trials += 1
                cur_state = env.reset()
                break

        if num_trials >= trial_len:
            break

if __name__ == "__main__":
    main()