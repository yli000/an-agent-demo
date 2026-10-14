# -*- coding: utf-8 -*-

"处理 CLINC150 意图识别结果与槽位参数。"

import json


def value_process(key, value):

    "槽位值标准化入口；当前保留原值。"

    # CLINC150 的大多数槽位值已使用统一格式。

    # 保留此入口，方便扩展槽位值标准化规则。

    return value


def intent_slot(function, map_intent, slot_map):

    "从模型工具调用中读取函数名与参数，映射为意图和槽位字符串。无有效槽位时返回意图名加 none，解析失败返回 Unknown-none。"

    try:

        # 从模型返回的工具调用中读取函数名。

        predict_func = function[0].get("function", {}).get("name", "Unknown")

        # 将函数名映射为意图标签。

        predict_intent = map_intent.get(predict_func, predict_func)


        # 读取模型抽取的槽位参数。

        slots_str = function[0].get("function", {}).get("arguments", "{}")

        slots_predict = json.loads(slots_str)


        # 拼接意图与槽位的输出字符串。

        result = predict_intent + "-"

        dict_slot = slot_map.get(predict_func)


        if slots_predict and isinstance(dict_slot, dict):

            # 槽位定义以字典形式保存。

            slot_parts = []

            for key, value in slots_predict.items():

                # 只输出非空槽位值。

                if value:

                    value = value_process(key, value)

                    slot_parts.append(f"{key}:{str(value)}")


            if slot_parts:

                result += ",".join(slot_parts)

            else:

                result += "none"

        else:

            # 未抽取到槽位，或该意图没有定义槽位。

            result += "none"


    except Exception as e:

        return "Unknown-none"


    return result
