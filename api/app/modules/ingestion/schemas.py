from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ImportIssue(BaseModel):
    code: str
    table: str
    message: str
    count: int = 1
    sample: List[str] = []


class ImportBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campus_id: str
    uploaded_by: str
    status: str
    file_sha256: str
    source_files: List[Dict[str, Any]]
    row_counts: Dict[str, int]
    term_ids: List[str]
    validation_errors: List[ImportIssue]
    warnings: List[ImportIssue]
    linked_students: int
    unlinked_students: int
    created_at: datetime
    committed_at: Optional[datetime] = None
    duplicate: bool = False


class ImportBatchPage(BaseModel):
    items: List[ImportBatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TableSpec(BaseModel):
    name: str
    required: bool
    required_columns: List[str]
    optional_columns: List[str]


class CanonicalSchemaResponse(BaseModel):
    tables: List[TableSpec]
    upload_fields: List[str]
    notes: List[str]
