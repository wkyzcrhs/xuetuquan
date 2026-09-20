from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MistakeBase(BaseModel):
    subject: str
    raw_text: Optional[str] = None
    image_url: Optional[str] = None
    ai_analysis: Optional[str] = None

class MistakeCreate(MistakeBase):
    pass

class MistakeUpdate(BaseModel):
    ai_analysis: Optional[str] = None

class Mistake(MistakeBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True