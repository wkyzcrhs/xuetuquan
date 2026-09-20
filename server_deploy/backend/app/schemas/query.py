from typing import Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    group_id: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]