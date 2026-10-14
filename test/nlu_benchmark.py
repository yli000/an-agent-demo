"""

NLU服务压力测试 (使用locust)



运行命令：

locust -f nlu_benchmark.py --host http://127.0.0.1:8009 --headless -u 10 -r 5 -t 60s --csv=result/nlu_benchmark



参数说明：

  -u 10: 10个并发用户

  -r 5: 每秒启动5个用户

  -t 60s: 运行60秒

  --csv=result/nlu_benchmark: 保存结果到 result/nlu_benchmark_stats.csv



结果文件：

  result/nlu_benchmark_stats.csv - 统计摘要

  result/nlu_benchmark_stats_history.csv - 历史数据

  result/nlu_benchmark_failures.csv - 失败记录

"""


import random

import uuid

from locust import HttpUser, task, between


fd = open("../train/data/intent/test.txt")

samples = [k.split("\t")[0] for k in fd]


class User(HttpUser):

    wait_time = between(3, 5)


    @task

    def task_post_archive(self):

        trace_id = f'cevi{uuid.uuid4().hex}'

        path = '/chatnlu-server/v1'

        headers = {

            'Content-Type': 'application/json'

        }

        data = {

            "query": random.choice(samples),

            "trace_id": trace_id

        }

        self.client.post(path, json=data, headers=headers)
