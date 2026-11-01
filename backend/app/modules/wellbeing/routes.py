from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_wellbeing():
    return {"module": "wellbeing", "status": "active"}
