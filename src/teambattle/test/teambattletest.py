# -*- coding: utf8 -*-
import random
import time
from multiprocessing import Process, Manager, Lock

from teambattle.teambattletrainer_manager import TeamBattleTrainerManager
from common import cf as C


def read_process(battle_id, raw_log_path):
    raw_file = open(raw_log_path, "r")
    lines = raw_file.readlines()
    producer_times = []
    for line in lines:
        time.sleep(random.randint(1,5)/float(1000))
        json_str = line[23:]
        json_str = json_str.replace('"ID":1', '"ID":'+str(battle_id), 1)
        begin_time = time.time()
        response = TeamBattleTrainerManager.One.read_process(json_str)
        print(response)
        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        producer_times.append(delta_millionseconds)
        if len(producer_times) >= 100:
            print("model producer_process average calculate time(ms)",
                  sum(producer_times) // float(len(producer_times)))
            producer_times = []

    print(battle_id, 'done')

if __name__ == "__main__":
    try:
        num = 1
        manager = TeamBattleTrainerManager(0, num, C.RUN_MODE_PREDICT)
        print('训练器准备完毕')

        read_process(1, '/Users/sky4star/Github/zy2go/battle_logs/model_2018-02-28111835.446603/raw_1.log')
    except Exception as e:
        print(e)