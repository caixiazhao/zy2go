import threading

import time
from util.modelthread import ModelThread
from util.singleton import Singleton


class LineTrainerManager(metaclass=Singleton):
    # sess = U.make_session(8)
    # sess.__enter__()
    # U.initialize()
    # line_trainers = {}
    # norm = tf.random_normal([2, 3], mean=-1, stddev=4)

    # save_dir, model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(
    #     model1_path=None,
    #     model2_path=None,
    #     schedule_timesteps=200000,
    #     model1_initial_p=0.05,
    #     model1_final_p=0.05,
    #     model2_initial_p=0.05,
    #     model2_final_p=0.05,
    #     )
    model1 = ModelThread(name='model1')
    init_model = False
    line_trainers = {}
    using_line_trainers = []
    lock = threading.Lock()

    def response(self, get_data):
        with self.lock:
            if not self.init_model:
                self.init_model = True
                print("model start")
                self.model1.start()

        with self.lock:
            if get_data not in self.line_trainers.keys():
                print(get_data, '开始创建')
                self.line_trainers[get_data] = get_data + 10

        if get_data not in self.using_line_trainers:
            line_trainer = self.line_trainers[get_data]
            self.using_line_trainers.append(get_data)
            # 这里假装处理一段时间
            print(get_data, '正在处理')
            self.model1.q.put(get_data)
            while True:
                self.model1.done_signal.wait(1)
                # check package
                if get_data in self.model1.results:
                    result = self.model1.results.pop(get_data)
                    break
            print(get_data, result)
            self.using_line_trainers.remove(get_data)
            return line_trainer
        else:
            # 如果当前训练器正在被使用，直接返回空，本次请求超时，这样客户端会继续重试，直到训练器返回为止
            print(get_data, '被占用，直接返回')
            return None

        # sess = U.make_session(8)
        # sess.__enter__()
        # U.initialize()
        # norm = tf.random_normal([2, 3], mean=-1, stddev=4)
        # sess = U.get_session()
        # obj = JSON.loads(get_data)
        # self.model1.q.put('input')
        # rsp_str = sess.run(norm)
        # raw_state_info = StateInfo.decode(obj)
        # if raw_state_info.battleid not in self.line_trainers:
        #     # PPO
        #     ob = np.zeros(183, dtype=float).tolist()
        #     model1_cache = PPO_CACHE2(ob, 1, horizon=self.model_1.optim_batchsize)
        #     model2_cache = PPO_CACHE2(ob, 1, horizon=self.model_2.optim_batchsize)
        #     self.line_trainers[raw_state_info.battleid] = LineTrainerPPO(self.save_dir, '27', self.model_1,
        #                                                                  self.model1_save_header, model1_cache,
        #                                                                  '28', self.model_2, self.model2_save_header,
        #                                                                  model2_cache, real_hero=None,
        #                                                                  policy_ratio=-1, policy_continue_acts=3)
        # # 交给对线训练器来进行训练
        # rsp_str = self.line_trainers[raw_state_info.battleid].train_line_model(get_data)
        return ''