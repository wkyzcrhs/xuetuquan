from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any
from app.schemas.user import User
from app.schemas.group import Group

class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    category: Optional[str] = None
    cover_url: Optional[str] = None
    is_team: Optional[bool] = False
    team_limit: Optional[int] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    category: Optional[str] = None
    cover_url: Optional[str] = None
    is_team: Optional[bool] = None
    team_limit: Optional[int] = None
    status: Optional[str] = None

class Activity(ActivityBase):
    id: int
    organizer_id: int
    status: str
    created_at: Optional[datetime] = None
    organizer: User
    participants: List[User] = []
    group_id: Optional[int] = None
    group: Optional[Group] = None
    teams: List[Group] = []

    class Config:
        from_attributes = True