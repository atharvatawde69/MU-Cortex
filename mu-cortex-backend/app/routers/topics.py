import logging
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Query

from app.models.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("")
def get_topics(
    subject_id: str = Query(..., description="Subject UUID"),
    scheme_id: str = Query(..., description="Scheme id (e.g. 2019 or 2024)"),
):
    """
    Fetch topics for a subject, grouped by module_number.
    
    Returns topics ordered by module_number ASC, grouped into modules.
    """
    try:
        # 1. Verify subject exists for given subject_id and scheme_id
        subject_resp = (
            supabase.table("subjects")
            .select("id, name")
            .eq("id", subject_id)
            .eq("scheme_id", scheme_id)
            .execute()
        )
        
        if not subject_resp.data:
            logger.warning(f"Subject not found: subject_id={subject_id}, scheme_id={scheme_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Subject not found for subject_id={subject_id} and scheme_id={scheme_id}"
            )
        
        subject = subject_resp.data[0]
        subject_name = subject["name"]
        
        # 2. Fetch all topics for that subject from topics table
        topics_resp = (
            supabase.table("topics")
            .select("id, name, module_number")
            .eq("subject_id", subject_id)
            .order("module_number", desc=False)  # Order by module_number ASC
            .execute()
        )
        
        topics = topics_resp.data or []
        
        # 3. Group topics by module_number
        modules_dict = defaultdict(list)
        for topic in topics:
            module_num = topic["module_number"]
            modules_dict[module_num].append({
                "id": topic["id"],
                "name": topic["name"]
            })
        
        # 4. Build response with modules sorted by module_number
        modules = [
            {
                "module_number": module_num,
                "topics": topics_list
            }
            for module_num, topics_list in sorted(modules_dict.items())
        ]
        
        response = {
            "subject_id": subject_id,
            "subject_name": subject_name,
            "total_topics": len(topics),
            "modules": modules
        }
        
        logger.info(f"Fetched {len(topics)} topics for subject_id={subject_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch topics") from e
