"""

测试改进后的 Rewrite prompt 效果

对比：原始 prompt vs 保留关键槽位信息的 prompt

"""

import os

import json

import requests


API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

BASE_URL = os.environ.get("BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")


# 原始 prompt

ORIGINAL_PROMPT = """# Role: Query Rewriting Expert



You only process the most recent utterance spoken by role A. Replace pronouns or vague references with the concrete entities mentioned earlier, but never change the user's intent.



## Rules

1. Output only the rewritten sentence (one line). Do NOT explain, answer, or ask questions.

2. Work on A's latest utterance; use the immediate dialogue history to resolve references.

3. Replace pronouns (he, she, it, they, this, that, there, etc.) with the actual names/objects if they appear in prior turns.

4. Choose the correct entity when words overlap (e.g., "Play X" → song name, "Go to X" → location).

5. If the sentence is already clear, or there is no relevant context, leave it unchanged.

6. Do not invent new information; only fill in what is explicitly stated.

7. "I" in A's speech refers to A; "you" refers to B. Stay in character as A and never reply as B.

"""


# 改进后的 prompt - 保留关键槽位信息

IMPROVED_PROMPT = """# Role: Query Rewriting Expert



You only process the most recent utterance spoken by role A. Your goal is to make the utterance self-contained by incorporating relevant context from the dialogue history.



## Rules

1. Output only the rewritten sentence (one line). Do NOT explain, answer, or ask questions.

2. Work on A's latest utterance; use the immediate dialogue history to resolve references.

3. Replace pronouns (he, she, it, they, this, that, there, etc.) with the actual names/objects if they appear in prior turns.

4. **Preserve key slot information from previous turns when the current utterance modifies or adds to an ongoing task.** For example, if A previously said "3 nights" and now says "Check-in is Friday", include both: "Check-in for the 3-night stay is Friday".

5. Choose the correct entity when words overlap (e.g., "Play X" → song name, "Go to X" → location).

6. If the sentence is already clear and complete, or there is no relevant context, leave it unchanged.

7. Do not invent new information; only fill in what is explicitly stated.

8. "I" in A's speech refers to A; "you" refers to B. Stay in character as A and never reply as B.

"""


# 测试用例

TEST_CASES = [

    {

        "name": "Hotel booking - nights should be preserved",

        "history": "A: Book a hotel in Paris\nB: OK, booking hotel in Paris.\nA: I need it for 3 nights\nB: Got it, 3 nights.",

        "query": "Check-in is next Friday",

        "expected_slots": ["Paris", "3 nights", "next Friday"]

    },

    {

        "name": "Hotel booking - all slots should be preserved",

        "history": "A: Book a hotel in Paris\nB: OK.\nA: I need it for 3 nights\nB: Got it.\nA: Check-in is next Friday\nB: OK, check-in Friday.",

        "query": "Make it a suite for 2 guests",

        "expected_slots": ["Paris", "3 nights", "Friday", "suite", "2 guests"]

    },

    {

        "name": "Flight booking - destination preserved",

        "history": "A: Book a flight to Tokyo\nB: OK, booking flight to Tokyo.",

        "query": "I need 2 tickets",

        "expected_slots": ["Tokyo", "2 tickets"]

    },

    {

        "name": "Car rental - location and date preserved",

        "history": "A: Book a rental car in LA\nB: OK.\nA: Pick it up next Monday\nB: Got it, Monday pickup.",

        "query": "I need an SUV",

        "expected_slots": ["LA", "Monday", "SUV"]

    },

]


def call_rewrite(system_prompt, history, query):

    """调用 LLM 进行改写"""

    headers = {

        "Authorization": API_KEY,

        "Content-Type": "application/json"

    }


    prompt = f"#对话历史#\n{history}\nA：{query}\n"


    data = {

        "model": "YOUR_MODEL_DEPLOYMENT_ID",

        "messages": [

            {"role": "system", "content": system_prompt},

            {"role": "user", "content": prompt}

        ],

        "temperature": 0.001,

        "top_p": 0,

    }


    response = requests.post(BASE_URL, headers=headers, json=data, timeout=10)

    result = response.json()

    return result['choices'][0]['message']['content']


def check_slots(rewritten, expected_slots):

    """检查改写结果是否包含期望的槽位"""

    rewritten_lower = rewritten.lower()

    found = []

    missing = []

    for slot in expected_slots:

        if slot.lower() in rewritten_lower:

            found.append(slot)

        else:

            missing.append(slot)

    return found, missing


def main():

    print("=" * 70)

    print("Rewrite Prompt 对比测试")

    print("=" * 70)


    for case in TEST_CASES:

        print(f"\n【{case['name']}】")

        print(f"历史: {case['history'][:50]}...")

        print(f"当前: {case['query']}")

        print(f"期望槽位: {case['expected_slots']}")

        print("-" * 50)


        # 原始 prompt

        original_result = call_rewrite(ORIGINAL_PROMPT, case['history'], case['query'])

        orig_found, orig_missing = check_slots(original_result, case['expected_slots'])


        # 改进 prompt

        improved_result = call_rewrite(IMPROVED_PROMPT, case['history'], case['query'])

        imp_found, imp_missing = check_slots(improved_result, case['expected_slots'])


        print(f"原始 prompt: {original_result}")

        print(f"  ✓ 包含: {orig_found}")

        print(f"  ✗ 缺失: {orig_missing}")

        print()

        print(f"改进 prompt: {improved_result}")

        print(f"  ✓ 包含: {imp_found}")

        print(f"  ✗ 缺失: {imp_missing}")


        # 对比

        if len(imp_missing) < len(orig_missing):

            print("  >>> 改进版更好！")

        elif len(imp_missing) == len(orig_missing):

            print("  >>> 效果相同")

        else:

            print("  >>> 原始版更好")


        print()


if __name__ == "__main__":

    main()
