from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_counselling():
    return {"module": "counselling", "status": "active"}
