# from __future__ import annotations

# from datetime import datetime, timedelta, timezone
# from typing import Any

# _CACHE_TTL = timedelta(days=7)

# # cache[topic_id] = {"videos": [...], "expires_at": datetime}
# cache: dict[str, dict[str, Any]] = {}


# def get_cached_videos(topic_id: str) -> list[dict[str, Any]] | None:
#     entry = cache.get(topic_id)
#     if not entry:
#         return None

#     expires_at: datetime = entry.get("expires_at")
#     if not isinstance(expires_at, datetime):
#         cache.pop(topic_id, None)
#         return None

#     now = datetime.now(timezone.utc)
#     if expires_at <= now:
#         cache.pop(topic_id, None)
#         return None

#     videos = entry.get("videos")
#     if isinstance(videos, list):
#         return videos
#     return None


# def set_cached_videos(topic_id: str, videos: list[dict[str, Any]]) -> None:
#     cache[topic_id] = {
#         "videos": videos,
#         "expires_at": datetime.now(timezone.utc) + _CACHE_TTL,
#     }

import time

CACHE = {}
TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def get_cache(key: str):
    data = CACHE.get(key)
    if not data:
        return None

    if time.time() > data["expires_at"]:
        del CACHE[key]
        return None

    return data["value"]


def set_cache(key: str, value):
    CACHE[key] = {
        "value": value,
        "expires_at": time.time() + TTL_SECONDS,
    }
