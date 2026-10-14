# -*- coding: utf-8 -*-

"""

使用 LLM 根据 function.py 的 schema 重新生成测试数据的槽位标注

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


API_KEY = os.environ.get("API_KEY")

BASE_URL = os.environ.get("BASE_URL")


# 构建 intent_id -> function schema 映射

id2name = {}

with open("config/class.txt", 'r') as f:

    for line in f:

        id, name, func = line.strip().split(':')

        id2name[id] = name


name2schema = {}

for tool in tools1:

    name = tool['function']['name']

    name2schema[name] = tool['function']['parameters']['properties']


def extract_slots_with_llm(query, intent_name, schema):

    """调用 LLM 提取槽位"""

    if not schema:

        return {}


    # 构建 prompt

    schema_desc = json.dumps(schema, indent=2, ensure_ascii=False)

    prompt = f"""Extract slot values from the user query based on the schema below.

Return a JSON object with slot names as keys. Use empty string "" for slots not mentioned.



Schema:

{schema_desc}



User query: "{query}"



Return ONLY the JSON object, no explanation."""


    headers = {

        "Authorization": API_KEY,

        "Content-Type": "application/json"

    }

    data = {

        "model": "YOUR_MODEL_DEPLOYMENT_ID",

        "messages": [{"role": "user", "content": prompt}],

        "temperature": 0

    }


    try:

        response = requests.post(BASE_URL, headers=headers, json=data, timeout=30)

        result = response.json()

        content = result['choices'][0]['message']['content']

        # 提取 JSON

        content = content.strip()

        if content.startswith('```'):

            content = content.split('```')[1]

            if content.startswith('json'):

                content = content[4:]

        return json.loads(content)

    except Exception as e:

        print(f"Error for '{query}': {e}")

        return {}


def main():

    # 读取测试数据

    input_file = "test/data/single_slots_new.txt"

    output_file = "test/data/single_slots_regenerated.txt"


    with open(input_file, 'r') as f:

        lines = f.readlines()


    results = []

    for line in tqdm(lines, desc="Processing"):

        parts = line.strip().split('\t')

        query, intent_id, old_slots = parts[0], parts[1], parts[2]


        intent_name = id2name.get(intent_id)

        schema = name2schema.get(intent_name, {})


        if schema:

            new_slots = extract_slots_with_llm(query, intent_name, schema)

        else:

            new_slots = {}


        results.append(f"{query}\t{intent_id}\t{json.dumps(new_slots, ensure_ascii=False)}")


    with open(output_file, 'w') as f:

        f.write('\n'.join(results))


    print(f"\nSaved to {output_file}")


if __name__ == "__main__":

    main()
