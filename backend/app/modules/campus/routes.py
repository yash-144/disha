from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_campus():
    return {"module": "campus", "status": "active"}
