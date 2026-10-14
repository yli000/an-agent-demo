# E2E测试


import os

import json

import random

import socketio

import queue

import sys


URL = os.environ["ENTRY_URL"]


sio = socketio.Client()

data_q = queue.Queue(2000)


# 静默模式，不打印每条响应

VERBOSE = False


@sio.on("connect")

def on_connect():

    if VERBOSE:

        print("connected to server")


@sio.on("disconnect")

def on_disconnect():

    if VERBOSE:

        print("disconnected to server")


@sio.on("message")

def on_message(data):

    if VERBOSE:

        print('Received message:', data)


@sio.on("error")

def on_error(e):

    print('Error:', e)


@sio.on("request_nlu")

def on_response(data):

    data = json.loads(data)

    data_q.put(data)

    if VERBOSE:

        print('Response:', data)


def rand_str(size=6):

    return "".join(random.sample("1234567890zyxwvutsrqponmlkjihgfedcba", size))


def print_progress(current, total, bar_length=40):

    """打印进度条"""

    percent = current / total

    filled = int(bar_length * percent)

    bar = '█' * filled + '░' * (bar_length - filled)

    sys.stdout.write(f'\r[{bar}] {current}/{total} ({percent*100:.1f}%)')

    sys.stdout.flush()


if __name__ == "__main__":

    # 读取所有行并计算总数

    with open("test/data/multi_test.txt") as fd:

        lines = [line for line in fd if line.strip()]


    total_conversations = len(lines)

    print(f"E2E Test: {total_conversations} conversations to process")

    print("=" * 60)


    fw = open("test/result/multi_test_output.txt", "w")


    for conv_idx, line in enumerate(lines, 1):

        sio.connect(URL)

        data = {

            "sender_id": rand_str(9)

        }

        sessions = [t.strip() for t in line.split("\t") if t.strip()]


        for query in sessions:

            data["trace_id"] = rand_str(9)

            data["query"] = query

            data["enable_dm"] = False

            sio.emit("request_nlu", json.dumps(data, ensure_ascii=False))


            result = {}

            result["query"] = query

            result["res"] = []


            while data_q.empty():

                while True:

                    response = data_q.get()

                    result["res"].append(response)

                    if response.get("intent") != "闲聊百科" or response.get("intent") == "闲聊百科" and response.get("status") == 2:

                        break

                break


            result_str = json.dumps(result, ensure_ascii=False)

            fw.write(result_str + "\n")

            fw.flush()


        sio.disconnect()


        # 更新进度条

        print_progress(conv_idx, total_conversations)


    print()  # 换行

    print("=" * 60)

    print(f"Done! Results saved to: test/result/multi_test_output.txt")

    fw.close()
