from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_student_identity():
    return {"module": "student_identity", "status": "active"}
