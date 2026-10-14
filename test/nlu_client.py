"""

NLU准确率测试



用法:

    python nlu_client.py                    # 测试全部数据

    python nlu_client.py --sample 100       # 随机抽样100条测试

    python nlu_client.py --sample 100 --save  # 抽样测试并保存详细结果

"""


import os

import requests

import uuid

import json

import random

import argparse

from datetime import datetime

from tqdm import tqdm


URL = os.environ["NLU_URL"]

RESULT_DIR = "result"


def get_completion(query):

    headers = {'Content-Type': 'application/json'}

    data = {"query": query, "trace_id": str(uuid.uuid1()), "enable_dm": False}

    response = requests.post(url=URL, headers=headers, data=json.dumps(data))

    return response.json()


def run_test(data_file, sample_size=None, save_results=False):

    """运行NLU测试"""

    with open(data_file) as fd:

        data = fd.readlines()


    # 抽样

    if sample_size and sample_size < len(data):

        data = random.sample(data, sample_size)

        print(f"Sampled {sample_size} from {len(data)} total samples")


    intent_right = 0

    slots_right = 0

    total = 0

    detailed_results = []


    for idx in tqdm(range(len(data)), desc="Testing NLU"):

        line = data[idx]

        parts = line.strip().split("\t")

        if len(parts) < 3:

            continue


        text, label, slots_str = parts[0], parts[1], parts[2]

        response = get_completion(text)

        pred_slots = response.get("slots", {})

        expected_slots = json.loads(slots_str)


        intent_correct = response.get("intent_id") == label

        slots_correct = expected_slots == pred_slots


        if slots_correct:

            slots_right += 1

        if intent_correct:

            intent_right += 1

        total += 1


        # 保存详细结果

        if save_results:

            detailed_results.append({

                "query": text,

                "expected_intent_id": label,

                "predicted_intent_id": response.get("intent_id"),

                "predicted_intent": response.get("intent"),

                "intent_correct": intent_correct,

                "expected_slots": expected_slots,

                "predicted_slots": pred_slots,

                "slots_correct": slots_correct,

                "cost": response.get("cost", 0)

            })


    # 计算准确率

    intent_acc = intent_right / total if total > 0 else 0

    slots_acc = slots_right / total if total > 0 else 0


    print("\n" + "=" * 50)

    print(f"NLU Test Results")

    print("=" * 50)

    print(f"Total samples: {total}")

    print(f"Intent accuracy: {intent_acc:.4f} ({intent_right}/{total})")

    print(f"Slots accuracy:  {slots_acc:.4f} ({slots_right}/{total})")

    print("=" * 50)


    # 保存结果

    if save_results:

        os.makedirs(RESULT_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        result_file = os.path.join(RESULT_DIR, f"nlu_test_result_{timestamp}.json")


        output = {

            "generated_at": datetime.now().isoformat(),

            "total_samples": total,

            "intent_accuracy": round(intent_acc, 4),

            "slots_accuracy": round(slots_acc, 4),

            "intent_correct": intent_right,

            "slots_correct": slots_right,

            "results": detailed_results

        }


        with open(result_file, 'w', encoding='utf-8') as f:

            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\nDetailed results saved to: {result_file}")


    return intent_acc, slots_acc


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='NLU accuracy test')

    parser.add_argument('--sample', type=int, default=None,

                        help='Number of samples to test (default: all)')

    parser.add_argument('--save', action='store_true',

                        help='Save detailed results to JSON file')

    parser.add_argument('--data', type=str, default="data/single_slots_new.txt",

                        help='Test data file path')

    args = parser.parse_args()


    run_test(args.data, sample_size=args.sample, save_results=args.save)
