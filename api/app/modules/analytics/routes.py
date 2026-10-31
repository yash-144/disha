from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_analytics():
    return {"module": "analytics", "status": "active"}
