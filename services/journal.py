from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class JournalRow:
    date: str  # YYYY-MM-DD
    mood: float | None
    productivity: float | None


def _to_float(v: str) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_journal(path: str) -> list[JournalRow]:
    rows: list[JournalRow] = []
    p = Path(path)
    if not p.exists():
        return rows

    with open(p, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            d = (r.get("date") or "").strip()
            if not d:
                continue
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                continue

            rows.append(
                JournalRow(
                    date=d,
                    mood=_to_float(r.get("mood", "")),
                    productivity=_to_float(r.get("productivity", "")),
                )
            )
    return rows


def upsert_journal_row(path: str, date_str: str, mood: int, productivity: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # โหลดของเดิม
    existing = load_journal(path)
    by_date = {r.date: r for r in existing}

    by_date[date_str] = JournalRow(date=date_str, mood=float(mood), productivity=float(productivity))

    # เขียนกลับแบบเรียงวัน
    rows_sorted = [by_date[d] for d in sorted(by_date.keys())]

    with open(p, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "mood", "productivity"])
        writer.writeheader()
        for r in rows_sorted:
            writer.writerow(
                {
                    "date": r.date,
                    "mood": "" if r.mood is None else int(r.mood),
                    "productivity": "" if r.productivity is None else int(r.productivity),
                }
            )