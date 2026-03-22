from langchain_core.tools import tool
import requests
import os

AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

@tool
def amap_geocode(address: str) -> str:
    """地理编码：将地址转换为经纬度坐标

    Args:
        address: 地址，如"北京市朝阳区阜通东大街6号"
    """
    if not AMAP_API_KEY:
        return "Error: AMAP_API_KEY not set"

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {"key": AMAP_API_KEY, "address": address}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data["status"] == "1" and data["geocodes"]:
            loc = data["geocodes"][0]
            return f"地址: {loc['formatted_address']}\n经纬度: {loc['location']}\n层级: {loc['level']}"
        return f"Error: {data.get('info', 'Unknown error')}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def amap_regeo(location: str) -> str:
    """逆地理编码：将经纬度转换为地址

    Args:
        location: 经纬度，格式"经度,纬度"，如"116.481488,39.990464"
    """
    if not AMAP_API_KEY:
        return "Error: AMAP_API_KEY not set"

    url = "https://restapi.amap.com/v3/geocode/regeo"
    params = {"key": AMAP_API_KEY, "location": location}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data["status"] == "1":
            addr = data["regeocode"]["formatted_address"]
            return f"地址: {addr}"
        return f"Error: {data.get('info', 'Unknown error')}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def amap_weather(city: str) -> str:
    """查询天气信息

    Args:
        city: 城市名称或城市编码，如"北京"或"110000"
    """
    if not AMAP_API_KEY:
        return "Error: AMAP_API_KEY not set"

    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {"key": AMAP_API_KEY, "city": city}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data["status"] == "1" and data["lives"]:
            w = data["lives"][0]
            return f"城市: {w['city']}\n天气: {w['weather']}\n温度: {w['temperature']}℃\n风向: {w['winddirection']}\n风力: {w['windpower']}级\n湿度: {w['humidity']}%\n更新时间: {w['reporttime']}"
        return f"Error: {data.get('info', 'Unknown error')}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def amap_poi_search(keywords: str, city: str = "") -> str:
    """POI搜索：搜索地点

    Args:
        keywords: 搜索关键词，如"餐厅"、"加油站"
        city: 城市名称，如"北京"（可选）
    """
    if not AMAP_API_KEY:
        return "Error: AMAP_API_KEY not set"

    url = "https://restapi.amap.com/v3/place/text"
    params = {"key": AMAP_API_KEY, "keywords": keywords, "city": city}

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data["status"] == "1" and data["pois"]:
            results = []
            for poi in data["pois"][:5]:
                results.append(f"名称: {poi['name']}\n地址: {poi.get('address', 'N/A')}\n位置: {poi['location']}\n类型: {poi['type']}")
            return "\n\n".join(results)
        return f"Error: {data.get('info', 'No results')}"
    except Exception as e:
        return f"Error: {str(e)}"
