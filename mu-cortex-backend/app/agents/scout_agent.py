import os
import requests

# Scout Phase 2 logic frozen after relevance-gated ranking validation.
# Validation confirmed: relevance-based demotion (0.3x for irrelevant),
# whitelist boost (1.25x) applied last, ~20 candidate pool, proper deduplication.

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
STATS_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_videos_from_channel(query: str, channel_id: str, max_results: int = 5):
    # 1. search videos
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "channelId": channel_id,
        "key": YOUTUBE_API_KEY,
    }

    search_response = requests.get(SEARCH_URL, params=search_params)
    search_response.raise_for_status()
    search_data = search_response.json()

    video_ids = [
        item["id"]["videoId"]
        for item in search_data.get("items", [])
    ]

    if not video_ids:
        return []

    # 2. fetch statistics
    stats_params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    stats_response = requests.get(STATS_URL, params=stats_params)
    stats_response.raise_for_status()
    stats_data = stats_response.json()

    stats_map = {
        item["id"]: item["statistics"]
        for item in stats_data.get("items", [])
    }

    videos = []
    for item in search_data.get("items", []):
        vid = item["id"]["videoId"]
        stats = stats_map.get(vid, {})

        views = int(stats.get("viewCount", 0))
        comments = int(stats.get("commentCount", 0))

        videos.append({
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "channel": item["snippet"]["channelTitle"],
            "channel_id": item["snippet"]["channelId"],
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "views": views,
            "comments": comments,
            "engagement_score": views + comments,
        })

    return videos


def fetch_videos_from_global_search(query: str, max_results: int = 12, exclude_channel_ids: set = None):
    """
    Fetch videos from global YouTube search (any channel).
    Similar to fetch_videos_from_channel but without channelId filter.
    Excludes channels in exclude_channel_ids to prevent double-weighting.
    """
    if exclude_channel_ids is None:
        exclude_channel_ids = set()
    
    # 1. search videos
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }

    search_response = requests.get(SEARCH_URL, params=search_params)
    search_response.raise_for_status()
    search_data = search_response.json()

    video_ids = [
        item["id"]["videoId"]
        for item in search_data.get("items", [])
    ]

    if not video_ids:
        return []

    # 2. fetch statistics
    stats_params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    stats_response = requests.get(STATS_URL, params=stats_params)
    stats_response.raise_for_status()
    stats_data = stats_response.json()

    stats_map = {
        item["id"]: item["statistics"]
        for item in stats_data.get("items", [])
    }

    videos = []
    for item in search_data.get("items", []):
        channel_id = item["snippet"]["channelId"]
        
        # Skip whitelisted channels to prevent double-weighting
        # These channels are already handled in Phase A (whitelisted fetch)
        if channel_id in exclude_channel_ids:
            continue
        
        vid = item["id"]["videoId"]
        stats = stats_map.get(vid, {})

        views = int(stats.get("viewCount", 0))
        comments = int(stats.get("commentCount", 0))

        videos.append({
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "channel": item["snippet"]["channelTitle"],
            "channel_id": channel_id,
            "youtube_url": f"https://www.youtube.com/watch?v={vid}",
            "views": views,
            "comments": comments,
            "engagement_score": views + comments,
        })

    return videos