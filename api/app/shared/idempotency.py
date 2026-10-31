from fastapi import Header, HTTPException

async def verify_idempotency_key(idempotency_key: str = Header(..., alias="X-Idempotency-Key")):
    if not idempotency_key or len(idempotency_key) < 16:
        raise HTTPException(status_code=400, detail="Invalid X-Idempotency-Key header")
    return idempotency_key
