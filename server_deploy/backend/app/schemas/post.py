from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.user import User

class PostBase(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

class Post(PostBase):
    id: int
    author_id: int
    like_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: User
    is_liked: Optional[bool] = False

    class Config:
        from_attributes = True