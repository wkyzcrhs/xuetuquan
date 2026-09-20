from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class LearningRecord(BaseModel):
    id: int
    type: str  
    content: str
    created_at: datetime

class LearningProgress(BaseModel):
    completed: int
    total: int
    percentage: float

class LearningSummary(BaseModel):
    progress: LearningProgress
    recent_records: List[LearningRecord]