from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_audit():
    return {"module": "audit", "status": "active"}
