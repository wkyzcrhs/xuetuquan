from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.notification import NotificationType
from app.schemas.user import User as UserSchema

class NotificationBase(BaseModel):
    type: NotificationType
    content: Optional[str] = None
    status: Optional[str] = "pending"
    target_id: Optional[int] = None
    target_type: Optional[str] = None

class NotificationCreate(NotificationBase):
    user_id: int
    sender_id: Optional[int] = None

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class Notification(NotificationBase):
    id: int
    user_id: int
    sender_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    sender: Optional[UserSchema] = None

    class Config:
        from_attributes = True

class NotificationCount(BaseModel):
    unread_count: int