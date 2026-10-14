import os

import requests

import uuid

import json

from tqdm import tqdm

from collections import defaultdict


INTENT_URL = os.environ["INTENT_URL"]


def get_intent(query):

    headers = {'Content-Type': 'application/json'}

    data = {"query": query, "trace_id": str(uuid.uuid1())}

    response = requests.post(url=INTENT_URL, headers=headers, data=json.dumps(data))

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


    top1_right = 0

    top5_right = 0

    total = 0

    errors = []


    for text, label, slots in tqdm(sampled_data):

        try:

            response = get_intent(text)

            results = response["data"].split(",")

            scores = response["score"].split(",")


            top1_match = results[0] == label

            top5_match = label in results


            if top1_match:

                top1_right += 1

            if top5_match:

                top5_right += 1

            else:

                errors.append({

                    "query": text,

                    "expected": label,

                    "predicted_top5": results,

                    "scores": scores

                })


            total += 1

        except Exception as e:

            print(f"Error processing: {text}, error: {e}")

            total += 1


    print(f"\n=== BERT Intent Results ===")

    print(f"Top1 accuracy: {top1_right}/{total} = {top1_right/total:.4f}")

    print(f"Top5 accuracy: {top5_right}/{total} = {top5_right/total:.4f}")


    # 展示正确标签未进入前五候选的错误样本。

    print(f"\n=== Samples where label NOT in top5 (first 10) ===")

    for err in errors[:10]:

        print(f"Query: {err['query']}")

        print(f"  Expected: {err['expected']}")

        print(f"  Predicted top5: {err['predicted_top5']}")

        print(f"  Scores: {err['scores']}")

        print()
