from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    major: Optional[str] = None
    learning_goal: Optional[str] = None
    preferences: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    major: Optional[str] = None
    learning_goal: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[str] = None

class User(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    points: int = 0
    ai_chat_count: int = 0
    ai_extract_count: int = 0

    @field_validator('points', 'ai_chat_count', 'ai_extract_count', mode='before')
    def set_zero_if_none(cls, v):
        return v if v is not None else 0

    @property
    def title(self) -> str:

        ai_chat = self.ai_chat_count or 0
        ai_ext = self.ai_extract_count or 0
        pts = self.points or 0

        if ai_chat >= 50 and ai_ext >= 100:
            return "AI掌控者"
        if ai_chat >= 10 and ai_ext >= 20:
            return "AI探索者"

        if pts >= 5000:
            return "废寝忘食"
        if pts >= 2000:
            return "精益求精"
        if pts >= 1000:
            return "持之以恒"
        if pts >= 500:
            return "刻苦用功"
        if pts >= 100:
            return "勤奋好学"
        return "新人上路"

    class Config:
        from_attributes = True

class UserStats(BaseModel):
    post_count: int
    activity_count: int
    group_count: int
    mistake_count: int
    document_count: int = 0
    points: int = 0
    badges: List[str] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None