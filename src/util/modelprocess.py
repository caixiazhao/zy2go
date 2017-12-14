# -*- coding: utf8 -*-
import sys
import queue
import time

from model.cmdaction import CmdAction
from train.cmdactionenum import CmdActionEnum
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
            # model1_path='/Users/sky4star/Github/zy2go/data/20171205/model_2017-12-05003908.817275/line_model_1_v40/model',
            # model2_path='/Users/sky4star/Github/zy2go/data/20171205/model_2017-12-05003908.817275/line_model_2_v40/model',
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
    while True:
        try:
            # 从训练队列中提取请求
            # 只有当训练集中有所有的战斗的数据时候才会开始训练
            with lock:
                if not train_queue.empty():
                    (battle_id, train_model_name, o4r, batch_size) = train_queue.get()
                    print('model_process', battle_id, train_model_name, 'receive train signal, batch size', batch_size)
                    if train_model_name == ModelProcess.NAME_MODEL_1:
                        o4r_list_model1[battle_id] = o4r
                        print('model_process model1 train collection', ';'.join((str(k) for k in o4r_list_model1.keys())))
                    elif train_model_name == ModelProcess.NAME_MODEL_2:
                        o4r_list_model2[battle_id] = o4r
                        print('model_process model2 train collection', ';'.join((str(k) for k in o4r_list_model2.keys())))

            trained = False
            if len(o4r_list_model1) >= battle_id_num and len(o4r_list_model2) >= battle_id_num:
                print('model_process1', train_model_name, 'begin to train')
                begin_time = time.time()
                model_1.replay(o4r_list_model1.values(), batch_size)
                o4r_list_model1.clear()

                # 由自己来决定什么时候缓存模型
                if_save_model(model_1, model1_save_header, save_batch)

                print('model_process2', train_model_name, 'begin to train')
                model_2.replay(o4r_list_model2.values(), batch_size)
                o4r_list_model2.clear()
                end_time = time.time()
                delta_millionseconds = (end_time - begin_time) * 1000

                print('model train time', delta_millionseconds)

                # 由自己来决定什么时候缓存模型
                if_save_model(model_2, model2_save_header, save_batch)

                trained = True

            if trained:
                with lock:
                    print('model process, add trained events')
                    restartCmd = CmdAction(ModelProcess.NAME_MODEL_1, CmdActionEnum.RESTART, 0, None, None, None, None, None, None)
                    for battle_id in range(1, battle_id_num+1):
                        # 给每个客户端添加一个训练结束的通知
                        results[(battle_id, ModelProcess.NAME_MODEL_1)] = (restartCmd, None, None)
                        continue

            # 从行为队列中拿请求
            # 等待在这里（阻塞），加上等待超时确保不会出现只有个train信号进来导致死锁的情况
            battle_ids = []
            act_model_names = []
            state_inputs = []
            while not action_queue.empty():
                (battle_id, act_model_name, state_input) = action_queue.get(timeout=1)

                with lock:
                    # 如果上一条还没有消耗掉，则忽略本条请求，这种情况应该只会出现在训练后
                    if (battle_id, act_model_name) in results:
                        continue

                battle_ids.append(battle_id)
                act_model_names.append(act_model_name)
                state_inputs.append(state_input)

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
            num_cache.append(len(battle_ids))
            if len(time_cache) >= 1000:
                print("model get_action average calculate time(ms)", sum(time_cache) // float(len(time_cache)), sum(num_cache) / float(len(num_cache)))
                time_cache = []
                num_cache = []

            with lock:
                for battle_id, act_model_name, actions, vpred in zip(battle_ids, act_model_names, actions_list, vpreds):
                    if (battle_id, act_model_name) not in results:
                        results[(battle_id, act_model_name)] = (actions, explor_value, vpred)
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