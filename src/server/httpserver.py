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

class S(BaseHTTPRequestHandler):
    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        get_data = self.rfile.read(content_length)  # <--- Gets the data itself
        self.log_file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + get_data + "\n")

        # 简单解析
        obj = JSON.loads(get_data)
        battleid = obj['wldstatic']['ID']
        tick = obj['wldruntime']['tick']
        rsp_obj = {"ID":battleid, "tick": tick, "cmd":
            [{"hero_id": "27", "action": "AUTO"},
             {"hero_id": "28", "action": "AUTO"},
             {"hero_id": "29", "action": "AUTO"},
             {"hero_id": "30", "action": "AUTO"},
             {"hero_id": "31", "action": "AUTO"},
             {"hero_id": "32", "action": "AUTO"},
             {"hero_id": "33", "action": "AUTO"},
             {"hero_id": "34", "action": "AUTO"},
             {"hero_id": "35", "action": "AUTO"},
             {"hero_id": "36", "action": "AUTO"}]}
        rsp_str = JSON.dumps(rsp_obj)
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