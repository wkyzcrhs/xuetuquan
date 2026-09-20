from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.schemas.user import User

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "study"
    tags: Optional[str] = None
    is_public: Optional[int] = 1

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[str] = None
    is_public: Optional[int] = None

class GroupInDBBase(GroupBase):
    id: int
    owner_id: int
    activity_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GroupMember(BaseModel):
    user_id: int
    group_id: int
    status: Optional[str] = "approved"
    joined_at: datetime
    user: User

    class Config:
        from_attributes = True

class Group(GroupInDBBase):
    members: List[User] = []
    membership: List[GroupMember] = []