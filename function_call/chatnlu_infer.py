import os

import sys

import json

import uuid

import random

import numpy as np

import requests

import base64

import time

import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:

    sys.path.insert(0, PROJECT_ROOT)

if CURRENT_DIR not in sys.path:

    sys.path.insert(0, CURRENT_DIR)


import prompts  # noqa: E402

from slot_process import intent_slot  # noqa: E402

from function import tools1  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402

from utils import logger  # noqa: E402

from dm.factory import DMFactory  # noqa: E402


## 创建FastAPI应用

app = FastAPI()


MAX_CONF = 0.98

TIMEOUT = 5

INTENT_URL = os.environ["INTENT_URL"]

DOUBAO_API_KEY = os.environ["API_KEY"]

DOUBAO_URL = os.environ["BASE_URL"]


id2func = {}

func2name = {}

name2id = {}

with open("../config/class.txt", 'r', encoding='utf-8') as mapfile:

    for line in mapfile:

        id, name, func = line.strip().split(":")

        id2func[id] = func

        func2name[func] = name

        name2id[name] = id


tool_map = {}

with open("../config/slot_intent.json", "r", encoding="utf-8") as slotfile:

    slot_map = json.load(slotfile)

    for item in tools1:

        name = item["function"]["name"]

        if name not in tool_map.keys():

            lst = [item]

            new_dict = {name: lst}

            tool_map.update(new_dict)

        else:

            tool_map.get(name).append(item)


def send_messages(messages, tool_lst):

    headers = {

        "Authorization": DOUBAO_API_KEY,

        "Content-Type": "application/json"

    }

    data = {

        "model": "YOUR_MODEL_DEPLOYMENT_ID", # deepseek v3.2，支持functioncall

        "messages": messages,

        "tools": tool_lst,

        "tool_choice": "required",  # 强制调用function

        "temperature": 1e-6,

        "top_p": 0

    }

    try:

        response = requests.post(

            DOUBAO_URL,

            headers=headers,

            data=json.dumps(data),

            timeout=TIMEOUT

        )

        res = response.content.decode('utf-8')

        res = json.loads(res)

        return res['choices'][0]['message']['tool_calls']

    except Exception as e:

        logger.error(f"Doubao error: {e}")

        return None


def intent_recall(query, trace_id):

    headers = {'Content-Type': 'application/json'}

    data = {"query": query, "trace_id": str(uuid.uuid1())}

    response = requests.post(url=INTENT_URL, headers=headers, data=json.dumps(data))

    return response.json()


def predict(query, trace_id):

    try:

        start = time.time()

        intent_rec = intent_recall(query, trace_id)

        results = intent_rec["data"].split(",")

        scores = [float(k) for k in intent_rec["score"].split(",")]

        max_score = max(scores)

        logger.info(f"top5：{intent_rec['data']}, scores: {scores}, cost: {time.time() - start}")


        # 如果置信度高，直接信任意图模型的 top1 结果

        if max_score > MAX_CONF:

            top1_func = id2func.get(results[0])

            if top1_func:

                # 只用 top1 的 function 让 LLM 提取槽位

                now_tool = tool_map.get(top1_func, [])

                if now_tool:

                    header = [{"role": "system", "content": prompts.NLU_SYSTEM_PROMPT}]

                    context = [{"role": "user", "content": query}]

                    messages = header + context

                    result = send_messages(messages, now_tool)

                    if result:

                        nlu = intent_slot(result, func2name, slot_map)

                        return nlu

            return "Unknown-none"


        now_tool = []

        for t in results:

            func = id2func.get(t)

            lst_a = tool_map.get(func)

            if lst_a:

                for s in lst_a:

                    now_tool.append(s)

            else:

                continue


        header = [{"role": "system", "content": prompts.NLU_SYSTEM_PROMPT}]

        context = [{"role": "user", "content": query}]

        messages = header + context

        start_time = time.time()

        result = send_messages(messages, now_tool)

        logger.info(f"llm结果：{result}")

        logger.info(f"function调用时间:{time.time() - start_time}")

        if not result:

            return "Unknown-none"


        nlu = intent_slot(result, func2name, slot_map)

    except:

        return "Unknown-none"


    logger.info(f"返回结果：{nlu}")


    return nlu


@app.post("/chatnlu-server/v1")

async def inference(request: Request):

    json_info = await request.json()


    begin = time.time()

    query = json_info.get("query")

    enable_dm = json_info.get("enable_dm", True)

    trace_id = json_info.get("trace_id", "1")


    # 抽取意图和槽位

    nlu = predict(query, trace_id)


    # NLU后处理

    nlu_items = nlu.split("-")

    intent = nlu_items[0]

    if len(nlu_items) > 2:

        slots_str = "-".join(nlu_items[1:])

    else:

        slots_str = nlu_items[1]


    if slots_str != "none":

        slots = {}

        for item in slots_str.split(","):

            if ":" in item:

                # 只在第一个冒号处分割，处理值中包含冒号的情况（如时间 "8:00 AM"）

                parts = item.split(":", 1)

                if len(parts) == 2:

                    k, v = parts

                    slots[k] = v

    else:

        slots = {}

    intent_id = name2id.get(intent)

    func_name = id2func.get(intent_id)


    response = {

        "query": query,

        "tarce_id": trace_id,

        "intent": intent,

        "intent_id": intent_id,

        "function": func_name,

        "slots": slots,

    }


    if enable_dm:

        for name in ["weather", "time", "play_music"]:

            dm_result = await DMFactory.get(name)(func_name, query, slots)

            if dm_result:

                tool_response, nlg = dm_result

                response["tool"] = tool_response

                response["nlg"] = nlg


    cost = time.time() - begin

    response["cost"] = cost


    return response


if __name__ == '__main__':

    uvicorn.run(app, host='0.0.0.0', port=8009, workers=1)
