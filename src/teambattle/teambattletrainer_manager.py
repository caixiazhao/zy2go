#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process, Manager, Lock

import queue
import sys
import json as JSON
import traceback
import time

from model.stateinfo import StateInfo
from teambattle.teambattletrainer import TeamBattleTrainer


def start_team_battle_trainer_process(p_battle_id, p_request_dict, p_result_dict, lock):

    battle_trainer = TeamBattleTrainer(p_battle_id)

    while True:
        json_str = None
        if p_battle_id in p_request_dict.keys():
            json_str = p_request_dict[p_battle_id]
            del p_request_dict[p_battle_id]

        if json_str is not None:
            try:
                response = battle_trainer.build_response(json_str)
                with lock:
                    # print('trainer_process', p_battle_id, 'put a result', time.time())
                    p_result_dict[p_battle_id] = response
            except Exception as e:
                print('linetrainer manager catch exception', traceback.format_exc())
                with lock:
                    p_result_dict[p_battle_id] = '{}'


class TeamBattleTrainerManager:
    def __init__(self, battle_id_num):
        manager = Manager()
        self.request_dict = manager.dict()
        self.result_dict = manager.dict()
        self.lock = Lock()
        self.battle_trainer_process_list = []

        for battle_id in range(1, battle_id_num+1):
            battle_trainer_process = Process(target=start_team_battle_trainer_process,
                                           args=(battle_id, self.request_dict, self.result_dict, self.lock,))
            self.battle_trainer_process_list.append(battle_trainer_process)
        print('训练器初始化完毕, 训练器数量', battle_id_num)

    def start(self):
        for battle_trainer_process in self.battle_trainer_process_list:
            battle_trainer_process.start()

        print('训练器启动完毕')

    @staticmethod
    def read_process(json_str, p_request_dict, p_result_dict, lock):
        begin_time = time.time()
        obj = JSON.loads(json_str)
        raw_state_info = StateInfo.decode(obj)
        p_battle_id = raw_state_info.battleid
        # if raw_state_info.tick == -1:
        #     print('read_process: need to handle ', p_battle_id, raw_state_info.tick, 'raw log', json_str)
        # else:
        #     print('read_process: need to handle ', p_battle_id, raw_state_info.tick)

        with lock:
            # print('read_process', p_battle_id, 'send a request', raw_state_info.tick)
            p_request_dict[p_battle_id] = json_str

        try:
            while True:
                if p_battle_id in p_result_dict.keys():
                    with lock:
                        # print('read_process', p_battle_id, 'get a result', raw_state_info.tick)
                        result = p_result_dict[p_battle_id]
                        del p_result_dict[p_battle_id]
                        end_time = time.time()
                        print('read_process', p_battle_id, raw_state_info.tick, (end_time - begin_time) * 1000, '取得结果', result)
                        return result
        except queue.Empty:
            print("LineTrainerManager Exception empty")
            return '{}'
        except Exception:
            print("LineTrainerManager Exception")
            type, value, traceback = sys.exc_info()
            traceback.print_exc()
            return '{}'