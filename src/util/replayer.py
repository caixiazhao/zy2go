#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 解析json日志，还原出来基础信息
# 得到每次
#   英雄位置信息，
#   兵线信息
#   技能冷却信息
#   攻击信息
#   野怪信息
# 统计出来
#   玩家意图

# 第一条信息貌似和后续信息有所不同
import json as JSON
from src.model.stateinfo import StateInfo


class Replayer:
    @staticmethod
    def parse_state_log(json_str):
        state_json = JSON.loads(json_str)
        state_info = StateInfo.decode(state_json)

    @staticmethod
    def update_state_log(prev_state, cur_state):
        # 因为每一次传输时候并不是全量信息，所以需要好上一帧的完整信息进行合并
        return

    @staticmethod
    def guess_strategy(state_infos):
        # 根据英雄的位置和状态猜测他当之前一段时间内的策略层面的决定
        return

if __name__ == "__main__":
    json_head = '{"wldstatic":{"ID":6443764701731028995},"wldruntime":{"State":1,"tick":330.0},"waypoint":[["(-56.3, 0.0, -1.5)","(-51.6, 0.0, -13.5)","(-41.0, 0.0, -28.5)","(-33.9, 0.0, -37.6)","(-19.9, 0.0, -49.5)","(0.0, 0.0, -62.3)","(15.7, 0.0, -55.0)","(32.2, 0.0, -39.3)","(39.0, 0.0, -29.5)","(54.0, 0.0, -20.0)","(55.0, 0.0, -5.0)","(57.1, 0.0, -3.6)"],["(-57.3, 0.0, 3.6)","(-53.6, 0.0, 18.0)","(-39.1, 0.0, 30.2)","(-20.1, 0.0, 51.2)","(0.0, 0.0, 60.1)","(25.5, 0.0, 44.6)","(36.3, 0.0, 33.3)","(42.8, 0.0, 25.2)","(53.4, 0.0, 18.2)","(53.6, 0.0, 4.4)","(56.8, 0.0, 1.7)"],["(-55.0, 0.0, 0.0)","(-46.4, 0.0, 2.0)","(-39.0, 0.0, 1.2)","(-20.0, 0.0, -0.8)","(9.0, 0.0, -0.1)","(27.4, 0.0, -0.5)","(44.8, 0.0, -2.9)","(56.9, 0.0, -1.2)"],["(-60.0, 0.0, -5.5)","(-50.0, 0.0, -15.5)","(-41.0, 0.0, -28.5)","(-33.9, 0.0, -37.6)","(-19.9, 0.0, -49.5)","(0.0, 0.0, -62.3)","(15.7, 0.0, -55.0)","(32.2, 0.0, -39.3)","(39.0, 0.0, -29.5)","(54.0, 0.0, -20.0)","(55.0, 0.0, -5.0)","(58.3, 0.0, -2.7)"],["(-55.0, 0.0, 0.0)","(-46.4, 0.0, 2.0)","(-39.0, 0.0, 1.2)","(-20.0, 0.0, -0.8)","(9.0, 0.0, -0.1)","(27.4, 0.0, -0.5)","(44.8, 0.0, -2.9)","(58.0, 0.0, -1.0)"],["(-60.0, 0.0, 5.0)","(-53.6, 0.0, 18.0)","(-39.1, 0.0, 30.2)","(-20.1, 0.0, 51.2)","(0.0, 0.0, 60.1)","(25.5, 0.0, 44.6)","(36.3, 0.0, 33.3)","(42.8, 0.0, 25.2)","(53.4, 0.0, 18.2)","(53.6, 0.0, 4.4)","(57.9, 0.0, 0.9)"]],"1":{"state":"in","cfgID":"965","pos":"( -57400, -100, -2310)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"2":{"state":"in","cfgID":"965","pos":"( -57460, -100, 2210)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"3":{"state":"in","cfgID":"975","pos":"( 57570, -80, -2230)","fwd":"( -1000, 0, 0)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"4":{"state":"in","cfgID":"900","pos":"( -75680, -80, 0)","fwd":"( 0, 0, 1000)","hp":16000,"maxhp":16000,"speed":5000,"chrtype":2,"att":660},"5":{"state":"in","cfgID":"975","pos":"( 57330, -80, 2540)","fwd":"( -1000, 0, 0)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"6":{"state":"in","cfgID":"900","pos":"( 75140, -80, 0)","fwd":"( 0, 0, 1000)","hp":16000,"maxhp":16000,"speed":5000,"chrtype":2,"att":660},"7":{"state":"in","cfgID":"961","pos":"( -62407, -230, -154)","fwd":"( -799, 0, -601)","hp":3750,"maxhp":3750,"speed":5000,"chrtype":2,"att":130,"Hprec":10},"8":{"state":"in","cfgID":"961","pos":"( 62390, -270, 190)","fwd":"( 779, 0, 626)","hp":3750,"maxhp":3750,"speed":5000,"chrtype":2,"att":130,"Hprec":10},"9":{"state":"in","cfgID":"964","pos":"( -17640, -80, -53540)","fwd":"( 929, 0, -370)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"10":{"state":"in","cfgID":"963","pos":"( -41710, -80, -30310)","fwd":"( 899, 0, -439)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"11":{"state":"in","cfgID":"9622","pos":"( -52300, -80, -17540)","fwd":"( 838, 0, -546)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"12":{"state":"in","cfgID":"974","pos":"( 17700, -80, -53840)","fwd":"( -707, 0, -707)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"13":{"state":"in","cfgID":"973","pos":"( 41730, -80, -30320)","fwd":"( -707, 0, -707)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"14":{"state":"in","cfgID":"9722","pos":"( 52390, -80, -17420)","fwd":"( -640, 0, -768)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"15":{"state":"in","cfgID":"964","pos":"( -17110, -80, 2080)","fwd":"( 1000, 0, 0)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"16":{"state":"in","cfgID":"963","pos":"( -32930, -80, -2020)","fwd":"( 1000, 0, 0)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"17":{"state":"in","cfgID":"9621","pos":"( -46840, -80, 0)","fwd":"( 1000, 0, 0)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"18":{"state":"in","cfgID":"974","pos":"( 17110, -80, -2080)","fwd":"( -984, 0, -176)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"19":{"state":"in","cfgID":"973","pos":"( 32930, -80, 2020)","fwd":"( -971, 0, -240)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"20":{"state":"in","cfgID":"9721","pos":"( 46840, -80, 0)","fwd":"( -871, 0, -491)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"21":{"state":"in","cfgID":"964","pos":"( -17700, -80, 53840)","fwd":"( 575, 0, 818)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"22":{"state":"in","cfgID":"963","pos":"( -41550, -80, 30230)","fwd":"( 399, 0, 917)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"23":{"state":"in","cfgID":"9623","pos":"( -52330, -80, 17430)","fwd":"( 70, 0, 998)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"24":{"state":"in","cfgID":"974","pos":"( 17640, -80, 53540)","fwd":"( -981, 0, 194)","hp":1700,"maxhp":1700,"speed":5000,"chrtype":2,"att":130},"25":{"state":"in","cfgID":"973","pos":"( 41710, -80, 30310)","fwd":"( -708, 0, 706)","hp":1500,"maxhp":1500,"speed":5000,"chrtype":2,"att":130},"26":{"state":"in","cfgID":"9723","pos":"( 52330, -80, 17430)","fwd":"( -930, 0, 367)","hp":1300,"maxhp":1300,"speed":1500,"chrtype":2,"att":130},"27":{"state":"in","cfgID":"118","pos":"( -75000, 0, 2060)","fwd":"( 1000, 0, 0)","hp":750,"maxhp":750,"mp":300,"maxmp":300,"speed":3800,"gold":210,"att":44,"Hprec":15,"Skill0":{"ID":11801,"MaxCD":1000},"Skill1":{"ID":11810,"MaxCD":13000,"Cost":50},"Skill2":{"ID":11820,"MaxCD":12000,"Cost":60},"Skill3":{"ID":11830,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000},"equip0":{"ID":41301.0,"NUM":1.0},"buff":["369","90020"]},"28":{"state":"in","cfgID":"112","pos":"( -74280, 0, -1900)","fwd":"( 1000, 0, 0)","hp":750,"maxhp":750,"mp":300,"maxmp":300,"speed":3300,"gold":450,"att":44,"Hprec":15,"Skill0":{"ID":11201,"MaxCD":1000},"Skill1":{"ID":11210,"MaxCD":11000,"Cost":50},"Skill2":{"ID":11220,"MaxCD":12000,"Cost":50},"Skill3":{"ID":11230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"29":{"state":"in","cfgID":"108","pos":"( 75000, 0, -1610)","fwd":"( -1000, 0, 0)","hp":800,"maxhp":800,"maxmp":10,"speed":3500,"gold":450,"att":46,"Hprec":15,"Skill0":{"ID":10801,"MaxCD":1000},"Skill1":{"ID":10810,"MaxCD":9000},"Skill2":{"ID":10820,"MaxCD":12000},"Skill3":{"ID":10830,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"30":{"state":"in","cfgID":"122","pos":"( 74230, 0, 570)","fwd":"( -1000, 0, 0)","hp":875,"maxhp":875,"mp":300,"maxmp":300,"speed":3500,"gold":450,"att":39,"Hprec":15,"Skill0":{"ID":12201,"MaxCD":1000},"Skill1":{"ID":12210,"MaxCD":12000,"Cost":50},"Skill2":{"ID":12220,"MaxCD":12000,"Cost":50},"Skill3":{"ID":12230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"31":{"state":"in","cfgID":"101","pos":"( 75000, 0, 2900)","fwd":"( -1000, 0, 0)","hp":800,"maxhp":800,"maxmp":100,"speed":3500,"gold":450,"att":46,"Hprec":15,"Skill0":{"ID":10101,"MaxCD":1000},"Skill1":{"ID":10110,"MaxCD":4500,"Cost":25},"Skill2":{"ID":10120,"MaxCD":10000,"Cost":25},"Skill3":{"ID":10130,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"32":{"state":"in","cfgID":"120","pos":"( -74240, 0, 0)","fwd":"( 1000, 0, 0)","hp":750,"maxhp":750,"mp":400,"maxmp":400,"speed":3400,"gold":450,"att":45,"Hprec":15,"Skill0":{"ID":12001,"MaxCD":1000},"Skill1":{"ID":12010,"MaxCD":10000,"Cost":50},"Skill2":{"ID":12020,"MaxCD":7000,"Cost":70},"Skill3":{"ID":12030,"MaxCD":30000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"33":{"state":"in","cfgID":"117","pos":"( -76360, 0, 1140)","fwd":"( 1000, 0, 0)","hp":750,"maxhp":750,"mp":400,"maxmp":400,"speed":3300,"gold":450,"att":44,"Hprec":15,"Skill0":{"ID":11701,"MaxCD":1000},"Skill1":{"ID":11710,"MaxCD":12000,"Cost":50},"Skill2":{"ID":11720,"MaxCD":12000,"Cost":60},"Skill3":{"ID":11730,"MaxCD":45000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"34":{"state":"in","cfgID":"121","pos":"( 76660, 0, 1250)","fwd":"( -1000, 0, 0)","hp":800,"maxhp":800,"mp":300,"maxmp":300,"speed":3500,"gold":450,"att":46,"Hprec":15,"Skill0":{"ID":12101,"MaxCD":1000},"Skill1":{"ID":12110,"MaxCD":12000,"Cost":50},"Skill2":{"ID":12120,"MaxCD":11000,"Cost":46},"Skill3":{"ID":12130,"MaxCD":30000,"Cost":60},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"35":{"state":"in","cfgID":"112","pos":"( 76590, 0, -540)","fwd":"( -1000, 0, 0)","hp":750,"maxhp":750,"mp":300,"maxmp":300,"speed":3300,"gold":450,"att":44,"Hprec":15,"Skill0":{"ID":11201,"MaxCD":1000},"Skill1":{"ID":11210,"MaxCD":11000,"Cost":50},"Skill2":{"ID":11220,"MaxCD":12000,"Cost":50},"Skill3":{"ID":11230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"36":{"state":"in","cfgID":"103","pos":"( -77580, 0, -3390)","fwd":"( 1000, 0, 0)","hp":875,"maxhp":875,"speed":3500,"gold":450,"att":39,"Hprec":20,"Skill0":{"ID":10300,"MaxCD":1000},"Skill1":{"ID":10310,"MaxCD":8000,"Cost":43},"Skill2":{"ID":10320,"MaxCD":12000,"Cost":43},"Skill3":{"ID":10330,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}}}'
    json_middle = '{"wldstatic":{"ID":0},"wldruntime":{"tick":31218.0},"attackinfos":[{"atker":28,"tgtpos":"( -2047, 0, -319)","skill":11020},{"atker":32,"defer":28,"skill":10820}],"27":{"pos":"( 25317, 0, -44447)","gold":36,"Skill0":{"ID":10901,"MaxCD":1000},"Skill1":{"ID":10910,"MaxCD":11000,"Cost":50},"Skill2":{"ID":10920,"MaxCD":11000,"Cost":50},"Skill3":{"ID":10930,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"28":{"pos":"( 3499, 0, 670)","fwd":"( -984, 0, -176)","mp":354,"moving":0,"gold":216,"Skill0":{"ID":11001,"MaxCD":1000},"Skill1":{"ID":11010,"MaxCD":12000,"Cost":60},"Skill2":{"ID":11020,"MaxCD":13000,"Cost":50,"CD":12868},"Skill3":{"ID":11030,"MaxCD":45000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"29":{"pos":"( 27212, 0, 43854)","fwd":"( -683, 0, 730)","gold":36,"Skill0":{"ID":11701,"MaxCD":1000},"Skill1":{"ID":11710,"MaxCD":12000,"Cost":50},"Skill2":{"ID":11720,"MaxCD":12000,"Cost":60},"Skill3":{"ID":11730,"MaxCD":45000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"30":{"pos":"( 13241, 0, 896)","fwd":"( -1000, 0, -23)","gold":6,"Skill0":{"ID":10601,"MaxCD":1000},"Skill1":{"ID":10610,"MaxCD":10000,"Cost":50},"Skill2":{"ID":10620,"MaxCD":12000,"Cost":60},"Skill3":{"ID":10630,"MaxCD":45000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"31":{"pos":"( -22288, 0, -47448)","gold":36,"Skill0":{"ID":11201,"MaxCD":1000},"Skill1":{"ID":11210,"MaxCD":11000,"Cost":50},"Skill2":{"ID":11220,"MaxCD":12000,"Cost":50},"Skill3":{"ID":11230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"32":{"pos":"( 2514, 0, 493)","fwd":"( 984, 0, 176)","moving":0,"gold":36,"Skill0":{"ID":10801,"MaxCD":1000},"Skill1":{"ID":10810,"MaxCD":9000},"Skill2":{"ID":10820,"MaxCD":12000,"CD":12000},"Skill3":{"ID":10830,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"33":{"pos":"( -21460, 0, 49736)","fwd":"( 673, 0, 740)","gold":36,"Skill0":{"ID":11300,"MaxCD":1000},"Skill1":{"ID":11310,"MaxCD":12000,"Cost":60},"Skill2":{"ID":11320,"MaxCD":13000,"Cost":60},"Skill3":{"ID":11330,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"34":{"pos":"( -5975, 0, -413)","gold":36,"Skill0":{"ID":12901,"MaxCD":1000},"Skill1":{"ID":12910,"MaxCD":10000,"Cost":50},"Skill2":{"ID":12920,"MaxCD":10000,"Cost":60},"Skill3":{"ID":12930,"MaxCD":45000,"Cost":150},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"35":{"pos":"( -23267, 0, 47744)","gold":36,"Skill0":{"ID":11501,"MaxCD":1000},"Skill1":{"ID":11510,"MaxCD":11000},"Skill2":{"ID":11520,"MaxCD":12000},"Skill3":{"ID":11530,"MaxCD":45000},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000}},"36":{"gold":456,"Skill0":{"ID":10200,"MaxCD":1000},"Skill1":{"ID":10210,"MaxCD":9000,"Cost":50},"Skill2":{"ID":10220,"MaxCD":12000,"Cost":50},"Skill3":{"ID":10230,"MaxCD":45000,"Cost":100},"Skill4":{"ID":10002,"MaxCD":90000},"Skill5":{"ID":64141,"MaxCD":90000},"Skill6":{"ID":10000},"Skill7":{"ID":202,"MaxCD":12000},"Skill8":{"ID":10003,"MaxCD":20000},"buff":["90010","90025","102400","90020"]},"37":{"pos":"( 39363, 0, -1115)"},"38":{"pos":"( -37514, 0, 1027)","fwd":"( 995, 0, -102)"},"39":{"pos":"( 51978, 0, -19296)"},"40":{"pos":"( -48398, 0, -17363)"},"41":{"pos":"( 53112, 0, 19052)"},"42":{"pos":"( -51387, 0, 19899)"},"43":{"pos":"( 42387, 0, -1563)"},"44":{"pos":"( -40554, 0, 1331)"},"45":{"pos":"( 53291, 0, -16819)","fwd":"( -190, 0, -982)"},"46":{"pos":"( -50094, 0, -14819)"},"47":{"pos":"( 54354, 0, 16585)","fwd":"( -81, 0, 997)"},"48":{"pos":"( -53624, 0, 17865)","fwd":"( 762, 0, 648)"},"49":{"pos":"( 45411, 0, -1954)","fwd":"( -990, 0, 144)"},"50":{"pos":"( -43594, 0, 1648)"},"51":{"pos":"( 53875, 0, -13819)","fwd":"( -191, 0, -982)"},"52":{"pos":"( -51790, 0, -12275)"},"53":{"pos":"( 54602, 0, 13545)","fwd":"( -81, 0, 997)"},"54":{"pos":"( -54384, 0, 14905)","fwd":"( 248, 0, 969)"},"55":{"pos":"( 48435, 0, -1482)","fwd":"( -988, 0, -155)"},"56":{"pos":"( -46630, 0, 1897)","fwd":"( 995, 0, -96)"},"57":{"pos":"( 54462, 0, -10822)","fwd":"( -192, 0, -981)"},"58":{"pos":"( -53145, 0, -9560)","fwd":"( 358, 0, -934)"},"59":{"pos":"( 54853, 0, 10505)","fwd":"( -82, 0, 997)"},"60":{"pos":"( -55144, 0, 11945)"}}'
    replayer = Replayer()
    replayer.parse_state_log(json_middle)