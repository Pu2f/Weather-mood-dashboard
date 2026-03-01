from __future__ import annotations

import math
from datetime import timedelta

from services.journal import JournalRow


def align_by_date(
    journal: list[JournalRow],
    weather: dict[str, dict],
    start,
    end,
) -> list[dict]:
    journal_map = {r.date: r for r in journal}

    # use date range as backbone, so rows still render even if weather API fails
    total_days = (end - start).days
    if total_days < 0:
        start, end = end, start
        total_days = (end - start).days

    dates = [(start + timedelta(days=i)).isoformat() for i in range(total_days + 1)]
    rows: list[dict] = []
    for d in dates:
        w = weather.get(d, {})
        j = journal_map.get(d)
        rows.append(
            {
                "date": d,
                "temp_mean": w.get("temp_mean"),
                "temp_max": w.get("temp_max"),
                "rain_mm": w.get("rain_mm"),
                "mood": j.mood if j else None,
                "productivity": j.productivity if j else None,
            }
        )
    return rows


def _paired_xy(
    xs: list[float | None], ys: list[float | None]
) -> list[tuple[float, float]]:
    pairs = []
    for x, y in zip(xs, ys):
        if x is None or y is None:
            continue
        pairs.append((float(x), float(y)))
    return pairs


def compute_correlation(xs: list[float | None], ys: list[float | None]) -> float | None:
    pairs = _paired_xy(xs, ys)
    n = len(pairs)
    if n < 3:
        return None

    xvals = [p[0] for p in pairs]
    yvals = [p[1] for p in pairs]

    mx = sum(xvals) / n
    my = sum(yvals) / n
    num = sum((x - mx) * (y - my) for x, y in pairs)
    denx = math.sqrt(sum((x - mx) ** 2 for x in xvals))
    deny = math.sqrt(sum((y - my) ** 2 for y in yvals))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def linear_regression(xs: list[float | None], ys: list[float | None]) -> dict | None:
    pairs = _paired_xy(xs, ys)
    n = len(pairs)
    if n < 3:
        return None

    xvals = [p[0] for p in pairs]
    yvals = [p[1] for p in pairs]
    mx = sum(xvals) / n
    my = sum(yvals) / n

    sxx = sum((x - mx) ** 2 for x in xvals)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in pairs)

    b = sxy / sxx
    a = my - b * mx
    return {"a": a, "b": b, "n": n}


def group_productivity_by_rain(
    rain_mm: list[float | None],
    productivity: list[float | None],
    threshold: float,
) -> dict:
    rainy = []
    dry = []
    for r, p in zip(rain_mm, productivity):
        if r is None or p is None:
            continue
        if float(r) >= threshold:
            rainy.append(float(p))
        else:
            dry.append(float(p))

    def avg(v: list[float]) -> float | None:
        return (sum(v) / len(v)) if v else None

    return {
        "rainy_avg": avg(rainy),
        "dry_avg": avg(dry),
        "rainy_n": len(rainy),
        "dry_n": len(dry),
    }
