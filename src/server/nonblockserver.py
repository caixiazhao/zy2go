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
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import traceback

from tornado.options import define, options

from train.linetrainer_manager import LineTrainerManager

define("port", default=8780, help="run on the given port", type=int)

# curl -l -H "Content-type: application/json" -X POST -d 'save' http://localhost:8780
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, p_request_dict, p_result_dict, p_request_signal, p_done_signal, lock):
        self.p_request_dict = p_request_dict
        self.p_result_dict = p_result_dict
        self.p_request_signal = p_request_signal
        self.p_done_signal = p_done_signal
        self.lock = lock

    def get(self, *args, **kwargs):
        try:
            content = tornado.escape.to_basestring(self.request.body)
            response = LineTrainerManager.read_process(content, self.p_request_dict, self.p_result_dict,
                                                   self.p_request_signal, self.p_done_signal, self.lock)
            self.write(response)
        except Exception as e:
            print('nonblock server catch exaception', traceback.format_exc())

    def post(self, *args, **kwargs):
        self.write("not implement yet")


def main():
    trainer_num = int(sys.argv[1])
    manager = LineTrainerManager(trainer_num)
    manager.start()

    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler,
         dict(p_request_dict=manager.request_dict, p_result_dict=manager.result_dict,
              p_request_signal=manager.request_signal, p_done_signal=manager.done_signal, lock=manager.lock)),
    ])
    http_server = tornado.httpserver.HTTPServer(application)

    # tornado对windows的支持不完善，在windows下只能启动单进程的网络服务
    if hasattr(os, 'fork'):
        http_server.bind(options.port)
        http_server.start(0)    # multi-process

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