# -*- coding: utf-8 -*-

"""

使用 function call 方式重新生成测试数据的槽位标注

和 NLU 服务使用完全一样的方式

"""

import os

import sys

import json

import requests

from tqdm import tqdm


# 设置工作目录

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

os.chdir(PROJECT_ROOT)

sys.path.insert(0, PROJECT_ROOT)


from function_call.function import tools1

import prompts


API_KEY = os.environ.get("API_KEY")

BASE_URL = os.environ.get("BASE_URL")


# 构建映射

id2name = {}

id2func = {}

with open("config/class.txt", 'r') as f:

    for line in f:

        id, name, func = line.strip().split(':')

        id2name[id] = name

        id2func[id] = func


# 构建 tool_map

tool_map = {}

for item in tools1:

    name = item["function"]["name"]

    if name not in tool_map:

        tool_map[name] = [item]

    else:

        tool_map[name].append(item)


def extract_slots_with_function_call(query, intent_id):

    """使用 function call 方式提取槽位，和 NLU 服务一样"""

    func_name = id2func.get(intent_id)

    if not func_name:

        return {}


    tool_lst = tool_map.get(func_name, [])

    if not tool_lst:

        return {}


    headers = {

        "Authorization": API_KEY,

        "Content-Type": "application/json"

    }


    # 和 NLU 服务完全一样的调用方式

    messages = [

        {"role": "system", "content": prompts.NLU_SYSTEM_PROMPT},

        {"role": "user", "content": query}

    ]


    data = {

        "model": "YOUR_MODEL_DEPLOYMENT_ID",

        "messages": messages,

        "tools": tool_lst,

        "temperature": 1e-6,

        "top_p": 0

    }


    try:

        response = requests.post(BASE_URL, headers=headers, json=data, timeout=30)

        result = response.json()

        tool_calls = result['choices'][0]['message'].get('tool_calls')


        if not tool_calls:

            return {}


        # 提取槽位

        arguments = tool_calls[0].get('function', {}).get('arguments', '{}')

        slots = json.loads(arguments)


        # 过滤空值

        return {k: v for k, v in slots.items() if v}


    except Exception as e:

        print(f"Error for '{query}': {e}")

        return {}


def main():

    input_file = "test/data/single_slots_new.txt"

    output_file = "test/data/single_slots_v2.txt"


    with open(input_file, 'r') as f:

        lines = f.readlines()


    results = []

    for line in tqdm(lines, desc="Processing"):

        parts = line.strip().split('\t')

        query, intent_id, old_slots = parts[0], parts[1], parts[2]


        new_slots = extract_slots_with_function_call(query, intent_id)

        results.append(f"{query}\t{intent_id}\t{json.dumps(new_slots, ensure_ascii=False)}")


    with open(output_file, 'w') as f:

        f.write('\n'.join(results))


    print(f"\nSaved to {output_file}")


if __name__ == "__main__":

    main()
