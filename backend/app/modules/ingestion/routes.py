from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_ingestion():
    return {"module": "ingestion", "status": "active"}
