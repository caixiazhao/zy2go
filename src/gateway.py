import sys

import tornado.httpserver
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.options
import tornado.web

#from tornado.options import define, options

from common import cf as C

#define("port", default=8780, help="run on the given port", type=int)

"""
b = b'{"wldstatic":{"ID":21},"wldruntime":{"tick":29502.0},"27":{"Skill0":{"ID":10101,"MaxCD":1000,"canuse":true,"CD":0},"Skill1":{"ID":10110,"MaxCD":4500,"Cost":25,"up":false,"canuse":true,"CD":0},"Skill2":{"ID":10120,"MaxCD":10000,"Cost":25,"up":false,"canuse":false,"CD":0},"Skill3":{"ID":10130,"MaxCD":45000,"up":false,"canuse":false,"CD":0},"Skill4":{"ID":10002,"MaxCD":90000,"canuse":true},"Skill5":{"ID":64141,"MaxCD":90000,"canuse":true},"Skill6":{"ID":10000,"canuse":true},"Skill7":{"ID":202,"MaxCD":12000,"canuse":true},"Skill8":{"ID":10003,"MaxCD":20000,"canuse":true},"buff":["369"]},"28":{"Skill0":{"ID":10101,"MaxCD":1000,"canuse":true,"CD":0},"Skill1":{"ID":10110,"MaxCD":4500,"Cost":25,"up":false,"canuse":true,"CD":0},"Skill2":{"ID":10120,"MaxCD":10000,"Cost":25,"up":false,"canuse":false,"CD":0},"Skill3":{"ID":10130,"MaxCD":45000,"canuse":false,"CD":0,"up":false},"Skill4":{"ID":10002,"MaxCD":90000,"canuse":true},"Skill5":{"ID":64141,"MaxCD":90000,"canuse":true},"Skill6":{"ID":10000,"canuse":true},"Skill7":{"ID":202,"MaxCD":12000,"canuse":true},"Skill8":{"ID":10003,"MaxCD":20000,"canuse":true}},"29":{"pos":"( 44277, 0, -1843)","fwd":"( -989, 0, 147)"},"30":{"pos":"( -42454, 0, 1528)"},"31":{"pos":"( 53658, 0, -14946)","fwd":"( -192, 0, -981)"},"32":{"pos":"( -51154, 0, -13229)"},"33":{"pos":"( 54511, 0, 14685)","fwd":"( -82, 0, 997)"},"34":{"pos":"( -54100, 0, 16015)"},"35":{"pos":"( 47301, 0, -1660)"},"36":{"pos":"( -45494, 0, 1848)","fwd":"( 994, 0, -105)"},"37":{"pos":"( 54242, 0, -11946)"},"38":{"pos":"( -52735, 0, -10628)","fwd":"( 358, 0, -934)"},"39":{"pos":"( 54759, 0, 11645)","fwd":"( -81, 0, 997)"},"40":{"pos":"( -54857, 0, 13055)","fwd":"( 248, 0, 969)"},"41":{"pos":"( 50325, 0, -1185)"},"42":{"pos":"( -48490, 0, 1474)"},"43":{"pos":"( 54829, 0, -8949)","fwd":"( -192, 0, -981)"},"44":{"pos":"( -53835, 0, -7780)","fwd":"( 359, 0, -933)"},"45":{"pos":"( 55007, 0, 8605)"},"46":{"pos":"( -55617, 0, 10095)"},"47":{"pos":"( 53349, 0, -705)"},"48":{"pos":"( -51466, 0, 798)","fwd":"( 975, 0, 222)"},"49":{"pos":"( 55406, 0, -5946)"},"50":{"pos":"( -54939, 0, -4932)"},"51":{"pos":"( 55247, 0, 5565)"},"52":{"pos":"( -56377, 0, 7135)"}}'
"""
GAME_BASE_PORT = C.GAME_BASE_PORT
GAME_WORKER_SLOTS = C.GAME_WORKER_SLOTS


def battle_id_and_game_worker_port(content):
    id_str = content.partition(b'}')[0].rpartition(b':')[2]
    battle_id = int(id_str)
    port = GAME_BASE_PORT + battle_id // GAME_WORKER_SLOTS
    return (battle_id, port)


def fetch_request(url, callback, **kwargs):
    req = tornado.httpclient.HTTPRequest(url, **kwargs)
    client = tornado.httpclient.AsyncHTTPClient()
    client.fetch(req, callback, raise_error=False)


class ForwardHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def post(self, *args, **kwargs):
        self.write("not implement yet")

    @tornado.web.asynchronous
    def get(self):
        info = {}

        def handle_response(response):
            if (response.error and not isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code, response.reason)
                self._headers = tornado.httputil.HTTPHeaders()  # clear tornado default header

                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v)  # some header appear multiple times, eg 'Set-Cookie'

                if response.body:
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
            self.finish()
            print('forward %d:%d %d/%d' % (
                info['id'], info['port'], len(self.request.body), len(response.body)))

        body = self.request.body

        if not body:
            body = None
        else:
            battle_id, port = battle_id_and_game_worker_port(body)
            info['id'] = battle_id
            info['port'] = port

            uri = 'http://localhost:%d/' % port
            fetch_request(
                self.request.uri, handle_response,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)


def run_proxy(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([
        (r'.*', ForwardHandler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    port = 8780
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting HTTP proxy on port %d" % port)
    run_proxy(port)