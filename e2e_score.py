"""计算任务型对话agent端到端准确率得分



输出两个文件:

1. multi_test_output_for_labeling.txt - 简化格式供人工标注

2. multi_test_output_detailed.json - 详细JSON格式供错误分析

"""


import json

import os

from datetime import datetime


INPUT_FILE = "test/result/multi_test_output.txt"

LABELING_FILE = "test/result/multi_test_output_for_labeling.txt"

DETAILED_FILE = "test/result/multi_test_output_detailed.json"


def process_results():

    """处理E2E测试结果，生成标注文件和详细分析文件"""


    if not os.path.exists(INPUT_FILE):

        print(f"Error: {INPUT_FILE} not found. Run test.py first.")

        return


    detailed_results = []

    labeling_lines = []


    with open(INPUT_FILE, 'r', encoding='utf-8') as fd:

        for line_num, line in enumerate(fd, 1):

            try:

                info = json.loads(line)

            except json.JSONDecodeError:

                print(f"Warning: Line {line_num} is not valid JSON, skipping")

                continue


            query = info.get("query", "")

            res_list = info.get("res", [])


            # 构建详细结果

            detail = {

                "line_num": line_num,

                "query": query,

                "results": []

            }


            # 构建标注行

            res_summary = ""


            for msg in res_list:

                intent = msg.get("intent", "Unknown")

                slots = msg.get("slots", {})

                cost = msg.get("cost", 0)


                result_item = {

                    "intent": intent,

                    "intent_id": msg.get("intent_id"),

                    "function": msg.get("function"),

                    "slots": slots,

                    "cost": round(cost, 3)

                }


                # 处理闲聊百科的特殊字段

                if intent == "闲聊百科" or msg.get("func") == "CHAT":

                    frame = msg.get("frame", "")

                    status = msg.get("status")

                    if status == 2:  # 完成状态

                        result_item["response"] = frame

                    res_summary += frame.replace("\n", " ")

                else:

                    res_summary = f"{intent}\t{json.dumps(slots, ensure_ascii=False)}"

                    result_item["response"] = None


                # 只保存最终结果（非流式中间状态）

                if msg.get("status") != 1:  # 非流式中间状态

                    detail["results"].append(result_item)


            detailed_results.append(detail)


            # 标注格式: [空白供标注]\tquery\t结果摘要

            labeling_lines.append(f"\t{query}\t{res_summary}")


    # 保存详细JSON结果

    output_data = {

        "generated_at": datetime.now().isoformat(),

        "total_queries": len(detailed_results),

        "results": detailed_results

    }


    with open(DETAILED_FILE, 'w', encoding='utf-8') as f:

        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Detailed results saved to: {DETAILED_FILE}")


    # 保存标注文件

    with open(LABELING_FILE, 'w', encoding='utf-8') as f:

        f.write("# E2E Test Results for Labeling\n")

        f.write("# Format: [1/0 for correct/wrong]\\tquery\\tresult\n")

        f.write("# " + "="*60 + "\n")

        for line in labeling_lines:

            f.write(line + "\n")

    print(f"Labeling file saved to: {LABELING_FILE}")


    # 打印简单统计

    print(f"\nTotal queries processed: {len(detailed_results)}")


    # 打印到控制台（兼容原有行为）

    print("\n" + "="*60)

    print("Results Preview (query ############ result):")

    print("="*60)

    for detail in detailed_results[:10]:  # 只显示前10条

        query = detail["query"]

        if detail["results"]:

            last_result = detail["results"][-1]

            if last_result.get("response"):

                res = last_result["response"]

            else:

                res = f"{last_result['intent']}\t{json.dumps(last_result['slots'], ensure_ascii=False)}"

        else:

            res = "No result"

        print(f"{query}############{res}")


    if len(detailed_results) > 10:

        print(f"... and {len(detailed_results) - 10} more")


def calculate_score():

    """计算标注后的准确率"""

    labeled_file = "test/result/multi_test_output_labeled.txt"


    if not os.path.exists(labeled_file):

        print(f"Labeled file not found: {labeled_file}")

        print("Please label the results first (add 1 or 0 at the beginning of each line)")

        return


    right, total = 0, 0

    with open(labeled_file, 'r', encoding='utf-8') as f:

        for line in f:

            line = line.strip()

            if not line or line.startswith("#"):

                continue

            if line.startswith("1"):

                right += 1

                total += 1

            elif line.startswith("0"):

                total += 1


    if total > 0:

        accuracy = round(right / total * 100, 2)

        print("\n" + "="*50)

        print(f"E2E Accuracy: {accuracy}% ({right}/{total})")

        print("="*50)

    else:

        print("No labeled results found")


if __name__ == "__main__":

    import sys


    if len(sys.argv) > 1 and sys.argv[1] == "--score":

        calculate_score()

    else:

        process_results()
