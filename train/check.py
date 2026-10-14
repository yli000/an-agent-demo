import torch

import os

from transformers import BertModel, BertTokenizer


# 你的 ModelScope 缓存路径

model_path = "./train/pretrained/bert-base-uncased"


print(f"📂 正在尝试加载模型: {model_path}")


try:

    # 1. 加载 Tokenizer

    tokenizer = BertTokenizer.from_pretrained(model_path)

    print("✅ Tokenizer 加载成功！")


    # 测试分词

    text = "reservation"

    tokens = tokenizer.tokenize(text)

    ids = tokenizer.convert_tokens_to_ids(tokens)

    print(f"   测试分词 '{text}': {tokens} -> {ids}")


    # 验证是否是英文 Tokenizer

    if ids == [100] or ids == [10478]: # 在该 BERT 词表中，10478 对应 reservation。

        print("   (Tokenizer 看起来是正常的英文版)")

    else:

        print(f"   ⚠️ 警告：Token ID {ids} 看起来不像标准的 bert-base-uncased，请确认！")


    # 2. 加载模型权重

    model = BertModel.from_pretrained(model_path)

    print("✅ 模型架构加载成功！")


    # 3. 检查权重是否是随机初始化的（核心检查！）

    # 检查 Embedding 层的一个切片

    # 预训练过的 BERT，word_embeddings 通常在 [-0.1, 0.1] 之间，但有特定分布

    embedding_sample = model.embeddings.word_embeddings.weight[10478][:5].detach().numpy()

    print(f"   'reservation' 的 Embedding 前5位: {embedding_sample}")


    # 检查 pooler 层 (通常接近 0 或 1 附近的tanh结果，但权重本身...)

    pooler_weight_sample = model.pooler.dense.weight[0][:5].detach().numpy()

    print(f"   Pooler 层权重前5位: {pooler_weight_sample}")


    # 4. 跑一次前向传播

    print("\n🏃‍♂️ 正在尝试前向传播 (Forward Pass)...")

    inputs = tokenizer("Hello world", return_tensors="pt")

    with torch.no_grad():

        outputs = model(**inputs)


    print(f"✅ 前向传播成功！输出形状: {outputs.last_hidden_state.shape}")

    print("🎉 结论：模型文件本身看起来是完好无损的！")


except OSError as e:

    print("\n❌ 加载失败！")

    print(f"原因: 找不到文件或文件损坏。\n详细信息: {e}")

except Exception as e:

    print(f"\n❌ 发生未知错误: {e}")
