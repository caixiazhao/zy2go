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
    curl -l -H "Content-type: application/json" -X POST -d 'save' http://localhost:8780
    curl -d "foo=bar&bin=baz" http://localhost
    curl -l -H "Content-type: application/json" -X POST -d '{"phone":"13521389587","password":"test"}' http://123.59.149.39:8780
    curl -l -H "Content-type: application/json" -X GET -d '{"wldstatic":{"ID":6442537685409333250},"wldruntime":{"State":1,"tick":66.0}}' http://localhost:8780
    curl -l -H "Content-type: application/json" -X GET -d '{"wldstatic":{"ID":9999},"wldruntime":{"State":1,"tick":528.0},"waypoint":[["(56.8, 0.0, -2.8)","(54.0, 0.0, -5.1)","(53.0, 0.0, -20.0)","(37.5, 0.0, -29.5)","(31.8, 0.0, -38.7)","(14.0, 0.0, -54.5)","(-0.6, 0.0, -61.0)","(-22.1, 0.0, -47.0)","(-33.4, 0.0, -37.5)","(-41.0, 0.0, -27.0)","(-51.0, 0.0, -13.0)","(-56.3, 0.0, 0.8)"],["(56.9, 0.0, 2.6)","(54.0, 0.0, 5.0)","(54.2, 0.0, 18.4)","(43.3, 0.0, 25.7)","(36.5, 0.0, 34.0)","(26.0, 0.0, 45.2)","(0.0, 0.0, 60.8)","(-20.6, 0.0, 51.7)","(-39.9, 0.0, 30.0)","(-52.9, 0.0, 14.8)","(-56.8, 0.0, 2.6)"],["(56.9, 0.0, -0.1)","(45.1, 0.0, -2.0)","(28.8, 0.0, 0.5)","(16.9, 0.0, 1.0)","(-11.5, 0.0, 0.3)","(-17.4, 0.0, -0.2)","(-44.9, 0.0, 2.6)","(-56.5, 0.0, 1.7)"],["(54.0, 0.0, -5.1)","(53.0, 0.0, -20.0)","(37.5, 0.0, -29.5)","(31.8, 0.0, -38.7)","(14.0, 0.0, -54.5)","(-0.6, 0.0, -61.0)","(-22.1, 0.0, -47.0)","(-33.4, 0.0, -37.5)","(-41.0, 0.0, -27.0)","(-51.0, 0.0, -13.0)","(-56.5, 0.0, 0.6)"],["(58.1, 0.0, -0.1)","(45.1, 0.0, -2.0)","(28.8, 0.0, 0.5)","(16.9, 0.0, 1.0)","(-11.5, 0.0, 0.3)","(-17.4, 0.0, -0.2)","(-44.9, 0.0, 2.6)","(-56.5, 0.0, 1.7)"],["(54.0, 0.0, 5.0)","(54.2, 0.0, 18.4)","(43.3, 0.0, 25.7)","(36.5, 0.0, 34.0)","(26.0, 0.0, 45.2)","(0.0, 0.0, 60.8)","(-20.6, 0.0, 51.7)","(-39.9, 0.0, 30.0)","(-52.2, 0.0, 15.2)","(-57.1, 0.0, 2.3)"]],"1":{"state":"in","cfgID":"965","pos":"( -57400, -100, -2310)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"2":{"state":"in","cfgID":"965","pos":"( -57460, -100, 2210)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"3":{"state":"in","cfgID":"975","pos":"( 57570, -80, -2230)","fwd":"( -1000, 0, 0)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"4":{"state":"in","cfgID":"900","pos":"( -75680, -80, 0)","fwd":"( 0, 0, 1000)","hp":16000,"maxhp":16000,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":660,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"5":{"state":"in","cfgID":"975","pos":"( 57330, -80, 2540)","fwd":"( -1000, 0, 0)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"6":{"state":"in","cfgID":"900","pos":"( 75140, -80, 0)","fwd":"( 0, 0, 1000)","hp":16000,"maxhp":16000,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":660,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"7":{"state":"in","cfgID":"961","pos":"( -62407, -230, -154)","fwd":"( -799, 0, -601)","hp":3750,"maxhp":3750,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":10,"movelock":false,"vis1":false,"vis3":false},"8":{"state":"in","cfgID":"961","pos":"( 62390, -270, 190)","fwd":"( 779, 0, 626)","hp":3750,"maxhp":3750,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":10,"movelock":false,"vis2":false,"vis3":false},"9":{"state":"in","cfgID":"964","pos":"( -17640, -80, -53540)","fwd":"( 929, 0, -370)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"10":{"state":"in","cfgID":"963","pos":"( -41710, -80, -30310)","fwd":"( 899, 0, -439)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"11":{"state":"in","cfgID":"9622","pos":"( -52300, -80, -17540)","fwd":"( 838, 0, -546)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"12":{"state":"in","cfgID":"974","pos":"( 17700, -80, -53840)","fwd":"( -707, 0, -707)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"13":{"state":"in","cfgID":"973","pos":"( 41730, -80, -30320)","fwd":"( -707, 0, -707)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"14":{"state":"in","cfgID":"9722","pos":"( 52390, -80, -17420)","fwd":"( -640, 0, -768)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"15":{"state":"in","cfgID":"964","pos":"( -17110, -80, 2080)","fwd":"( 1000, 0, 0)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"16":{"state":"in","cfgID":"963","pos":"( -32930, -80, -2020)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"17":{"state":"in","cfgID":"9621","pos":"( -46840, -80, 0)","fwd":"( 1000, 0, 0)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"18":{"state":"in","cfgID":"974","pos":"( 17110, -80, -2080)","fwd":"( -984, 0, -176)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"19":{"state":"in","cfgID":"973","pos":"( 32930, -80, 2020)","fwd":"( -971, 0, -240)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"20":{"state":"in","cfgID":"9721","pos":"( 46840, -80, 0)","fwd":"( -871, 0, -491)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"21":{"state":"in","cfgID":"964","pos":"( -17700, -80, 53840)","fwd":"( 575, 0, 818)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"22":{"state":"in","cfgID":"963","pos":"( -41550, -80, 30230)","fwd":"( 399, 0, 917)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"23":{"state":"in","cfgID":"9623","pos":"( -52330, -80, 17430)","fwd":"( 70, 0, 998)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis1":false,"vis3":false},"24":{"state":"in","cfgID":"974","pos":"( 17640, -80, 53540)","fwd":"( -981, 0, 194)","hp":1700,"maxhp":1700,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"25":{"state":"in","cfgID":"973","pos":"( 41710, -80, 30310)","fwd":"( -708, 0, 706)","hp":1500,"maxhp":1500,"mp":0,"maxmp":0,"speed":5000,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"26":{"state":"in","cfgID":"9723","pos":"( 52330, -80, 17430)","fwd":"( -930, 0, 367)","hp":1300,"maxhp":1300,"mp":0,"maxmp":0,"speed":1500,"chrtype":2,"gold":0,"attspeed":0,"att":130,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":0,"movelock":false,"vis2":false,"vis3":false},"27":{"state":"in","cfgID":"101","pos":"( 75000, 0, -1610)","fwd":"( -1000, 0, 0)","hp":800,"maxhp":800,"mp":100,"maxmp":100,"speed":3500,"moving":0,"chrtype":0,"gold":450,"attspeed":0,"att":46,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":15,"movelock":false,"vis2":false,"vis3":false,"Skill0":{"ID":10101,"MaxCD":1000,"canuse":true},"Skill1":{"ID":10110,"MaxCD":4500,"Cost":25,"up":true},"Skill2":{"ID":10120,"MaxCD":10000,"Cost":25,"up":true},"Skill3":{"ID":10130,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000,"canuse":true},"Skill5":{"ID":64141,"MaxCD":90000,"canuse":true},"Skill6":{"ID":10000,"canuse":true},"Skill7":{"ID":202,"MaxCD":12000,"canuse":true},"Skill8":{"ID":10003,"MaxCD":20000,"canuse":true},"buff":["90010","90025","90020"]},"28":{"state":"in","cfgID":"102","pos":"( -75000, 0, 2060)","fwd":"( 1000, 0, 0)","hp":875,"maxhp":875,"mp":300,"maxmp":300,"speed":6000,"moving":0,"chrtype":0,"gold":210,"attspeed":0,"att":39,"mag":0,"attpen":0,"magpen":0,"attpenrate":0,"magpenrate":0,"Hprec":20,"movelock":false,"vis1":false,"vis3":false,"Skill0":{"ID":10200,"MaxCD":1000,"canuse":true},"Skill1":{"ID":10210,"MaxCD":9000,"Cost":50,"up":true},"Skill2":{"ID":10220,"MaxCD":12000,"Cost":50,"up":true},"Skill3":{"ID":10230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000,"canuse":true},"Skill5":{"ID":64141,"MaxCD":90000,"canuse":true},"Skill6":{"ID":10000,"canuse":true},"Skill7":{"ID":202,"MaxCD":12000,"canuse":true},"Skill8":{"ID":10003,"MaxCD":20000,"canuse":true},"equip0":{"ID":41301.0,"NUM":1.0}}}' http://192.168.142.188:8780
"""
import os
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer

from baselines.common import set_global_seeds
from model.stateinfo import StateInfo
from train.line_ppo_model import LinePPOModel
from train.linemodel_dpn import LineModel_DQN
from train.linemodel_ppo1 import LineModel_PPO1
from util.httputil import HttpUtil
from util.linetrainer import LineTrainer
import json as JSON
from datetime import datetime

from util.linetrainer_ppo import LineTrainerPPO
from util.ppocache import PPO_CACHE


class S(BaseHTTPRequestHandler):
    # static variable，目前只支持同一时间处理一场比赛
    prev_stat = None

    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        get_data = self.rfile.read(content_length)  # <--- Gets the data itself

        # decode for python3 version
        get_data = get_data.decode()

        # 解析客户端发送的请求
        obj = JSON.loads(get_data)
        raw_state_info = StateInfo.decode(obj)
        if raw_state_info.battleid not in self.line_trainers:
            # DQN
            # self.line_trainer[raw_state_info.battleid] = LineTrainer(self.save_dir, ['27'], self.model1,
            #                                                          self.model1_save_header,
            #                                                          ['28'], self.model2,
            #                                                          self.model2_save_header
            #                                                          )
            # PPO
            ob = np.zeros(183, dtype=float).tolist()
            model1_cache = PPO_CACHE(ob, 1, horizon=64)
            model2_cache = PPO_CACHE(ob, 1, horizon=64)
            self.line_trainers[raw_state_info.battleid] = LineTrainerPPO(self.save_dir, '27', self.model_1,
                             self.model1_save_header, model1_cache,
                             '28', self.model_2, self.model2_save_header, model2_cache)
        # 交给对线训练器来进行训练
        rsp_str = self.line_trainers[raw_state_info.battleid].train_line_model(get_data)
        print(rsp_str)
        print('\n')
        rsp_str = rsp_str.encode(encoding="utf-8")

        #给客户端提供对应的指令
        self._set_headers()
        self.wfile.write(rsp_str)
            
    def do_HEAD(self):
        self._set_headers()

    # 通过命令来要求模型存储结果
    # curl -l -H "Content-type: application/json" -X POST -d 'save' http://localhost:8780
    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        post_data = post_data.decode()
        if post_data == 'save':
            print('save model(s)')
            self.line_trainer.save_models()
        self._set_headers()
        self.wfile.write("copy that! ".encode(encoding="utf-8"))

    def log_message(self, format, *args):
        return

    line_trainers = {}
    real_heros = None
    save_dir, model_1, model1_save_header, model_2, model2_save_header = HttpUtil.build_models_ppo(model1_path=None,
                          model2_path=None,
                          initial_p=0.5,
                          final_p=0)

def run(server_class=HTTPServer, handler_class=S, port=8780):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
