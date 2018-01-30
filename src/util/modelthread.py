# -*- coding: utf8 -*-
import random
import threading
import time
import logging
import queue
import baselines.common.tf_util as U
import tensorflow as tf

from util.modelutil import ModelUtil


# 维护三个队列，一个action队列用来计算英雄行为，一个train队列用来训练模型，一个save队列用来存储模型
# 所有的模型都在本线程中进行维护
class ModelThread(threading.Thread):

    NAME_MODEL_1 = 'model_1'
    NAME_MODEL_2 = 'model_2'

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ModelThread,self).__init__()
        self.target = target
        self.name = name
        self.action_queue = queue.Queue()
        self.train_queue = queue.Queue()
        self.save_queue = queue.Queue()
        self.results = {}
        self.done_signal = threading.Event()
        self.save_batch = 200
        self.inited = False

        self.save_dir = None
        self.model_1 = None
        self.model1_save_header = None
        self.model_2 = None
        self.model2_save_header = None
        self.init_signal = threading.Event()

    def init_models(self):
        self.save_dir, self.model_1, self.model1_save_header, self.model_2, self.model2_save_header = ModelUtil.build_models_ppo(
            model1_path=None,
            model2_path=None,
            schedule_timesteps=200000,
            model1_initial_p=0.05,
            model1_final_p=0.05,
            model1_gamma=0.95,
            model2_initial_p=0.05,
            model2_final_p=0.05,
            model2_gamma=0.95
        )

    def if_save_model(self, model, save_header):
        # 训练之后检查是否保存
        replay_time = model.iters_so_far
        if replay_time % self.save_batch == 0:
            model.save(save_header + str(replay_time) + '/model')

    def run(self):
        # 在运行线程中启动tf模型，注意这里必须在运行线程中而不是在初始化线程中启动tf.session，否则会找不到默认线程
        if not self.inited:
            print('初始化模型线程')
            self.init_models()
            self.inited = True
            self.init_signal.set()

        while True:
            try:
                # 优先从save队列中取请求
                if not self.save_queue.empty():
                    (battle_id, save_model_name, path) = self.save_queue.get()
                    print(battle_id, 'receive save signal')
                    if save_model_name == ModelThread.NAME_MODEL_1:
                        self.model_1.save(path)
                        self.if_save_model(self.model_1, self.model1_save_header)
                    elif save_model_name == ModelThread.NAME_MODEL_2:
                        self.model_2.save(path)
                        self.if_save_model(self.model_2, self.model2_save_header)

                # 其次从训练队列中提取请求
                if not self.train_queue.empty():
                    (battle_id, train_model_name, o4r, batch_size) = self.train_queue.get()
                    print(battle_id, train_model_name, 'receive train signal, batch size', batch_size)
                    if train_model_name == ModelThread.NAME_MODEL_1:
                        self.model_1.replay(o4r, batch_size)
                    elif train_model_name == ModelThread.NAME_MODEL_2:
                        self.model_2.replay(o4r, batch_size)

                # 最后从行为队列中拿请求
                # 等待在这里（阻塞），加上等待超时确保不会出现只有个train信号进来导致死锁的情况
                (battle_id, act_model_name, state_info, hero_name, rival_hero) = self.action_queue.get(timeout=1)
                print(battle_id, 'receive act signal', act_model_name, hero_name)
                if act_model_name == ModelThread.NAME_MODEL_1:
                    action, explorer_ratio, action_ratios = self.model_1.get_action(state_info, hero_name, rival_hero)
                elif act_model_name == ModelThread.NAME_MODEL_2:
                    action, explorer_ratio, action_ratios = self.model_2.get_action(state_info, hero_name, rival_hero)
                print(str(battle_id) + ' Getting for ' + str(act_model_name)
                                  + ' : ' + str(self.action_queue.qsize()) + ' items in queue ')
                self.results[(battle_id, act_model_name)] = (action, explorer_ratio, action_ratios)
                self.done_signal.set()
                self.action_queue.task_done()
            except queue.Empty:
                continue
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