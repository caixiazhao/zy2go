from baselines.common.mpi_running_mean_std import RunningMeanStd
import baselines.common.tf_util as U
import tensorflow as tf
import gym
from baselines.common.distributions import make_pdtype, CategoricalPdType
import tensorflow.contrib.layers as layers



class LinePPOModel(object):
    recurrent = False
    def __init__(self, name, ob_space, ac_space):
        self.scope = name
        with tf.variable_scope(name):
            self._init(ob_space, ac_space)
            self.scope = tf.get_variable_scope().name

    def _init(self, ob_space, ac_space):
        with tf.variable_scope(self.scope):
            self.pdtype = pdtype = CategoricalPdType(ac_space)
            ob = U.get_placeholder(name="ob", dtype=tf.float32, shape=[None, ob_space])

            out = ob
            out = layers.fully_connected(out, num_outputs=256, activation_fn=tf.nn.relu, weights_initializer=U.normc_initializer(1.0))
            out = layers.fully_connected(out, num_outputs=128, activation_fn=tf.nn.relu, weights_initializer=U.normc_initializer(1.0))

            self.batch_size = 1
            self.time_steps = tf.shape(out)[0]
            self.cell_size = 128
            out = tf.reshape(out, [-1, self.time_steps, self.cell_size], name='2_3D')
            lstm_cell = tf.contrib.rnn.BasicLSTMCell(self.cell_size, forget_bias=1.0, state_is_tuple=True)
            state = lstm_cell.zero_state(self.batch_size, tf.float32)
            # todo:batch normalize
            out, state = tf.nn.dynamic_rnn(lstm_cell, out, initial_state=state, time_major=False)
            out = tf.reshape(out, [-1, self.cell_size], name='2_2D')

            out = tf.nn.dropout(out, keep_prob=0.6)

            out = layers.fully_connected(out, num_outputs=128, activation_fn=tf.nn.relu, weights_initializer=U.normc_initializer(1.0))
            pdparam = U.dense(out, pdtype.param_shape()[0], "polfinal")
            self.vpred = U.dense(out, 1, "value")[:, 0]
            self.pd = pdtype.pdfromflat(pdparam)

            self.state_in = []
            self.state_out = []

            stochastic = tf.placeholder(dtype=tf.bool, shape=(), name="stochastic")

            update_eps = tf.placeholder(tf.float32, (), name="update_eps")
            deterministic_actions = self.pd.full_sample()  # tf.argmax(q_values, axis=1)
            random_actions = tf.random_uniform(tf.shape(deterministic_actions), minval=-1, maxval=1, dtype=tf.float32)
            chose_random = tf.random_uniform(tf.shape(deterministic_actions), minval=0, maxval=1, dtype=tf.float32) < update_eps
            stochastic_actions = tf.where(chose_random, random_actions, deterministic_actions)

            ac = U.switch(stochastic, stochastic_actions, self.pd.flatparam())
            self._act = U.function(inputs=[stochastic, update_eps, ob],
                                   outputs=[ac, self.vpred],
                                   givens={update_eps: -1.0, stochastic: True}
            )

    def act(self, ob, stochastic, update_eps):
        ac1, vpred1 = self._act(stochastic, update_eps, ob[None])
        return ac1[0], vpred1[0]

    def get_variables(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.scope)

    def get_trainable_variables(self):
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, self.scope)

    def get_initial_state(self):
        return []

