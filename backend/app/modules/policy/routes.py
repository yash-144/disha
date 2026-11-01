from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_policy():
    return {"module": "policy", "status": "active"}
