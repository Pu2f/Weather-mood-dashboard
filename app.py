from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from services.journal import load_journal, upsert_journal_row
from services.weather import get_daily_weather
from services.stats import (
    align_by_date,
    compute_correlation,
    linear_regression,
    group_productivity_by_rain,
)

APP_TITLE = "Weather vs Mood/Productivity — Hat Yai Lab"
HAT_YAI_LAT = 7.01
HAT_YAI_LON = 100.47
RAIN_THRESHOLD_MIN = 0.0
RAIN_THRESHOLD_MAX = 200.0
RAIN_THRESHOLD_DEFAULT = 1.0

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

logger = logging.getLogger(__name__)


def _parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


@app.get("/")
def index():
    today = date.today()
    default_start = today - timedelta(days=30)

    start = _parse_date(request.args.get("start"), default_start)
    end = _parse_date(request.args.get("end"), today)
    if end < start:
        start, end = end, start

    xvar = request.args.get("xvar", "temp_mean")  # temp_mean | temp_max | rain_mm
    rain_threshold = _parse_float(
        request.args.get("rain_threshold"),
        RAIN_THRESHOLD_DEFAULT,
    )
    rain_threshold = _clamp_float(
        rain_threshold,
        RAIN_THRESHOLD_MIN,
        RAIN_THRESHOLD_MAX,
    )

    journal = load_journal("data/journal.csv")
    try:
        weather = get_daily_weather(
            lat=HAT_YAI_LAT,
            lon=HAT_YAI_LON,
            start=start,
            end=end,
            cache_path="data/weather_cache.json",
        )
    except Exception as exc:
        logger.warning(
            "Weather fetch failed, falling back to journal-only view: %s", exc
        )
        weather = {}

    rows = align_by_date(journal, weather, start, end)

    labels = [r["date"] for r in rows]
    temp_mean = [r.get("temp_mean") for r in rows]
    temp_max = [r.get("temp_max") for r in rows]
    rain_mm = [r.get("rain_mm") for r in rows]
    productivity = [r.get("productivity") for r in rows]
    mood = [r.get("mood") for r in rows]

    x_series_map = {"temp_mean": temp_mean, "temp_max": temp_max, "rain_mm": rain_mm}
    x_series = x_series_map.get(xvar, temp_mean)

    corr = compute_correlation(x_series, productivity)
    reg = linear_regression(x_series, productivity)
    rain_groups = group_productivity_by_rain(rain_mm, productivity, rain_threshold)

    context = {
        "title": APP_TITLE,
        "filters": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "xvar": xvar,
            "rain_threshold": rain_threshold,
        },
        "series": {
            "labels": labels,
            "temp_mean": temp_mean,
            "temp_max": temp_max,
            "rain_mm": rain_mm,
            "productivity": productivity,
            "mood": mood,
        },
        "stats": {"corr": corr, "regression": reg, "rain_groups": rain_groups},
        "meta": {"lat": HAT_YAI_LAT, "lon": HAT_YAI_LON},
    }
    return render_template("index.html", **context)


@app.get("/log")
def log_get():
    # ค่าเริ่มต้น: วันนี้
    today = date.today().isoformat()
    return render_template("log.html", title=APP_TITLE, today=today)


@app.post("/log")
def log_post():
    day = request.form.get("date", "").strip()
    mood = request.form.get("mood", "").strip()
    productivity = request.form.get("productivity", "").strip()

    try:
        datetime.strptime(day, "%Y-%m-%d")
        mood_v = int(mood)
        prod_v = int(productivity)
        if not (1 <= mood_v <= 5 and 1 <= prod_v <= 5):
            raise ValueError("out of range")
    except Exception:
        flash("กรอกข้อมูลไม่ถูกต้อง: date ต้องเป็น YYYY-MM-DD และคะแนนต้องอยู่ 1–5", "error")
        return redirect(url_for("log_get"))

    upsert_journal_row(
        path="data/journal.csv",
        date_str=day,
        mood=mood_v,
        productivity=prod_v,
    )
    flash("บันทึกแล้ว ✅", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
