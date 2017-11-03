# -*- coding: utf8 -*-
import sys
import queue

from util.httputil import HttpUtil
from multiprocessing import Process, Manager, Value, Array, Lock, Queue, Event


# 维护三个队列，一个action队列用来计算英雄行为，一个train队列用来训练模型，一个save队列用来存储模型
# 所有的模型都在本线程中进行维护
def if_save_model(model, save_header, save_batch):
    # 训练之后检查是否保存
    replay_time = model.iters_so_far
    if replay_time % save_batch == 0:
        model.save(save_header + str(replay_time) + '/model')


def start_model_process(battle_id_num, init_signal, train_queue, action_queue, results, train_done_signal, done_signal, save_batch, save_dir, lock):
    model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(
            save_dir,
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
    init_signal.set()
    print('模型进程启动')

    o4r_list_model1 = []
    o4r_list_model2 = []
    while True:
        try:
            # 从训练队列中提取请求
            with lock:
                if not train_queue.empty():
                    (battle_id, train_model_name, o4r, batch_size) = train_queue.get()
                    print('model_process', battle_id, train_model_name, 'receive train signal, batch size', batch_size)
                    if train_model_name == ModelProcess.NAME_MODEL_1:
                        o4r_list_model1.append(o4r)
                    elif train_model_name == ModelProcess.NAME_MODEL_2:
                        o4r_list_model2.append(o4r)

            trained = False
            if len(o4r_list_model1) >= battle_id_num:
                print('model_process', train_model_name, 'begin to train')
                model_1.replay(o4r_list_model1, batch_size)
                o4r_list_model1.clear()
                trained = True

                # 由自己来决定什么时候缓存模型
                if_save_model(model_1, model1_save_header, save_batch)

            if len(o4r_list_model2) >= battle_id_num:
                print('model_process', train_model_name, 'begin to train')
                model_2.replay(o4r_list_model2, batch_size)
                o4r_list_model2.clear()
                trained = True

                # 由自己来决定什么时候缓存模型
                if_save_model(model_2, model2_save_header, save_batch)

            if trained:
                train_done_signal.set()
                print('model process, train signal sent')

            # 从行为队列中拿请求
            # 等待在这里（阻塞），加上等待超时确保不会出现只有个train信号进来导致死锁的情况
            (battle_id, act_model_name, state_info, hero_name, rival_hero) = action_queue.get(timeout=1)
            print('model_process', battle_id, 'receive act signal', act_model_name, hero_name)
            if act_model_name == ModelProcess.NAME_MODEL_1:
                action, explorer_ratio, action_ratios = model_1.get_action(state_info, hero_name, rival_hero)
            elif act_model_name == ModelProcess.NAME_MODEL_2:
                action, explorer_ratio, action_ratios = model_2.get_action(state_info, hero_name, rival_hero)
            print('model_process', battle_id, 'get_action done')

            with lock:
                results[(battle_id, act_model_name)] = (action, explorer_ratio, action_ratios)
                done_signal.set()
        except queue.Empty:
            continue
        except BaseException:
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
        self.train_done_signal = Event()
        self.done_signal = Event()
        self.save_batch = 200
        self.init_signal = Event()
        self.lock = Lock()
        self.battle_id_num = battle_id_num
        self.save_dir = HttpUtil.get_save_root_path()

    def start(self):
        p = Process(target=start_model_process, args=(self.battle_id_num, self.init_signal, self.train_queue,
                                                      self.action_queue, self.results, self.train_done_signal,
                                                      self.done_signal, self.save_batch, self.save_dir, self.lock))
        p.start()

if __name__ == '__main__':
    model_process = ModelProcess()
    model_process.start()