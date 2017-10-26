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

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from train.linetrainer_manager import LineTrainerManager

define("port", default=8780, help="run on the given port", type=int)

# curl -l -H "Content-type: application/json" -X POST -d 'save' http://localhost:8780
class MainHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        content = tornado.escape.to_basestring(self.request.body)
        manager = LineTrainerManager()
        response = manager.response(content)
        print(response)
        self.write(response)

    def post(self, *args, **kwargs):
        self.write("Hello, world")


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    # http_server.listen(options.port)

    http_server.bind(options.port)
    http_server.start(0)    # multi-process
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    main()