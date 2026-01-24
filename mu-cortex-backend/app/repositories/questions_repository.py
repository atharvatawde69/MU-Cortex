"""
Repository for question data access.

Provides functions to query the questions table in Supabase.
"""
import asyncio
from typing import Optional

from app.models.database import supabase


async def get_question_by_id(question_id: str) -> Optional[dict]:
    """
    Fetch a question by its ID from the questions table.

    Args:
        question_id: UUID string of the question.

    Returns:
        Dictionary with keys: id, question_text, marks, topic_id
        Returns None if question not found.
    """
    def _fetch_sync():
        try:
            resp = (
                supabase.table("questions")
                .select("id, question_text, marks, topic_id")
                .eq("id", question_id)
                .execute()
            )
            
            if resp.data and len(resp.data) > 0:
                return resp.data[0]
            return None
        except Exception:
            return None
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync)
