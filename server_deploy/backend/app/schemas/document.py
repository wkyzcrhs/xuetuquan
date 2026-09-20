from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.document import DocStatus
from app.schemas.user import User

class DocumentBase(BaseModel):
    title: str
    file_url: str
    group_id: Optional[int] = None 

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    status: Optional[DocStatus] = None

class Document(DocumentBase):
    id: int
    user_id: int
    status: DocStatus
    created_at: datetime
    user: Optional[User] = None

    class Config:
        from_attributes = True