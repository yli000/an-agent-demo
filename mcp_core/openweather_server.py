import os

from typing import Any, Dict, Optional, Tuple

from datetime import datetime, timedelta

import requests

from mcp.server.fastmcp import FastMCP


OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]

mcp = FastMCP("openweather")


def _geocode(city: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:

    """

    Convert city name (any language) to coordinates using OpenWeather Geocoding API.



    Args:

        city: City name in any language (e.g., "London", "北京", "纽约", "東京")



    Returns:

        Tuple of (lat, lon, resolved_city_name) or (None, None, None) if not found

    """

    try:

        response = requests.get(

            "http://api.openweathermap.org/geo/1.0/direct",

            params={

                "q": city,

                "appid": OPENWEATHER_API_KEY,

                "limit": 1

            },

            timeout=10

        )

        response.raise_for_status()

        data = response.json()


        if data and len(data) > 0:

            return (

                data[0].get("lat"),

                data[0].get("lon"),

                data[0].get("name")

            )

        return None, None, None

    except requests.exceptions.RequestException:

        return None, None, None


def _parse_date(date_str: str) -> str:

    "解析目标日期，支持当天、次日及明确日期。"

    today = datetime.now().date()

    date_lower = date_str.lower().strip() if date_str else ""


    if not date_lower or date_lower in ["today", "now", ""]:

        return today.strftime("%Y-%m-%d")

    elif date_lower in ["tomorrow", "next day"]:

        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    elif date_lower in ["day after tomorrow", "in 2 days"]:

        return (today + timedelta(days=2)).strftime("%Y-%m-%d")

    else:

        # 尝试按 YYYY-MM-DD 格式解析日期。

        try:

            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()

            return parsed.strftime("%Y-%m-%d")

        except ValueError:

            # 日期解析失败时使用当天日期。

            return today.strftime("%Y-%m-%d")


def _find_forecast_for_date(forecasts: list, target_date: str) -> Optional[Dict]:

    "查找目标日期的天气记录，优先选择中午预报。"

    target_forecasts = []


    for item in forecasts:

        dt_txt = item.get("dt_txt", "")

        if dt_txt.startswith(target_date):

            target_forecasts.append(item)


    if not target_forecasts:

        return None


    # 优先选择最接近中午 12 点的预报。

    for item in target_forecasts:

        if "12:00:00" in item.get("dt_txt", ""):

            return item


    # 没有中午预报时，使用当天的第一条记录。

    return target_forecasts[0]


@mcp.tool()

def weather_current(city: str, units: str = "metric") -> Dict[str, Any]:

    """

    Get current weather for a city. Supports city names in any language.



    Args:

        city: City name in any language (e.g., "London", "北京", "纽约", "東京")

        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit)



    Returns:

        Current weather information including temperature, description, humidity, wind.

    """

    try:

        # 将城市名称转换为经纬度。

        lat, lon, resolved_name = _geocode(city)

        if lat is None:

            return {"error": f"City not found: {city}"}


        # 根据经纬度查询天气。

        response = requests.get(

            "https://api.openweathermap.org/data/2.5/weather",

            params={

                "lat": lat,

                "lon": lon,

                "appid": OPENWEATHER_API_KEY,

                "units": units

            },

            timeout=10

        )

        response.raise_for_status()

        data = response.json()


        if data.get("cod") != 200:

            return {"error": f"API error: {data.get('message', 'Unknown error')}"}


        unit_symbol = "°C" if units == "metric" else "°F"


        return {

            "city": resolved_name or data.get("name"),

            "country": data.get("sys", {}).get("country"),

            "date": datetime.now().strftime("%Y-%m-%d"),

            "weather": data.get("weather", [{}])[0].get("description", ""),

            "temperature": f"{data.get('main', {}).get('temp')}{unit_symbol}",

            "feels_like": f"{data.get('main', {}).get('feels_like')}{unit_symbol}",

            "humidity": f"{data.get('main', {}).get('humidity')}%",

            "wind_speed": f"{data.get('wind', {}).get('speed')} m/s",

        }

    except requests.exceptions.RequestException as e:

        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()

def weather_forecast(city: str, date: str = "", units: str = "metric") -> Dict[str, Any]:

    """

    Get weather forecast for a city on a specific date (up to 5 days ahead).

    Supports city names in any language.



    Args:

        city: City name in any language (e.g., "London", "北京", "纽约")

        date: Target date - "today", "tomorrow", "day after tomorrow", or "YYYY-MM-DD"

        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit)



    Returns:

        Weather forecast for the specified date.

    """

    try:

        # 将城市名称转换为经纬度。

        lat, lon, resolved_name = _geocode(city)

        if lat is None:

            return {"error": f"City not found: {city}"}


        # 解析目标日期。

        target_date = _parse_date(date)

        today = datetime.now().date()

        target = datetime.strptime(target_date, "%Y-%m-%d").date()


        # 检查日期是否在五天预报范围内。

        days_diff = (target - today).days

        if days_diff < 0:

            return {"error": "Cannot get forecast for past dates"}

        if days_diff > 5:

            return {"error": "Forecast only available for up to 5 days ahead"}


        # 查询当天时使用实时天气。

        if days_diff == 0:

            return weather_current(city, units)


        # 根据经纬度获取五天预报。

        response = requests.get(

            "https://api.openweathermap.org/data/2.5/forecast",

            params={

                "lat": lat,

                "lon": lon,

                "appid": OPENWEATHER_API_KEY,

                "units": units

            },

            timeout=10

        )

        response.raise_for_status()

        data = response.json()


        if str(data.get("cod")) != "200":

            return {"error": f"API error: {data.get('message', 'Unknown error')}"}


        # 查找目标日期的预报。

        forecast = _find_forecast_for_date(data.get("list", []), target_date)


        if not forecast:

            return {"error": f"No forecast data available for {target_date}"}


        unit_symbol = "°C" if units == "metric" else "°F"


        return {

            "city": resolved_name or data.get("city", {}).get("name"),

            "country": data.get("city", {}).get("country"),

            "date": target_date,

            "weather": forecast.get("weather", [{}])[0].get("description", ""),

            "temperature": f"{forecast.get('main', {}).get('temp')}{unit_symbol}",

            "feels_like": f"{forecast.get('main', {}).get('feels_like')}{unit_symbol}",

            "temp_min": f"{forecast.get('main', {}).get('temp_min')}{unit_symbol}",

            "temp_max": f"{forecast.get('main', {}).get('temp_max')}{unit_symbol}",

            "humidity": f"{forecast.get('main', {}).get('humidity')}%",

            "wind_speed": f"{forecast.get('wind', {}).get('speed')} m/s",

        }

    except requests.exceptions.RequestException as e:

        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()

def weather_5day(city: str, units: str = "metric") -> Dict[str, Any]:

    """

    Get 5-day weather forecast summary for a city.

    Supports city names in any language.



    Args:

        city: City name in any language (e.g., "London", "北京", "纽约")

        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit)



    Returns:

        5-day forecast with daily summaries.

    """

    try:

        # 将城市名称转换为经纬度。

        lat, lon, resolved_name = _geocode(city)

        if lat is None:

            return {"error": f"City not found: {city}"}


        response = requests.get(

            "https://api.openweathermap.org/data/2.5/forecast",

            params={

                "lat": lat,

                "lon": lon,

                "appid": OPENWEATHER_API_KEY,

                "units": units

            },

            timeout=10

        )

        response.raise_for_status()

        data = response.json()


        if str(data.get("cod")) != "200":

            return {"error": f"API error: {data.get('message', 'Unknown error')}"}


        # 按日期分组，每天选择一条预报，优先使用中午的数据。

        daily_forecasts = {}

        for item in data.get("list", []):

            date = item.get("dt_txt", "").split(" ")[0]

            if date not in daily_forecasts:

                daily_forecasts[date] = item

            elif "12:00:00" in item.get("dt_txt", ""):

                daily_forecasts[date] = item


        unit_symbol = "°C" if units == "metric" else "°F"


        forecasts = []

        for date, forecast in sorted(daily_forecasts.items()):

            forecasts.append({

                "date": date,

                "weather": forecast.get("weather", [{}])[0].get("description", ""),

                "temperature": f"{forecast.get('main', {}).get('temp')}{unit_symbol}",

                "humidity": f"{forecast.get('main', {}).get('humidity')}%",

            })


        return {

            "city": resolved_name or data.get("city", {}).get("name"),

            "country": data.get("city", {}).get("country"),

            "forecasts": forecasts

        }

    except requests.exceptions.RequestException as e:

        return {"error": f"Request failed: {str(e)}"}


if __name__ == "__main__":

    mcp.run(transport='stdio')
