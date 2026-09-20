from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatHistoryCreate(BaseModel):
    query: str
    answer: str
    group_id: Optional[int] = None
    sources: Optional[List[str]] = []

class ChatHistoryResponse(BaseModel):
    id: int
    user_id: int
    group_id: Optional[int] = None
    query: str
    answer: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True