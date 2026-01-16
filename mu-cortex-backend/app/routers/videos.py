# from fastapi import APIRouter, Query

# from app.agents.scout_agent import get_videos_for_topic
# from app.utils.cache import get_cached_videos, set_cached_videos

# router = APIRouter(prefix="/videos", tags=["videos"])


# @router.get("")
# def list_videos(
#     topic_id: str = Query(..., min_length=1),
#     limit: int = Query(10, ge=1, le=100),
# ):
#     cached = get_cached_videos(topic_id)
#     if cached is not None:
#         return cached

#     # Stubbed agent call (returns empty list for now)
#     videos = get_videos_for_topic(topic_id=topic_id, limit=limit)
#     set_cached_videos(topic_id, videos)
#     return videos

from fastapi import APIRouter
from app.agents.scout_agent import fetch_videos_from_channel, fetch_videos_from_global_search
from app.models.database import supabase
from app.utils.cache import get_cache, set_cache

router = APIRouter(prefix="/videos", tags=["videos"])


def extract_video_id(youtube_url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Format: https://www.youtube.com/watch?v={vid}
    return youtube_url.split("v=")[-1] if "v=" in youtube_url else youtube_url


@router.get("/")
def get_videos(topic_id: str, limit: int = 10):

    cache_key = f"videos:{topic_id}"

    # 1. check cache
    cached = get_cache(cache_key)
    if cached:
        return {
            "cached": True,
            **cached
        }

    # 2. fetch active channels
    response = supabase.table("channel_whitelist") \
        .select("channel_id") \
        .eq("status", "active") \
        .execute()

    channels = response.data
    whitelisted_channel_ids = {ch["channel_id"] for ch in channels}

    all_videos = []

    # 3. scout youtube from whitelisted channels (priority base)
    MAX_WHITELIST_PER_CHANNEL = 3
    for channel in channels:
        videos = fetch_videos_from_channel(
            query=topic_id,
            channel_id=channel["channel_id"],
            max_results=MAX_WHITELIST_PER_CHANNEL,
        )
        all_videos.extend(videos)

    # 4. scout youtube from global search (any channel, excluding whitelisted)
    # Target: ~20 total candidates (whitelisted + global combined)
    global_videos = fetch_videos_from_global_search(
        query=topic_id,
        max_results=17,
        exclude_channel_ids=whitelisted_channel_ids,
    )
    all_videos.extend(global_videos)

    # 5. deduplicate by video ID
    # If duplicate video_id exists, keep the entry with higher engagement_score
    video_map = {}
    for video in all_videos:
        vid_id = extract_video_id(video["youtube_url"])
        
        if vid_id not in video_map:
            video_map[vid_id] = video
        else:
            # Deduplication logic: keep the entry with higher engagement_score
            if video["engagement_score"] > video_map[vid_id]["engagement_score"]:
                video_map[vid_id] = video

    deduplicated_videos = list(video_map.values())
    
    # 6. Compute relevance_score for internal ranking
    # relevance_score represents how well the video matches the topic keyword
    # It's a separate metric from engagement_score, used for internal ranking only
    topic_lower = topic_id.lower()
    for video in deduplicated_videos:
        # Start with relevance_score = 0.0
        relevance_score = 0.0
        
        # Safely check title and description (handle missing fields)
        title = video.get("title", "")
        description = video.get("description", "")
        
        if title and topic_lower in title.lower():
            # Topic keyword found in title: add 1.0 to relevance_score
            relevance_score += 1.0
        elif description and topic_lower in description.lower():
            # Topic keyword found in description: add 0.5 to relevance_score
            relevance_score += 0.5
        
        # Attach relevance_score to video object (internal use only)
        video["relevance_score"] = relevance_score
    
    # 7. Apply relevance-based ranking adjustment
    # Order of operations: base score → relevance adjustment → whitelist boost
    # Relevance is applied before whitelist boost to ensure irrelevant videos
    # are demoted even if they come from whitelisted channels.
    # Whitelist should never rescue an irrelevant video (relevance_score == 0).
    # We use demotion (0.3x) instead of exclusion to maintain soft filtering
    # and allow edge cases where a video might still be useful despite no keyword match.
    for video in deduplicated_videos:
        # a) Base score = engagement_score
        base_score = video["engagement_score"]
        relevance_score = video.get("relevance_score", 0.0)
        
        # b) Apply relevance adjustment
        if relevance_score > 0:
            # Video has relevance: boost score by (1 + relevance_score)
            # e.g. relevance_score 1.0 → 2x multiplier, 1.5 → 2.5x multiplier
            video["engagement_score"] = int(base_score * (1 + relevance_score))
        else:
            # relevance_score == 0: apply strong demotion (0.3x)
            # This demotes irrelevant videos but doesn't exclude them entirely
            video["engagement_score"] = int(base_score * 0.3)
    
    # 8. Apply whitelist priority boost LAST (soft signal, not hard filter)
    # Boost engagement_score by 1.25x for videos from whitelisted channels.
    # Applied after relevance adjustment so whitelist cannot rescue irrelevant videos.
    # Whitelist is a bias signal, not dominance - it only provides a small boost
    # to already-relevant content from trusted sources.
    for video in deduplicated_videos:
        channel_id = video.get("channel_id", "")
        if channel_id in whitelisted_channel_ids:
            # Apply priority boost: multiply engagement_score by 1.25
            video["engagement_score"] = int(video["engagement_score"] * 1.25)
    
    # 9. Rank by engagement_score (highest first)
    ranked_videos = sorted(
        deduplicated_videos,
        key=lambda v: v.get("engagement_score", 0),
        reverse=True,
    )[:limit]

    # 10. Remove internal fields before API response
    # relevance_score is for internal ranking only, not exposed in API
    for video in ranked_videos:
        video.pop("relevance_score", None)
    
    payload = {
        "topic_id": topic_id,
        "total_channels": len(channels),
        "videos_found": len(ranked_videos),
        "videos": ranked_videos,
    }

    # 11. store in cache
    set_cache(cache_key, payload)

    return {
        "cached": False,
        **payload
    }
