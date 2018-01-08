# -*- coding: utf8 -*-
import sys

import time

import baselines.common.tf_util as U
import tensorflow as tf
import pickle
import tornado
import tornado.web
import tornado.ioloop
import traceback

from train.gl import GL
from util.httputil import HttpUtil
from tornado.options import define, options

define("port", default=8889, help="run on the given port", type=int)


#
def if_save_model(model, save_header, save_batch):
    # 训练之后检查是否保存
    replay_time = model.iters_so_far
    if replay_time % save_batch == 0:
        model.save(save_header + str(replay_time) + '/model')

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, trainer_num, save_batch,model_1, model1_save_header, model_2, model2_save_header,o4r_list_model1,o4r_list_model2):
        self.trainer_num = trainer_num
        self.save_batch =save_batch
        self.model_1=model_1
        self.model_2=model_2
        self.model1_save_header=model1_save_header
        self.model2_save_header = model2_save_header
        self.o4r_list_model1=o4r_list_model1
        self.o4r_list_model2=o4r_list_model2
    def get(self):
        try:
            #接受传来的训练数据 dict类型
            content1 =  self.request.body
            o4r=pickle.loads(content1)
            batch_size=0
            # for i in self.model_2.pi.get_variables():
            #     print(U.get_session().run(tf.reduce_sum(i)))
            #o4r_list_model2=pickle.loads(content2)
            #print(o4r_list_model1.values())
            #判断区分model1和model2
            if o4r[0]==1:
                self.o4r_list_model1[GL.s]=o4r[1]
                GL.s+=1
                self.finish("1")
                if len(self.o4r_list_model1) >= self.trainer_num :
                    try:
                        print("+++++++++++++++++++++++++")
                        for i in self.model_1.pi.get_variables() :
                            print(U.get_session().run(tf.reduce_sum(i)))
                        #print(U.get_session().run(tf.reduce_sum(self.model_2.pi.get_variables()[0])))

                        # 开始训练
                        begin_time = time.time()
                        self.model_1.replay(self.o4r_list_model1.values(),batch_size)

                        # 由自己来决定什么时候缓存模型
                        if_save_model(self.model_1, self.model1_save_header, self.save_batch)

                        self.o4r_list_model1.clear()
                        end_time = time.time()
                        delta_millionseconds = (end_time - begin_time) * 1000

                        print('model train time', delta_millionseconds)
                        GL.s=0


                        # self.model_2.replay(o4r_list_model2.values(), self.batch_size)
                        #
                        # # 由自己来决定什么时候缓存模型
                        # if_save_model(self.model_2, self.model2_save_header, self.save_batch)



                    except Exception as e:
                        type, value, traceback = sys.exc_info()
                        traceback.print_exc()



            if o4r[0]==2:
                self.o4r_list_model2[GL.d] = o4r[1]
                GL.d += 1
                self.finish("1")
                if len(self.o4r_list_model2) >= self.trainer_num:
                    try:

                        # 开始训练
                        self.model_2.replay(self.o4r_list_model2.values(),batch_size)

                        # 由自己来决定什么时候缓存模型
                        if_save_model(self.model_2, self.model2_save_header, self.save_batch)

                        self.o4r_list_model2.clear()
                        GL.d = 0


                        # self.model_2.replay(o4r_list_model2.values(), self.batch_size)
                        #
                        # # 由自己来决定什么时候缓存模型
                        # if_save_model(self.model_2, self.model2_save_header, self.save_batch)



                    except Exception as e:
                        type, value, traceback = sys.exc_info()
                        traceback.print_exc()
            if o4r[0] == 3:
                alllist=[]
                list1= []
                list = []
                begin_time = time.time()
                i = 0
                # 把变量转成list类型
                for newv in self.model_1.pi.get_variables():
                    # sess.run(tf.Print(newv, [newv],summarize=10))
                    list.append(U.get_session().run(newv).tolist())
                    # print(list[1])

                # 把list以str的形式传过去
                #self.finish(str(list))
                end_time = time.time()
                delta_millionseconds = (end_time - begin_time) * 1000

                print('model send time', delta_millionseconds)
                i = 0
                # 把变量转成list类型
                for newv in self.model_2.pi.get_variables():
                    # sess.run(tf.Print(newv, [newv],summarize=10))
                    list1.append(U.get_session().run(newv).tolist())
                alllist.append(list)
                alllist.append(list1)
               # print(list[1])

                    # 把list以str的形式传过去
                self.finish(pickle.dumps(alllist))
                # end = time.time()
                # delta = end - begin
                # file_object = open('/Users/Administrator/Desktop/send.txt', 'a')
                # file_object.write(str(delta * 1000) + '\n')
                # file_object.close()


        except Exception as e:
            print('nonblock server catch exception')
            print('nonblock server catch exception', traceback.format_exc())
            self.finish('{}')


def main():
    save_batch = 10
    trainer_num = int(sys.argv[1])
    save_dir = HttpUtil.get_save_root_path()

    model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(
        save_dir,
        model1_path=None, #'/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-17123006.954281/line_model_1_v10/model',
        # model1_path='/Users/Administrator/Desktop/wenjian/modell/model',
        # model2_path='/Users/Administrator/Desktop/wenjian/Model/model',
        model2_path=None,
        # '/Users/sky4star/Github/zy2go/battle_logs/model_2017-11-17123006.954281/line_model_2_v10/model',
        schedule_timesteps=1000000,
        model1_initial_p=0.5,
        model1_final_p=0.1,
        model1_gamma=0.93,
        model2_initial_p=0.5,
        model2_final_p=0.1,
        model2_gamma=0.93
    )
    o4r_list_model1 = {}
    o4r_list_model2 = {}

    application = tornado.web.Application([
        (r"/", MainHandler,
         dict(trainer_num=trainer_num, save_batch=save_batch,model_1=model_1, model1_save_header=model1_save_header, model_2=model_2, model2_save_header=model2_save_header,o4r_list_model1=o4r_list_model1,o4r_list_model2=o4r_list_model2)),
    ])


    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == '__main__':
    main()
