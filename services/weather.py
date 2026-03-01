from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests


def _daterange_key(lat: float, lon: float, start: date, end: date) -> str:
    return f"{lat:.4f},{lon:.4f}:{start.isoformat()}..{end.isoformat()}"


def get_daily_weather(
    lat: float,
    lon: float,
    start: date,
    end: date,
    cache_path: str,
) -> dict[str, dict]:
    """
    Returns:
      { "YYYY-MM-DD": { "temp_mean": float, "temp_max": float, "rain_mm": float } }
    """
    cache_file = Path(cache_path)
    cache: dict = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}

    key = _daterange_key(lat, lon, start, end)
    if key in cache:
        return cache[key]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_mean,temperature_2m_max,precipitation_sum",
        "timezone": "Asia/Bangkok",
    }

    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    payload = resp.json()

    daily = payload.get("daily", {})
    times = daily.get("time", [])
    t_mean = daily.get("temperature_2m_mean", [])
    t_max = daily.get("temperature_2m_max", [])
    rain = daily.get("precipitation_sum", [])

    out: dict[str, dict] = {}
    for i, d in enumerate(times):
        out[d] = {
            "temp_mean": t_mean[i] if i < len(t_mean) else None,
            "temp_max": t_max[i] if i < len(t_max) else None,
            "rain_mm": rain[i] if i < len(rain) else None,
        }

    cache[key] = out
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return out