from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_ml():
    return {"module": "ml", "status": "active"}
