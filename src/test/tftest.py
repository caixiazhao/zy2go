import tensorflow as tf
import numpy as np
import baselines.common.tf_util as U

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
    sess = tf.Session()
    print(sess.run(norm))
    print(sess.run(norm))

    # Set an op-level seed to generate repeatable sequences across sessions.
    norm = tf.random_normal([2, 3], seed=1234)
    sess = tf.Session()
    print(sess.run(norm))
    print(sess.run(norm))
    sess = tf.Session()
    print(sess.run(norm))
    print(sess.run(norm))

    norm = tf.random_normal([2, 5], seed=1234)
    acts = np.ones(5, dtype=float)
    acts[3] = 0
    print(acts)
    b = tf.constant(acts, dtype=tf.float32)
    c = tf.multiply(norm, b)
    sess = tf.Session()
    print(sess.run(c))

    one_hot = tf.one_hot(1, 5)
    sess = tf.Session()
    print(sess.run(one_hot))

if __name__ == "__main__":
    main()