# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost
    curl -l -H "Content-type: application/json" -X POST -d '{"phone":"13521389587","password":"test"}' http://123.59.149.39:8780
    curl -l -H "Content-type: application/json" -X GET -d '{"wldstatic":{"ID":6442537685409333250},"wldruntime":{"State":1,"tick":66.0}}' http://localhost:8780
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from time import gmtime, strftime
import json as JSON

from model.herostateinfo import HeroStateInfo
from model.stateinfo import StateInfo


class S(BaseHTTPRequestHandler):
    # static variable
    prev_stat = None

    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def build_action_command(self, hero_id, action, parameters):
        if action == 'MOVE' and 'pos' in parameters:
            return {"hero_id": hero_id, "action": action, "pos": parameters['pos']}
        if action == 'AUTO':
            return {"hero_id": hero_id, "action": action}
        raise ValueError('unexpected action type ' + action)

    def do_GET(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        get_data = self.rfile.read(content_length)  # <--- Gets the data itself
        self.log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + get_data + "\n")
        self.log_file.flush()

        # 简单解析
        obj = JSON.loads(get_data)
        state_info = StateInfo.decode(obj)
        S.prev_stat = state_info
        battleid = state_info.battleid
        tick = state_info.tick

        # 构造反馈结果
        action_strs = []
        for hero in state_info.heros:
            # 测试代码：在前1分钟，命令英雄到达指定地点
            if 528*2*60 > int(tick) > 528:
                action_str = self.build_action_command(hero.hero_name, 'MOVE', {'pos':'( 0, -80, 0)'})
            else:
                action_str = self.build_action_command(hero.hero_name, 'AUTO', {})
            action_strs.append(action_str)

        rsp_obj = {"ID":battleid, "tick": tick, "cmd": action_strs}
        rsp_str = JSON.dumps(rsp_obj)
        print rsp_str
        self._set_headers()
        self.wfile.write(rsp_str)

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        self.log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + post_data + "\n")
        self._set_headers()
        self.wfile.write("copy that! " + post_data)

    log_file = open('httpd.log', 'a')

    def log_message(self, format, *args):
        return

def run(server_class=HTTPServer, handler_class=S, port=8780):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()