import os

import requests

import uuid

import json

from tqdm import tqdm

from collections import defaultdict


URL = os.environ["NLU_URL"]


def get_completion(query):

    headers = {'Content-Type': 'application/json'}

    data = {"query": query, "trace_id": str(uuid.uuid1()), "enable_dm": False}

    response = requests.post(url=URL, headers=headers, data=json.dumps(data))

    return response.json()


if __name__ == '__main__':

    # 读取全部数据。

    fd = open("data/single_slots_new.txt")

    data = fd.readlines()


    # 按意图标签分组。

    intent_groups = defaultdict(list)

    for line in data:

        parts = line.strip().split("\t")

        if len(parts) == 3:

            text, label, slots = parts

            intent_groups[label].append((text, label, slots))


    # 每个意图抽取两个样本。

    sampled_data = []

    for label, items in intent_groups.items():

        sampled_data.extend(items[:2])


    print(f"Total intents: {len(intent_groups)}, Sampled data: {len(sampled_data)}")


    intent_right = 0

    slots_right = 0

    total = 0

    errors = []


    for text, label, slots in tqdm(sampled_data):

        try:

            response = get_completion(text)

            pred_slots = response.get("slots", {})

            expected_slots = json.loads(slots)


            intent_match = response.get("intent_id") == label

            slots_match = expected_slots == pred_slots


            if intent_match:

                intent_right += 1

            if slots_match:

                slots_right += 1


            if not intent_match or not slots_match:

                errors.append({

                    "query": text,

                    "expected_intent": label,

                    "predicted_intent": response.get("intent_id"),

                    "expected_slots": expected_slots,

                    "predicted_slots": pred_slots,

                    "intent_match": intent_match,

                    "slots_match": slots_match

                })


            total += 1

        except Exception as e:

            print(f"Error processing: {text}, error: {e}")

            total += 1


    print(f"\n=== Results ===")

    print(f"Intent accuracy: {intent_right}/{total} = {intent_right/total:.4f}")

    print(f"Slots accuracy: {slots_right}/{total} = {slots_right/total:.4f}")


    # 展示部分错误样本。

    print(f"\n=== Sample Errors (first 10) ===")

    for err in errors[:10]:

        print(f"Query: {err['query']}")

        print(f"  Expected intent: {err['expected_intent']}, Predicted: {err['predicted_intent']}, Match: {err['intent_match']}")

        print(f"  Expected slots: {err['expected_slots']}")

        print(f"  Predicted slots: {err['predicted_slots']}")

        print(f"  Slots match: {err['slots_match']}")

        print()
