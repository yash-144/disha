from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_cases():
    return {"module": "cases", "status": "active"}
