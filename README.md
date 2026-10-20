# an-agent-demo

一个能调用工具、也能聊天的 agent。示例是一个生活助手，可以查天气、查时间、放音乐；换成自己的意图和工具后，可用于车载、智能家居等场景。

![Agent 流程示意](images/workflow.svg)

## 流程

**收到用户的一句话后**（`start.py`，简化）

```python
ori_query = query                                            # 用户原话
query = request_rewrite(ori_query, last_answer, sender_id)   # 结合上文，补充缺失信息、指代信息等内容

# 以下几个流程同时开始，需求判断的结果出来后，选用对应流程的结果
arbitration = pool.submit(request_arbitration, ori_query, sender_id)  # 需求判断：要不要调用工具
nlu         = pool.submit(request_nlu, query, trace_id, enable_dm)    # 调用工具
reject      = pool.submit(request_reject, query, trace_id)            # 是否要拒绝回答
correlation = pool.submit(request_correlation, ori_query, sender_id)  # 和上一句是否相关
chat        = pool.submit(request_chat, ori_query, sender_id)         # 聊天

if arbitration.result() == "task":
    send(nlu.result())                                       # 用调用工具的结果
elif reject.result() == 1 or correlation.result() == "是":   # 不拒绝，或和上一句相关
    stream(chat.result())                                    # 用聊天的结果，边生成边输出
else:
    send_reject()                                            # 拒绝回答
```

**需要调用工具时**（`function_call/chatnlu_infer.py`，简化）

```python
top5, scores = intent_recall(query)                        # 分类模型给出最可能的几个意图，如查时间
candidates = top5[:1] if max(scores) > 0.98 else top5      # 第一名把握很大时，其余的不再考虑
tool_call = send_messages(messages, tools_of(candidates))  # 大模型从这些意图对应的工具里选一个，并填好参数
func_name, slots = parse(tool_call)                        # 如 time(location="London")

# 执行工具，再把结果说成一句话
tool_response, nlg = await DMFactory.get(func_name)(func_name, query, slots)
```

改成自己的项目时，主要改这几处：

- **意图和分类模型**：在 `config/class.txt` 列出意图类别，再用自己场景的数据重新训练意图分类和是否拒绝两个模型
- **工具**：在 `function_call/function.py` 定义工具和参数（`scripts/generate_functions.py` 可根据意图描述批量生成），在 `function_call/dm/` 写执行工具的代码。工具也可以是通过 MCP 接入的外部服务（见 `mcp_core/`）
- **提示词**：都在 `prompts.py`，如什么情况算要调用工具、聊天的风格

注意：工具在需求判断出结果前就会执行。开关设备这类有实际影响的操作，应改成等判断结果出来再执行。

## 安装与运行

需要 Redis（保存多轮对话的上下文），以及支持工具调用（function calling）的 OpenAI 兼容大模型接口。

```bash
pip install -r requirements.txt
cp config/config.example.ini config/config.ini   # 填写 API_KEY、BASE_URL、OPENWEATHER_API_KEY
# 把 client/ 和 function_call/chatnlu_infer.py 中的 YOUR_MODEL_DEPLOYMENT_ID 换成实际模型名

redis-server &
bash server.sh                                   # 启动各个服务
ENTRY_URL=http://127.0.0.1:8080 python dialog.py # 在命令行里对话
```

## 训练与评估

### 训练

训练两个分类模型，其余环节由大模型完成：

- **意图分类**：`train/train_intent.py`，示例数据为公开的英文意图数据集 CLINC150
- **是否拒绝**：`train/run.py --model bert_tiny --data reject`

### 评估

- 意图分类、是否拒绝的准确率：`test/intent_client.py`、`test/reject_client.py`
- 意图和参数（如地点、时间）的准确率：`test/nlu_client.py`
- 多轮对话的整体效果：`test.py` 跑一批对话，`e2e_score.py` 人工标注对错后计算准确率
- 各服务的并发压测：`test/*_benchmark.py`
