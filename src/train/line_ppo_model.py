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
            out = layers.fully_connected(out, num_outputs=128, activation_fn=tf.nn.relu, weights_initializer=U.normc_initializer(1.0))
            pdparam = U.dense(out, pdtype.param_shape()[0], "polfinal", U.normc_initializer(0.01))
            self.vpred = U.dense(out, 1, "value", U.normc_initializer(1.0))[:, 0]
            self.pd = pdtype.pdfromflat(pdparam)

            self.state_in = []
            self.state_out = []

            stochastic = tf.placeholder(dtype=tf.bool, shape=())
            ac = U.switch(stochastic, self.pd.full_sample(), self.pd.flatparam())
            self._act = U.function([stochastic, ob], [ac, self.vpred])

    def act(self, stochastic, ob):
        ac1, vpred1 =  self._act(stochastic, ob[None])
        return ac1[0], vpred1[0]
    def get_variables(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.scope)
    def get_trainable_variables(self):
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, self.scope)
    def get_initial_state(self):
        return []

