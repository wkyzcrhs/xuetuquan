import os
import shutil
import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.user import User, UserCreate, UserUpdate
from app.schemas.stats import UserStats
from app.schemas.post import Post as PostSchema
from app.schemas.activity import Activity as ActivitySchema
from app.schemas.group import Group as GroupSchema
from app.models.user import User as UserModel
from app.models.document import Document
from app.models.mistake import Mistake
from app.models.post import Post
from app.models.activity import Activity
from app.models.group import Group, GroupMember
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, Feedback as FeedbackSchema
from app.core.security import get_password_hash, verify_password
from pydantic import BaseModel
from fastapi import HTTPException
from app.models.chat_history import ChatHistory
from sqlalchemy import or_, func
from datetime import date, datetime, timedelta

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.get("/me/daily_report")
def get_daily_report(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = today_start + timedelta(days=1)

    personal_chat_count = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.group_id == None,
        ChatHistory.created_at >= today_start,
        ChatHistory.created_at < today_end
    ).count()

    group_chat_count = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.group_id != None,
        ChatHistory.created_at >= today_start,
        ChatHistory.created_at < today_end
    ).count()

    document_count = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.created_at >= today_start,
        Document.created_at < today_end
    ).count()

    return {
        "personal_chat_count": personal_chat_count,
        "group_chat_count": group_chat_count,
        "document_count": document_count,
        "total_chat_count": personal_chat_count + group_chat_count
    }

@router.get("/me/stats", response_model=UserStats)
def get_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    post_count = db.query(Post).filter(Post.author_id == current_user.id).count()
    activity_count = db.query(Activity).filter(Activity.organizer_id == current_user.id).count()

    group_count = db.query(Group).join(GroupMember, Group.id == GroupMember.group_id)        .filter(or_(Group.owner_id == current_user.id, GroupMember.user_id == current_user.id))        .distinct().count()

    mistake_count = db.query(Mistake).filter(Mistake.user_id == current_user.id).count()

    document_count = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.group_id == None
    ).count()

    badges = []

    if current_user.ai_chat_count >= 50 and current_user.ai_extract_count >= 100:
        badges.append("AI掌控者")
    elif current_user.ai_chat_count >= 10 and current_user.ai_extract_count >= 20:
        badges.append("AI探索者")

    if current_user.points >= 5000:
        badges.append("废寝忘食")
    elif current_user.points >= 2000:
        badges.append("精益求精")
    elif current_user.points >= 1000:
        badges.append("持之以恒")
    elif current_user.points >= 500:
        badges.append("刻苦用功")
    elif current_user.points >= 100:
        badges.append("勤奋好学")
    else:
        badges.append("新人上路")

    return UserStats(
        post_count=post_count,
        activity_count=activity_count,
        group_count=group_count,
        mistake_count=mistake_count,
        document_count=document_count,
        points=current_user.points,
        badges=badges
    )

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@router.put("/me/password")
def update_password(
    *,
    db: Session = Depends(deps.get_db),
    password_in: PasswordUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    if not verify_password(password_in.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    current_user.password_hash = get_password_hash(password_in.new_password)
    db.commit()
    return {"message": "密码修改成功"}

@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data:
        hashed_password = get_password_hash(user_data["password"])
        del user_data["password"]
        user_data["password_hash"] = hashed_password

    for field, value in user_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=User)
def upload_avatar(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
    file: UploadFile = File(...)
) -> Any:

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".png" 
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"/static/{filename}"

    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)

    return current_user

@router.post("/feedbacks")
def create_feedback(
    *,
    db: Session = Depends(deps.get_db),
    feedback_in: FeedbackCreate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    feedback = Feedback(
        user_id=current_user.id,
        content=feedback_in.content
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"message": "success"}

@router.get("/me", response_model=User)
def read_user_me(
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    return current_user

@router.get("/me/posts", response_model=List[PostSchema])
def read_user_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    posts = db.query(Post).filter(Post.author_id == current_user.id).offset(skip).limit(limit).all()
    return posts

@router.get("/me/groups", response_model=List[GroupSchema])
def read_user_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    groups = db.query(Group).filter(Group.owner_id == current_user.id).offset(skip).limit(limit).all()
    return groups

@router.get("/me/activities", response_model=List[ActivitySchema])
def read_user_activities(
    type: str = "participated",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    if type == "created":
        activities = db.query(Activity).filter(Activity.organizer_id == current_user.id).offset(skip).limit(limit).all()
    else:
        activities = db.query(Activity).filter(Activity.participants.any(id=current_user.id)).offset(skip).limit(limit).all()
    return activities