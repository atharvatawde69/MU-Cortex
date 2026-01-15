from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status():
    # No auth implementation yet (placeholder)
    return {"auth": "not_implemented"}

