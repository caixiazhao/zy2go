import tensorflow as tf
import numpy as np
import baselines.common.tf_util as U
import sys

def main():
    sess = U.make_session(8)
    sess.__enter__()
    U.initialize()
    # new_variables = set(tf.global_variables()) - set()
    # sess.run(tf.variables_initializer(new_variables))

    # Create a tensor of shape [2, 3] consisting of random normal values, with mean
    # -1 and standard deviation 4.
    norm = tf.random_normal([2, 3], mean=-1, stddev=4)

    # Shuffle the first dimension of a tensor
    c = tf.constant([[1, 2], [3, 4], [5, 6]])
    shuff = tf.random_shuffle(c)

    # Each time we run these ops, different results are generated
    # sess = tf.Session()
    # print(sess.run(norm))
    # print(sess.run(norm))
    #
    # # Set an op-level seed to generate repeatable sequences across sessions.
    # norm = tf.random_normal([2, 3], seed=1234)
    # sess = tf.Session()
    # print(sess.run(norm))
    # print(sess.run(norm))
    # sess = tf.Session()
    # print(sess.run(norm))
    # print(sess.run(norm))
    #
    # norm = tf.random_normal([15], seed=1234)
    # acts = np.ones(15, dtype=float)
    # acts[3] = -1
    # acts = [-1000 if a == -1 else 0 for a in acts]
    # print(acts)
    # b = tf.constant(acts, dtype=tf.float32)
    # c = tf.add(norm, b)
    # normalized = tf.nn.l2_normalize(norm, 0)
    # sess = tf.Session()
    # print(sess.run([norm, c, normalized]))
    #
    # one_hot = tf.one_hot(1, 5)
    # sess = tf.Session()
    # print(sess.run(one_hot))
    #
    # eps = 0.5
    # chose_random = tf.random_uniform(tf.stack([100]), minval=0, maxval=1, dtype=tf.float32, seed=1234)
    # result = chose_random < eps
    # sess = tf.Session()
    # print(sess.run([chose_random, result]))
    #
    # norm = tf.random_normal([2, 2, 15], seed=1234)
    # normalized = tf.nn.l2_normalize(norm, 2)
    # flatten = tf.contrib.layers.flatten(normalized)
    # sess = tf.Session()
    # print(sess.run([norm, normalized, flatten]))

    rand = np.random.rand(3, 20)
    sub1 = rand[:,2:3]
    sub2 = rand[:,3:6]
    o = tf.constant(rand, dtype=tf.float32)
    a = tf.constant(sub1, dtype=tf.float32)
    b = tf.constant(sub2, dtype=tf.float32)
    s = tf.slice(o, [0, 2], [-1, 4])
    c = tf.concat([a, b], 1)
    print(rand)
    print(sess.run([a, b, c, s]))


if __name__ == "__main__":
    main()