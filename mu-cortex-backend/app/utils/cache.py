from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

_CACHE_TTL = timedelta(days=7)

# cache[topic_id] = {"videos": [...], "expires_at": datetime}
cache: dict[str, dict[str, Any]] = {}


def get_cached_videos(topic_id: str) -> list[dict[str, Any]] | None:
    entry = cache.get(topic_id)
    if not entry:
        return None

    expires_at: datetime = entry.get("expires_at")
    if not isinstance(expires_at, datetime):
        cache.pop(topic_id, None)
        return None

    now = datetime.now(timezone.utc)
    if expires_at <= now:
        cache.pop(topic_id, None)
        return None

    videos = entry.get("videos")
    if isinstance(videos, list):
        return videos
    return None


def set_cached_videos(topic_id: str, videos: list[dict[str, Any]]) -> None:
    cache[topic_id] = {
        "videos": videos,
        "expires_at": datetime.now(timezone.utc) + _CACHE_TTL,
    }

