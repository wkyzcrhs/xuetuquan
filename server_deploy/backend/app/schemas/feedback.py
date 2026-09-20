from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.user import User

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    user_id: int
    status: str
    created_at: Optional[datetime] = None
    user: Optional[User] = None

    class Config:
        from_attributes = True