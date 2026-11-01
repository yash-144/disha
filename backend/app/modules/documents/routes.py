from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_documents():
    return {"module": "documents", "status": "active"}
