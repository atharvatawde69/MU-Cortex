"""
YouTube transcript fetching service.

Provides functionality to extract video IDs, fetch transcripts,
and get the best context from video resources for a given topic.
"""
import asyncio
import re
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


class TranscriptService:
    """Service for fetching and processing YouTube transcripts."""

    @staticmethod
    def extract_video_id(youtube_url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.

        Supports:
        - youtube.com/watch?v=VIDEO_ID
        - youtu.be/VIDEO_ID
        - youtube.com/embed/VIDEO_ID
        - youtube.com/v/VIDEO_ID

        Args:
            youtube_url: YouTube URL in any supported format.

        Returns:
            Video ID string or None if not found.
        """
        if not youtube_url:
            return None

        # Pattern for youtube.com/watch?v=VIDEO_ID
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})', youtube_url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    async def get_transcript(
        youtube_url: str,
        max_length: int = 3000
    ) -> Optional[str]:
        """
        Fetch transcript from YouTube video.

        Prefers manual transcripts (en, hi), falls back to auto-generated (en, hi).
        Truncates to max_length characters.

        Args:
            youtube_url: YouTube URL.
            max_length: Maximum length of transcript to return.

        Returns:
            Transcript text or None if unavailable.
        """
        video_id = TranscriptService.extract_video_id(youtube_url)
        if not video_id:
            return None

        def _fetch_sync():
            try:
                # Try manual transcripts first (en, hi)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                transcript = None
                try:
                    # Prefer manual English
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                except NoTranscriptFound:
                    try:
                        # Fallback to manual Hindi
                        transcript = transcript_list.find_manually_created_transcript(['hi'])
                    except NoTranscriptFound:
                        # Fallback to auto-generated English
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                        except NoTranscriptFound:
                            # Fallback to auto-generated Hindi
                            try:
                                transcript = transcript_list.find_generated_transcript(['hi'])
                            except NoTranscriptFound:
                                return None
                
                # Fetch transcript data
                transcript_data = transcript.fetch()
                
                # Concatenate text
                text_parts = [item['text'] for item in transcript_data]
                full_text = ' '.join(text_parts)
                
                # Truncate to max_length
                if len(full_text) > max_length:
                    full_text = full_text[:max_length].rsplit(' ', 1)[0] + '...'
                
                return full_text
                
            except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, Exception):
                return None

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_sync)

    @staticmethod
    async def get_best_context_for_topic(
        topic_id: str,
        supabase_client
    ) -> str:
        """
        Get the best transcript context for a topic from video resources.

        Queries video_resources table, orders by engagement_score DESC,
        tries to fetch transcripts from top 3 videos, returns first successful.

        Args:
            topic_id: Topic UUID.
            supabase_client: Supabase client instance.

        Returns:
            Formatted context string: "[Context from: VIDEO_TITLE]\n\nTRANSCRIPT"
            Returns empty string if no transcript found.
        """
        if not topic_id:
            return ""

        try:
            # Query video_resources for this topic
            resp = (
                supabase_client.table("video_resources")
                .select("youtube_url, title")
                .eq("topic_id", topic_id)
                .order("engagement_score", desc=True)
                .limit(3)
                .execute()
            )

            videos = resp.data or []
            if not videos:
                return ""

            # Try to fetch transcript from videos in order
            for video in videos:
                youtube_url = video.get("youtube_url")
                title = video.get("title", "Unknown Video")

                if not youtube_url:
                    continue

                transcript = await TranscriptService.get_transcript(youtube_url)
                if transcript:
                    return f"[Context from: {title}]\n\n{transcript}"

            return ""

        except Exception:
            return ""
