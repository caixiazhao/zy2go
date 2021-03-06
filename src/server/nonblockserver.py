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

from teambattle.teambattletrainer_manager import TeamBattleTrainerManager
from train.linetrainer_manager import LineTrainerManager

define("port", default=8780, help="run on the given port", type=int)

# curl -l -H "Content-type: application/json" -X POST -d 'save' http://localhost:8780
class MainHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        try:
            content = tornado.escape.to_basestring(self.request.body)
            response = TeamBattleTrainerManager.One.read_process(content)
            self.finish(response)
        except Exception as e:
            print('nonblock server catch exception')
            print('nonblock server catch exception', traceback.format_exc())
            self.finish('{}')

    def post(self, *args, **kwargs):
        self.write("not implement yet")


def main():
    trainer_num = int(sys.argv[1])
    manager = TeamBattleTrainerManager(trainer_num)

    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(application)

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