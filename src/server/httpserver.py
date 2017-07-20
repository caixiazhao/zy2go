# !/usr/bin/env python
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
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging
from time import gmtime, strftime

from cloghandler import ConcurrentRotatingFileHandler


class S(BaseHTTPRequestHandler):
    def __init__(self, *args):

        self.logger = logging.getLogger("httpd")
        fh = ConcurrentRotatingFileHandler("httpd.log", mode='a',
                                 maxBytes=10*1024*1024, backupCount=200)
        self.logger.addHandler(fh)
        self.logger.setLevel(logging.INFO)
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        get_data = self.rfile.read(content_length)  # <--- Gets the data itself
        self.logger.info(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + get_data)
        self._set_headers()
        self.wfile.write("copy that!")

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        self.logger.info(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " -- " + post_data)
        self._set_headers()
        self.wfile.write("copy that! " + post_data)


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