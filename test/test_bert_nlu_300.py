"""

测试脚本：对比BERT和完整NLU流程在相同300条数据上的效果

"""

import os

import sys

import requests

import uuid

import json

import random

from tqdm import tqdm


# 固定随机种子，确保两个测试使用相同的300条数据

RANDOM_SEED = 42

SAMPLE_SIZE = 300


INTENT_URL = os.environ.get("INTENT_URL", "http://127.0.0.1:8008/intent-server/v1")

NLU_URL = os.environ.get("NLU_URL", "http://127.0.0.1:8009/chatnlu-server/v1")


def load_and_sample_data(filepath, seed, size):

    """加载数据并抽样"""

    with open(filepath, 'r') as f:

        data = f.readlines()


    random.seed(seed)

    sampled = random.sample(data, min(size, len(data)))

    return sampled


def test_bert_only(data):

    """只测试BERT intent分类的top1准确率"""

    print("\n" + "="*60)

    print("测试 BERT Intent 分类 (Top1 准确率)")

    print("="*60)


    right = 0

    total = 0

    errors = []


    for idx in tqdm(range(len(data)), desc="BERT测试"):

        line = data[idx]

        parts = line.strip().split("\t")

        if len(parts) < 2:

            continue

        text, label = parts[0], parts[1]


        try:

            headers = {'Content-Type': 'application/json'}

            req_data = {"query": text, "trace_id": str(uuid.uuid1())}

            response = requests.post(url=INTENT_URL, headers=headers, data=json.dumps(req_data), timeout=10)

            result = response.json()


            pred_top1 = result["data"].split(",")[0]

            if pred_top1 == label:

                right += 1

            else:

                if len(errors) < 10:  # 只记录前10个错误

                    errors.append({

                        "text": text,

                        "true_label": label,

                        "pred_label": pred_top1,

                        "top5": result["data"],

                        "scores": result["score"]

                    })

            total += 1

        except Exception as e:

            print(f"Error: {e}")

            continue


    acc = right / total if total > 0 else 0

    print(f"\nBERT Intent Top1 准确率: {right}/{total} = {acc:.4f} ({acc*100:.2f}%)")


    if errors:

        print(f"\n前{len(errors)}个错误样例:")

        for i, err in enumerate(errors):

            print(f"  [{i+1}] text: {err['text'][:50]}...")

            print(f"      true: {err['true_label']}, pred: {err['pred_label']}, top5: {err['top5']}")


    return acc, right, total


def test_full_nlu(data):

    """测试完整NLU流程 (BERT + LLM)"""

    print("\n" + "="*60)

    print("测试完整 NLU 流程 (BERT + LLM Function Call)")

    print("="*60)


    intent_right = 0

    slots_right = 0

    total = 0

    intent_errors = []

    slot_errors = []


    for idx in tqdm(range(len(data)), desc="NLU测试"):

        line = data[idx]

        parts = line.strip().split("\t")

        if len(parts) < 3:

            continue

        text, label, slots_str = parts[0], parts[1], parts[2]


        try:

            headers = {'Content-Type': 'application/json'}

            req_data = {"query": text, "trace_id": str(uuid.uuid1()), "enable_dm": False}

            response = requests.post(url=NLU_URL, headers=headers, data=json.dumps(req_data), timeout=30)

            result = response.json()


            pred_intent_id = result.get("intent_id")

            pred_slots = result.get("slots", {})

            true_slots = json.loads(slots_str)


            # 检查intent

            if pred_intent_id == label:

                intent_right += 1

            else:

                if len(intent_errors) < 10:

                    intent_errors.append({

                        "text": text,

                        "true_label": label,

                        "pred_label": pred_intent_id,

                        "pred_intent": result.get("intent")

                    })


            # 检查slots

            if pred_slots == true_slots:

                slots_right += 1

            else:

                if len(slot_errors) < 10:

                    slot_errors.append({

                        "text": text[:50],

                        "true_slots": true_slots,

                        "pred_slots": pred_slots

                    })


            total += 1

        except Exception as e:

            print(f"Error on '{text[:30]}...': {e}")

            continue


    intent_acc = intent_right / total if total > 0 else 0

    slots_acc = slots_right / total if total > 0 else 0


    print(f"\nNLU Intent 准确率: {intent_right}/{total} = {intent_acc:.4f} ({intent_acc*100:.2f}%)")

    print(f"NLU Slots 准确率: {slots_right}/{total} = {slots_acc:.4f} ({slots_acc*100:.2f}%)")


    if intent_errors:

        print(f"\n前{len(intent_errors)}个Intent错误样例:")

        for i, err in enumerate(intent_errors):

            print(f"  [{i+1}] text: {err['text'][:50]}...")

            print(f"      true: {err['true_label']}, pred: {err['pred_label']} ({err['pred_intent']})")


    if slot_errors:

        print(f"\n前{len(slot_errors)}个Slots错误样例:")

        for i, err in enumerate(slot_errors):

            print(f"  [{i+1}] text: {err['text']}...")

            print(f"      true: {err['true_slots']}")

            print(f"      pred: {err['pred_slots']}")


    return intent_acc, slots_acc, intent_right, slots_right, total


if __name__ == '__main__':

    data_path = "data/single_slots_new.txt"


    print(f"加载数据并抽样 {SAMPLE_SIZE} 条 (seed={RANDOM_SEED})...")

    sampled_data = load_and_sample_data(data_path, RANDOM_SEED, SAMPLE_SIZE)

    print(f"实际抽样: {len(sampled_data)} 条")


    # 测试BERT

    bert_acc, bert_right, bert_total = test_bert_only(sampled_data)


    # 测试完整NLU

    nlu_intent_acc, nlu_slots_acc, nlu_intent_right, nlu_slots_right, nlu_total = test_full_nlu(sampled_data)


    # 汇总对比

    print("\n" + "="*60)

    print("测试结果汇总")

    print("="*60)

    print(f"BERT Intent Top1:     {bert_acc*100:.2f}%")

    print(f"NLU Intent (BERT+LLM): {nlu_intent_acc*100:.2f}%")

    print(f"NLU Slots:            {nlu_slots_acc*100:.2f}%")

    print(f"\nIntent准确率差异: {(nlu_intent_acc - bert_acc)*100:+.2f}%")
