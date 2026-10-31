from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentsBase(BaseModel):
    pass

class DocumentsResponse(DocumentsBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
