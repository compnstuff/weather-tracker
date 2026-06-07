import httpx
import os
from datetime import datetime, timezone

BASE_URL = "https://api.openweathermap.org/data/2.5"


def _api_key() -> str:
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key:
        raise ValueError("OPENWEATHER_API_KEY is not set in .env")
    return key


async def fetch_current(city: str) -> dict:
    params = {"q": city, "appid": _api_key(), "units": "metric"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/weather", params=params, timeout=10)
        r.raise_for_status()
        return r.json()


async def fetch_forecast(city: str) -> dict:
    params = {"q": city, "appid": _api_key(), "units": "metric", "cnt": 40}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/forecast", params=params, timeout=10)
        r.raise_for_status()
        return r.json()


def parse_current(data: dict) -> dict:
    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "wind_deg": data["wind"].get("deg", 0),
        "description": data["weather"][0]["description"].capitalize(),
        "icon": data["weather"][0]["icon"],
        "visibility": data.get("visibility"),
        "clouds": data["clouds"]["all"],
    }


def parse_forecast(data: dict) -> list[dict]:
    entries = []
    for item in data["list"]:
        entries.append({
            "dt": datetime.fromtimestamp(item["dt"], tz=timezone.utc).isoformat(),
            "temp_c": item["main"]["temp"],
            "feels_like_c": item["main"]["feels_like"],
            "humidity": item["main"]["humidity"],
            "wind_speed": item["wind"]["speed"],
            "description": item["weather"][0]["description"].capitalize(),
            "icon": item["weather"][0]["icon"],
            "pop": round(item.get("pop", 0) * 100),
        })
    return entries
