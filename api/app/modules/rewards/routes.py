from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_rewards():
    return {"module": "rewards", "status": "active"}
