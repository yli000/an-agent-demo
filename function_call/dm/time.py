from datetime import datetime

from zoneinfo import ZoneInfo  # 需要 Python 3.9 或以上版本。

from utils import logger


# 常见城市与时区的映射

CITY_TO_TIMEZONE = {

    # 北美洲

    "new york": "America/New_York",

    "los angeles": "America/Los_Angeles",

    "chicago": "America/Chicago",

    "toronto": "America/Toronto",

    "vancouver": "America/Vancouver",

    # 欧洲

    "london": "Europe/London",

    "paris": "Europe/Paris",

    "berlin": "Europe/Berlin",

    "rome": "Europe/Rome",

    "madrid": "Europe/Madrid",

    "moscow": "Europe/Moscow",

    # 亚洲

    "beijing": "Asia/Shanghai",

    "shanghai": "Asia/Shanghai",

    "tokyo": "Asia/Tokyo",

    "seoul": "Asia/Seoul",

    "singapore": "Asia/Singapore",

    "hong kong": "Asia/Hong_Kong",

    "dubai": "Asia/Dubai",

    "mumbai": "Asia/Kolkata",

    "bangkok": "Asia/Bangkok",

    # 大洋洲

    "sydney": "Australia/Sydney",

    "melbourne": "Australia/Melbourne",

    "auckland": "Pacific/Auckland",

    # 南美洲

    "sao paulo": "America/Sao_Paulo",

    "buenos aires": "America/Argentina/Buenos_Aires",

}


def _get_timezone(location: str, timezone: str) -> str:

    "根据显式时区或地点确定时区。"

    # 优先使用调用方显式提供的时区。

    if timezone:

        tz_upper = timezone.upper()

        # 处理常见的时区缩写。

        abbrev_map = {

            "PST": "America/Los_Angeles",

            "PDT": "America/Los_Angeles",

            "MST": "America/Denver",

            "MDT": "America/Denver",

            "CST": "America/Chicago",

            "CDT": "America/Chicago",

            "EST": "America/New_York",

            "EDT": "America/New_York",

            "GMT": "Europe/London",

            "UTC": "UTC",

            "BST": "Europe/London",

            "CET": "Europe/Paris",

            "JST": "Asia/Tokyo",

            "KST": "Asia/Seoul",

            "IST": "Asia/Kolkata",

            "AEST": "Australia/Sydney",

        }

        if tz_upper in abbrev_map:

            return abbrev_map[tz_upper]

        # 解析 UTC+8 等时区偏移格式。

        if tz_upper.startswith("UTC"):

            try:

                offset = tz_upper.replace("UTC", "").replace(" ", "")

                if offset in ["+8", "+08", "+08:00"]:

                    return "Asia/Shanghai"

                elif offset in ["-5", "-05", "-05:00"]:

                    return "America/New_York"

                # 可根据业务需要补充映射。

            except:

                pass

        # 尝试将原始输入作为 IANA 时区名称。

        return timezone


    # 根据地点匹配时区。

    if location:

        location_lower = location.lower().strip()

        if location_lower in CITY_TO_TIMEZONE:

            return CITY_TO_TIMEZONE[location_lower]


    # 未匹配到时区时使用 UTC。

    return "UTC"


async def process(func_name, query, slots):

    "处理时间查询，确定地点与时区并生成结果。"

    if func_name != "time":

        return None


    location = slots.get("location", "")

    timezone = slots.get("timezone", "")


    try:

        tz_name = _get_timezone(location, timezone)

        tz = ZoneInfo(tz_name)

        now = datetime.now(tz)


        time_str = now.strftime("%H:%M:%S")

        date_str = now.strftime("%Y-%m-%d")

        day_of_week = now.strftime("%A")


        display_location = location if location else tz_name


        tool_response = {

            "location": display_location,

            "timezone": tz_name,

            "time": time_str,

            "date": date_str,

            "day_of_week": day_of_week,

        }


        nlg = f"It is {time_str} on {day_of_week}, {date_str} in {display_location}."


        return (tool_response, nlg)


    except Exception as e:

        logger.error(f"time dm error: {e}")

        return None
