import sys
import hashlib

import tornado.httpserver
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.options
import tornado.web

from common import cf as C

GAME_BASE_PORT = C.GAME_BASE_PORT
GAME_WORKER_SLOTS = C.GAME_WORKER_SLOTS


G = {
    'batches': 0,
    'train_lock': False,
}


def battle_id_and_game_worker_port(content):
    id_str = content.partition(b'}')[0].rpartition(b':')[2]
    battle_id = int(id_str)
    port = GAME_BASE_PORT + (battle_id - 1) // GAME_WORKER_SLOTS
    return battle_id, port


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

            uri = 'http://127.0.0.1:%d/' % port
            fetch_request(
                uri, handle_response,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)


class DataHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        body = self.request.body
        path = self.request.path
        battle_id, model_name, generation_id = path[6:].split('/')
        self.finish(C.get_generation_id())

        def train__data_callback(response):
            G['batches'] += 1
            if G['batches'] >= C.TRAIN_GAME_BATCH:
                G['train_lock'] = True
                fetch_request(
                    'http://127.0.0.1:%d/train' % (C.TRAINER_PORT),
                    train__train_callback,
                    method='GET',
                    follow_redirects=False,
                    allow_nonstandard_methods=True)

        def train__train_callback(response):
            G['train_look'] = False
            G['batches'] = 0
            C.set_generation_id(int(response.body))

        if G['train_look']:
            return

        if int(generation_id) == C.get_generation_id():
            fetch_request(
                'http://127.0.0.1:%d%s' % (C.TRAINER_PORT, self.request.path),
                train__data_callback,
                method='GET', body=body,
                follow_redirects=False,
                allow_nonstandard_methods=True)


def run_gateway(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([
        (r'/data/.*', DataHandler),
        (r'.*', ForwardHandler),
    ])
    C.set_worker_name('gw')
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    port = 8780
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print("Starting HTTP proxy on port %d" % port)
    C.set_run_mode("gateway")
    C.set_generation_id(0)
    run_gateway(port)
