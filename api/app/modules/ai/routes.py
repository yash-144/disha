from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_ai():
    return {"module": "ai", "status": "active"}
