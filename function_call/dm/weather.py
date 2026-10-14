import json

from datetime import datetime

from client.nlg import request_nlg

from mcp_core.mcp_client import MCPClient


mcp_client = MCPClient()


def _parse_datetime_to_date(datetime_str: str) -> str:

    "将相对日期、常见英文表述或日期字符串转换为 YYYY-MM-DD。"

    if not datetime_str:

        return "today"


    dt_lower = datetime_str.lower().strip()


    # 直接转换常见的日期表述。

    if dt_lower in ["today", "now", "current"]:

        return "today"

    elif dt_lower in ["tomorrow", "next day"]:

        return "tomorrow"

    elif dt_lower in ["day after tomorrow", "in 2 days", "in two days"]:

        return "day after tomorrow"


    # 尝试按 YYYY-MM-DD 格式解析日期。

    try:

        datetime.strptime(datetime_str, "%Y-%m-%d")

        return datetime_str  # 日期已使用目标格式。

    except ValueError:

        pass


    # 无法转换时保留原值，由天气工具继续处理。

    return datetime_str


async def process(func_name, query, slots):

    "处理天气查询，解析地点、日期和单位后调用天气工具。"

    # 检查请求的函数名。

    if func_name not in ["weather"]:

        return None


    # 提取并处理槽位参数。

    location = slots.get("location", "").strip()

    datetime_str = slots.get("datetime", "")

    unit = slots.get("unit", "").lower()


    # 未提供地点时使用默认地点。

    if not location:

        location = "New York"  # 英语场景下的默认值。


    # 解析日期与时间。

    date_param = _parse_datetime_to_date(datetime_str)


    # 确定单位，默认使用公制与摄氏度。

    units = "metric"

    if unit in ["f", "fahrenheit", "imperial"]:

        units = "imperial"


    # 连接天气 MCP 服务。

    await mcp_client.connect_to_server("../mcp_core/openweather_server.py")


    # 调用天气工具，支持当天及未来日期。

    mcp_slots = {

        "city": location,

        "date": date_param,

        "units": units

    }


    tool_response = await mcp_client.execute("weather_forecast", mcp_slots)

    tool_response = json.loads(tool_response)


    # 将工具结果转成自然语言回答。

    nlg = request_nlg(query, tool_response)


    return (tool_response, nlg)
