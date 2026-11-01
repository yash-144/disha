from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_notifications():
    return {"module": "notifications", "status": "active"}
