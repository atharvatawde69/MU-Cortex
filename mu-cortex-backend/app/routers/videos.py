from fastapi import APIRouter, Query

from app.agents.scout_agent import get_videos_for_topic
from app.utils.cache import get_cached_videos, set_cached_videos

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("")
def list_videos(
    topic_id: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    cached = get_cached_videos(topic_id)
    if cached is not None:
        return cached

    # Stubbed agent call (returns empty list for now)
    videos = get_videos_for_topic(topic_id=topic_id, limit=limit)
    set_cached_videos(topic_id, videos)
    return videos

