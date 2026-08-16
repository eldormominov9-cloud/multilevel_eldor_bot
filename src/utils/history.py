"""Chiqarilgan mavzular tarixi — takror postlarning oldini oladi."""
import json
import os
from datetime import datetime, timezone, timedelta

from src import config

HISTORY_PATH = os.path.join("state", "history.json")
TASHKENT = timezone(timedelta(hours=5))


def load() -> list:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def recent_topics(history: list, limit: int = config.HISTORY_LOOKBACK) -> list:
    """Oxirgi mavzular ro'yxati — researcher agentiga beriladi."""
    return [h.get("topic", "") for h in history[-limit:] if h.get("topic")]


def next_category(history: list) -> str:
    """Rotatsiya bo'yicha navbatdagi kategoriya."""
    idx = len(history) % len(config.CATEGORY_ROTATION)
    return config.CATEGORY_ROTATION[idx]


def append(history: list, entry: dict) -> None:
    entry["published_at"] = datetime.now(TASHKENT).isoformat(timespec="seconds")
    history.append(entry)
    trimmed = history[-config.HISTORY_MAX:]
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)
