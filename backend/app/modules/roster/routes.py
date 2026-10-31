from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_roster():
    return {"module": "roster", "status": "active"}
