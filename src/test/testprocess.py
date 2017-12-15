#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Process

import random
import json as JSON
import time
import numpy as np
# from multiprocessing import SimpleQueue

from model.stateinfo import StateInfo
from util.multiprocessing import SimpleQueue


def start_consumer(battle_id_num, request_queues, result_queues):
    consumer_times = []
    while True:
        indexs = []
        requests = []
        for index, request_queue in enumerate(request_queues):

            if not request_queue.empty():
                request = request_queue.get()
                requests.append(request)
                indexs.append(index)

        begin_time = time.time()
        for index, json_str in zip(indexs, requests):
            obj = JSON.loads(json_str)
            raw_state_info = StateInfo.decode(obj)
            rand = np.random.rand(3, 3700)
            result_queues[index].put(rand)

        end_time = time.time()
        delta_millionseconds = (end_time - begin_time) * 1000
        consumer_times.append(delta_millionseconds)
        if len(consumer_times) >= 1000:
            print("model get_action average calculate time(ms)", sum(consumer_times) // float(len(consumer_times)))
            consumer_times = []


class TestConsumer:
    def __init__(self, battle_id_num):
        self.battle_id_num = battle_id_num
        self.request_queues = []
        self.result_queues = []
        for i in range(battle_id_num):
            request_queue = SimpleQueue()
            result_queue = SimpleQueue()
            self.request_queues.append(request_queue)
            self.result_queues.append(result_queue)

    def start(self):
        p = Process(target=start_consumer, args=(self.battle_id_num, self.request_queues, self.result_queues))
        p.start()

    @staticmethod
    def read_process(json_str, request_queue, result_queue):
        request_queue.put(json_str)

        while True:
            if not result_queue.empty():
                result = result_queue.get()
                return result

def producer_process(name, raw_log_path, request_queue, result_queue):
        raw_file = open(raw_log_path, "r")
        lines = raw_file.readlines()
        producer_times = []
        for line in lines:
            time.sleep(random.randint(1, 5) / float(1000))
            json_str = line[23:]
            begin_time = time.time()
            response = TestConsumer.read_process(json_str, request_queue, result_queue)
            end_time = time.time()
            delta_millionseconds = (end_time - begin_time) * 1000
            producer_times.append(delta_millionseconds)
            if len(producer_times) >= 100:
                print("model producer_process average calculate time(ms)", sum(producer_times) // float(len(producer_times)))
                producer_times = []
        print(name, 'done')


if __name__ == "__main__":
    num = 40
    consumer = TestConsumer(num)
    consumer.start()
    print('训练器准备完毕')

    for i in range(40):
        request_queue = consumer.request_queues[i]
        result_queue = consumer.result_queues[i]
        producer = Process(target=producer_process,
                           args=('process', '/Users/sky4star/Github/zy2go/battle_logs/test/raw_1.log',
                                 request_queue, result_queue))
        producer.start()
        producer.join()
    while 1:
        pass


