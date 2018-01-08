# -*- coding: utf8 -*-
import sys
import queue
import time
import http.client
import pickle
import numpy as np



import tensorflow as tf
from model.cmdaction import CmdAction
import baselines.common.tf_util as U
from train.cmdactionenum import CmdActionEnum
from train.gl import GL
from util.httputil import HttpUtil
from multiprocessing import Process, Manager, Value, Array, Lock, Queue, Event


# 维护三个队列，一个action队列用来计算英雄行为，一个train队列用来训练模型，一个save队列用来存储模型
# 所有的模型都在本线程中进行维护
def if_save_model(model, save_header, save_batch):
    # 训练之后检查是否保存
    replay_time = model.iters_so_far
    if replay_time % save_batch == 0:
        model.save(save_header + str(replay_time) + '/model')


def start_model_process(battle_id_num, init_signal, train_queue, action_queue, results, save_batch, save_dir, lock):
    model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(
            save_dir,
            model1_path=None,
            model2_path=None,
            # model1_path='/Users/sky4star/Github/zy2go/data/20171218/model_2017-12-14192241.120603/line_model_1_v460/model',
            # model2_path='/Users/sky4star/Github/zy2go/data/20171218/model_2017-12-14192241.120603/line_model_2_v460/model',
            # model1_path='/Users/sky4star/Github/zy2go/data/20171204/model_2017-12-01163333.956214/line_model_1_v430/model',
            # model2_path='/Users/sky4star/Github/zy2go/data/20171204/model_2017-12-01163333.956214/line_model_2_v430/model',
            # model1_path='/Users/sky4star/Github/zy2go/data/all_trained/battle_logs/trained/171127/line_model_1_v380/model', #'/Users/sky4star/Github/zy2go/data/20171115/model_2017-11-14183346.557007/line_model_1_v730/model', #'/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-17123006.954281/line_model_1_v10/model',
            # model2_path='/Users/sky4star/Github/zy2go/data/all_trained/battle_logs/trained/171127/line_model_2_v380/model', #'/Users/sky4star/Github/zy2go/data/20171121/model_2017-11-20150651.200368/line_model_2_v120/model',
            schedule_timesteps=1000000,
            model1_initial_p=0.5,
            model1_final_p=0.1,
            model1_gamma=0.93,
            model2_initial_p=0.5,
            model2_final_p=0.1,
            model2_gamma=0.93
        )
    init_signal.set()
    print('模型进程启动')

    time_cache = []
    num_cache = []

    o4r_list_model1 = {}
    o4r_list_model2 = {}
    done_signals = {}
    while True:
        try:
            trained = False
            # 从训练队列中提取请求
            # 只有当训练集中有所有的战斗的数据时候才会开始训练
            with lock:

                GL.modelend = time.time()
                if GL.modelend - GL.modelstart > 20:
                    begin = time.time()
                    GL.modelstart = time.time() + 16
                    conn = http.client.HTTPConnection("localhost", 8889)
                    list = []
                    list.append(3)
                    # for i in model_2.pi.get_variables():
                    #     print(U.get_session().run(tf.reduce_sum(i)))
                    # 把数据集序列化，发送给服务器
                    conn.request("GET", "/", pickle.dumps(list))
                    r1 = conn.getresponse()
                    print(r1.status, r1.reason)
                    # begin1 = time.time()
                    a = r1.read()
                    data = pickle.loads(a)



                    list=data[0]
                    list1=data[1]
                    # print(len(model_1.pi.get_variables()))
                    hh = 0
                    for i in range(len(list)):
                        if np.sum(GL.data[i]) != np.sum(list[i]):
                            GL.data[i] = list[i]
                            hh += 1

                    if hh > 0:
                        print("开始", hh)
                        #检验变量是否完成覆盖
                        for i in model_1.pi.get_variables():
                            print(U.get_session().run(tf.reduce_sum(i)))
                        for i in range(len(list)):
                            oldv1 = model_1.pi.get_variables()[i]
                            newv1 = tf.placeholder(dtype=tf.float32)
                            assign_old_eq_new = U.function([newv1], [], updates=[tf.assign(oldv1, newv1)])
                            assign_old_eq_new(list[i])
                        for i in range(len(list1)):
                            oldv1 = model_2.pi.get_variables()[i]
                            newv1 = tf.placeholder(dtype=tf.float32)
                            assign_old_eq_new = U.function([newv1], [], updates=[tf.assign(oldv1, newv1)])
                            assign_old_eq_new(list1[i])
                        trained = True
                    else:
                        print("countine")

                    # end = time.time()
                    # delta = end - begin
                    # file_object = open('/Users/Administrator/Desktop/if.txt', 'a')
                    # file_object.write(str(delta * 1000) + '\n')
                    # file_object.close()

                if not train_queue.empty():
                    begin1 = time.time()
                    (battle_id, train_model_name, o4r, batch_size) = train_queue.get()
                    # print('model_process', battle_id, train_model_name, 'receive train signal, batch size', batch_size)
                    if train_model_name == ModelProcess.NAME_MODEL_1:
                        begin=time.time()
                        conn = http.client.HTTPConnection("localhost", 8889)
                        list = []
                        list.append(1)
                        list.append(o4r)
                        # 把数据集序列化，发送给服务器
                        conn.request("GET", "/", pickle.dumps(list))

                        r1 = conn.getresponse()
                        print(r1.status, r1.reason)
                        print("------------OK---------")
                        end = time.time()
                        # delta = end - begin
                        # file_object = open('/Users/Administrator/Desktop/for.txt', 'a')
                        # file_object.write(str(delta * 1000) + '\n')
                        # file_object.close()


                        # trained = True



                    elif train_model_name == ModelProcess.NAME_MODEL_2:
                        conn = http.client.HTTPConnection("localhost", 8889)
                        list = []
                        list.append(2)
                        list.append(o4r)
                        # 把数据集序列化，发送给服务器
                        conn.request("GET", "/", pickle.dumps(list))

                        r1 = conn.getresponse()
                        print(r1.status, r1.reason)
                        print("------------OK---------")




            if trained:
                with lock:
                    print('model process, add trained events')
                    restartCmd = CmdAction(ModelProcess.NAME_MODEL_1, CmdActionEnum.RESTART, 0, None, None, None, None, None, None)
                    for battle_id in range(1, battle_id_num+1):
                        # 给每个客户端添加一个训练结束的通知
                        done_signals[(battle_id, ModelProcess.NAME_MODEL_1)] = (restartCmd, None, None)

            # 从行为队列中拿请求
            # 等待在这里（阻塞），加上等待超时确保不会出现只有个train信号进来导致死锁的情况
            state_inputs = []
            if not action_queue.empty():
                # 考虑到目前的并发情况，没有必要批量读取所有等待中的请求，因为基本只有一个等待的请求
                # state_inputs是个数组，可能含有多个请求（MCTS下）
                (battle_id, act_model_name, state_inputs) = action_queue.get(timeout=1)

                with lock:
                    # 如果上一条还没有消耗掉，则忽略本条请求，这种情况应该只会出现在训练后
                    if (battle_id, act_model_name) in done_signals:
                        results[(battle_id, act_model_name)] = done_signals[(battle_id, act_model_name)]
                        del done_signals[(battle_id, act_model_name)]
                        continue

            if len(state_inputs) == 0:
                continue

            begin_time = time.time()
            if act_model_name == ModelProcess.NAME_MODEL_1:
                actions_list, explor_value, vpreds = model_1.get_actions(state_inputs)
            elif act_model_name == ModelProcess.NAME_MODEL_2:
                actions_list, explor_value, vpreds = model_2.get_actions(state_inputs)
            end_time = time.time()
            delta_millionseconds = (end_time - begin_time) * 1000
            time_cache.append(delta_millionseconds)
            num_cache.append(len(state_inputs))
            if len(time_cache) >= 1000:
                print("model get_action average calculate time(ms)", sum(time_cache) // float(len(time_cache)), sum(num_cache) / float(len(num_cache)))
                time_cache = []
                num_cache = []

            with lock:
                results[(battle_id, act_model_name)] = (actions_list, explor_value, vpreds)
        except queue.Empty:
            continue
        except Exception as e:
            type, value, traceback = sys.exc_info()
            traceback.print_exc()


class ModelProcess:
    NAME_MODEL_1 = 'model_1'
    NAME_MODEL_2 = 'model_2'

    def __init__(self, battle_id_num):
        manager = Manager()
        self.action_queue = Queue()
        self.train_queue = Queue()
        self.results = manager.dict()
        self.save_batch = 10
        self.init_signal = Event()
        self.lock = Lock()
        self.battle_id_num = battle_id_num
        self.save_dir = HttpUtil.get_save_root_path()

    def start(self):
        p = Process(target=start_model_process, args=(self.battle_id_num, self.init_signal, self.train_queue,
                                                      self.action_queue, self.results,
                                                      self.save_batch, self.save_dir, self.lock))
        p.start()

if __name__ == '__main__':
    model_process = ModelProcess()
    model_process.start()