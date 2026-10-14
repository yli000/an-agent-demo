import time

import json

import os

import requests

import prompts

from utils import logger

from utils.redis_tool import RedisClient


TIMEOUT = 2.0

MAX_HIS = 6

TTL = 60

CHUNK_SIZE = 1024

MAX_TOKEN = 2048

REDIS_KEY = "voice:arbitration_history:"

_redis_client = RedisClient()


API_KEY = os.environ["API_KEY"]

DOUBAO_URL = os.environ["BASE_URL"]

SYSTEM_PROMPT = prompts.ARBITRAION_SYSTEM_PROMPT


def request_arbitration(query, sender_id):

    headers = {

        "Content-Type": "application/json",

        "Authorization": API_KEY

    }

    message = [{"role": "system", "content": SYSTEM_PROMPT}]


    try:

        start_time = time.time()


        # 看对话历史，

        history = _redis_client.get(REDIS_KEY + sender_id)

        if history:

            history = json.loads(history)

        else:

            history = []


        history.append({"role": "user", "content": query})


        message.extend(history)


        body = dict(

            model="YOUR_MODEL_DEPLOYMENT_ID", # 可选模型：豆包或 DeepSeek；实际型号以部署配置为准。

            messages=message,

            max_tokens=MAX_TOKEN,

            temperature=0,

            stream=True

        )

        response = requests.post(

            DOUBAO_URL,

            headers=headers,

            json=body,

            stream=True,

            timeout=TIMEOUT

        )

        text = "A" # 防崩溃 & ‘任务’优先

        for r in response.iter_lines(

                chunk_size=CHUNK_SIZE, decode_unicode=False, delimiter=b'\n'):

            r = r.decode("utf-8")

            if not r:

                continue

            r = r.lstrip("data: ")

            if r == "[DONE]":

                break

            r = json.loads(r.lstrip("data: "))

            text = r["choices"][0]["delta"]["content"]

            if not text:

                continue

            break

        logger.info(

            f"Arbitration history: {history}, query:{query}, result:{text}, cost time:{time.time() - start_time}")

        if text not in ["A", "B", "C", "D"]:

            text = "A"

        history.append({"role": "assistant", "content": text})

        history = history[-MAX_HIS:]

        history_str = json.dumps(history, ensure_ascii=False)

        _redis_client.set(REDIS_KEY + sender_id, history_str, ex=TTL)

        if text in ["C", "D"]:

            text = "chat"

        elif text == "B":

            text = "faq" # 最后好像没用到

        else:

            text = "task"


        return text


    except Exception as e:

        logger.info(f"Arbitration API error: {e}")

        return "task"


if __name__ == '__main__':

    while True:

        query = input("输入:")

        res = request_arbitration(query, "131")

        print(res)
