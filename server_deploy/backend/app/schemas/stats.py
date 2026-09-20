from pydantic import BaseModel
from typing import List

class UserStats(BaseModel):
    post_count: int
    activity_count: int
    group_count: int
    mistake_count: int
    document_count: int
    points: int = 0
    badges: List[str] = []