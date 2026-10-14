# 模型配置

| 模型 | 用途 | 配置位置 |
|---|---|---|
| BERT base uncased，150 类意图分类 | 前五意图候选召回 | `train/train_intent.py`、`train/intent_infer.py` |
| BERT Tiny，基座对应 prajjwal1/bert-tiny | 拒识二分类 | `train/models/bert_tiny.py`、`train/reject_infer.py` |
| 支持工具调用的 LLM，原调用注释标为 DeepSeek V3.2 | 意图识别、槽位抽取及闲聊 | `function_call/chatnlu_infer.py`、`client/stream_chat.py` |
| OpenAI 兼容模型部署 | 查询改写、仲裁、相关性判断、自然语言生成 | `client/`、`API_KEY`、`BASE_URL` |

LLM 以实际部署为准；`YOUR_MODEL_DEPLOYMENT_ID` 需替换为自己的模型部署。权重、训练样本和个人凭据需在本地准备。

意图模型使用 `train/saved/intent/bert_base_uncased/` 与对应 `bert.ckpt`；拒识模型使用 `train/pretrained/bert_tiny_en/` 与 `train/saved/reject/bert_tiny.ckpt`。类别文件的标签顺序需与训练产物一致。
