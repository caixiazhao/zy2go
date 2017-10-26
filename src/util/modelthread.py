import random
import threading
import time
import logging
import queue
import baselines.common.tf_util as U
import tensorflow as tf

from util.httputil import HttpUtil


class ModelThread(threading.Thread):

    logging.basicConfig(level=logging.DEBUG,
                        format='(%(threadName)-9s) %(message)s', )

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ModelThread,self).__init__()
        self.target = target
        self.name = name
        self.q = queue.Queue()
        self.results = {}
        self.done_signal = threading.Event()

        self.sess = U.make_session(8)
        self.sess.__enter__()
        U.initialize()
        self.norm = tf.random_normal([2, 3], mean=-1, stddev=4)

        # self.save_dir, self.model_1, self.model1_save_header, self.model_2, self.model2_save_header = HttpUtil.build_models_ppo(
        #     model1_path=None,
        #     model2_path=None,
        #     schedule_timesteps=200000,
        #     model1_initial_p=0.05,
        #     model1_final_p=0.05,
        #     model2_initial_p=0.05,
        #     model2_final_p=0.05,
        #     )

        return

    def run(self):
        while True:
            try:
                item = self.q.get()
                rsp_str = self.sess.run(self.norm)
                print(self.name + ' Getting ' + str(item)
                                  + ' : ' + str(self.q.qsize()) + ' items in queue ')
                time.sleep(3)
                self.results[item] = rsp_str
                self.done_signal.set()
                self.q.task_done()
            except Exception as e:
                print(e)

class ProducerThread(threading.Thread):
    def __init__(self, consumer, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ProducerThread,self).__init__()
        self.consumer = consumer
        self.target = target
        self.name = name

    def run(self):
        q = self.consumer.q
        while True:
            if not q.full():
                item = random.randint(1,10)
                q.put(item)
                print(self.name + ' Putting ' + str(item)
                      + ' : ' + str(q.qsize()) + ' items in queue')
                while True:
                    self.consumer.done_signal.wait(1)
                    # check package
                    if item in self.consumer.results:
                        result = self.consumer.results.pop(item)
                        print(self.name + ' Getting return ' + str(result)
                              + ' : ' + str(q.qsize()) + ' items in queue')
                        break

            time.sleep(random.random())
        return


if __name__ == '__main__':
    c = ModelThread(name='model1')
    p1 = ProducerThread(c, name='producer1')
    p2 = ProducerThread(c, name='producer2')
    p3 = ProducerThread(c, name='producer3')

    p1.start()
    p2.start()
    p3.start()
    time.sleep(2)
    c.start()
    time.sleep(2)