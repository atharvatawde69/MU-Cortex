from fastapi import APIRouter, HTTPException, Query

from app.models.database import supabase

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("")
def list_subjects(
    scheme_id: str = Query(..., description="Scheme id (e.g. 2019 or 2024)"),
    semester: int = Query(..., ge=1, le=8),
    branch: str = Query(..., min_length=1),
):
    try:
        resp = (
            supabase.table("subjects")
            .select("*")
            .eq("scheme_id", scheme_id)
            .eq("semester", semester)
            .eq("branch", branch)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch subjects") from e

