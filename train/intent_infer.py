import os

import json

import time

import torch

import torch.nn.functional as F

import uvicorn

import numpy as np

from fastapi import FastAPI, Request

from transformers import BertTokenizerFast, BertForSequenceClassification


from utils import logger


app = FastAPI()


DATA_DIR = "./data/intent"

MODEL_DIR = "./saved/intent/bert_base_uncased"      # 使用 Hugging Face 格式保存模型与分词器。

CKPT_PATH = "./saved/intent/bert.ckpt"              # 意图分类检查点，当前加载逻辑需要此文件。

TOPK = 5

PAD, CLS = '[PAD]', '[CLS]'

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# 读取 class.txt 获取标签映射

class_file = os.path.join(DATA_DIR, "class.txt")

with open(class_file, "r", encoding="utf-8") as f:

    class_list = [line.strip() for line in f if line.strip()]


tokenizer = BertTokenizerFast.from_pretrained(MODEL_DIR)

model = BertForSequenceClassification.from_pretrained(MODEL_DIR)

state = torch.load(CKPT_PATH, map_location=DEVICE)

model.load_state_dict(state, strict=False)

model.to(DEVICE)

model.eval()


def predict(query: str):

    encoded = tokenizer(

        query,

        add_special_tokens=True,

        max_length=64,

        padding="max_length",

        truncation=True,

        return_tensors="pt",

    )

    input_ids = encoded["input_ids"].to(DEVICE)

    attention_mask = encoded["attention_mask"].to(DEVICE)


    with torch.no_grad():

        logits = model(input_ids=input_ids, attention_mask=attention_mask).logits

        probs = F.softmax(logits, dim=-1).cpu().numpy()[0]

        top_indices = np.argsort(-probs)[:TOPK]

    return top_indices, probs[top_indices]


@app.post("/intent-server/v1")

async def inference(request: Request):

    data = await request.json()

    query = data.get("query", "")

    trace_id = data.get("trace_id", "unknown")


    try:

        top_labels, top_scores = predict(query)

    except Exception:

        top_labels = [len(class_list)] * TOPK

        top_scores = [1.0] * TOPK


    result = {

        "data": ",".join(str(int(idx)) for idx in top_labels),

        "score": ",".join(f"{float(s):.6f}" for s in top_scores),

    }

    logger.info(f"TraceID:{trace_id}, query:{query}, result:{result['data']}, score:{result['score']}")

    return result


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8008, workers=1)
