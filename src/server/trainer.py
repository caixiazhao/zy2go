# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import logging

import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

from common import cf as C
C.set_run_mode(C.RUN_MODE_TRAIN)

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import traceback

from tornado.options import define, options
from train.train_manager import LineTrainerManager

define("port", default=8999, help="run on the given port", type=int)
define("g", default=0, help="generation id")

manager = LineTrainerManager(C.get_run_mode())

class TrainerHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        try:
            data = self.request.body
            path = self.request.path

            if path.startswith('/generation_id'):
                self.finish(str(manager.get_generation_id()))
                return

            if path.startswith('/data'):
                # print('/data %d' % len(data))
                manager.push_data(data)
                self.finish(str(manager.get_generation_id()))
                return

            if path.startswith('/train'):
                manager.train()
                self.finish(str(manager.get_generation_id()))
                return

            self.finish()
            return
        except Exception as e:
            print('nonblock server catch exception')
            print('nonblock server catch exception', traceback.format_exc())
            self.finish('{}')

    def post(self, *args, **kwargs):
        self.write("not implement yet")


def main():
    tornado.options.parse_command_line()

    application = tornado.web.Application([
        (r"/.*", TrainerHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(application)

    C.set_worker_name("tr%d" % options.port)
    manager.generation_id = options.g
    # tornado对windows的支持不完善，在windows下只能启动单进程的网络服务
    if hasattr(os, 'fork'):
        http_server.bind(options.port)
        http_server.start(1)    # multi-process

        hn = logging.NullHandler()
        hn.setLevel(logging.DEBUG)
        logging.getLogger("tornado.access").addHandler(hn)
        logging.getLogger("tornado.access").propagate = False
    else:
        http_server.listen(options.port)

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    main()
