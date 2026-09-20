import os
import shutil
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.activity import Activity, ActivityCreate, ActivityUpdate
from app.crud import activity as crud_activity
from app.models.activity import ActivityStatus
from app.models.user import User as UserModel
from app.crud import group as crud_group
from app.schemas.group import GroupCreate
from app.crud.notification import create_notification
from app.models.notification import NotificationType

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.post("/upload_cover")
def upload_activity_cover(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
    file: UploadFile = File(...)
) -> Any:

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".png"
    filename = f"activity_cover_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cover_url = f"/static/{filename}"

    return {"cover_url": cover_url}

@router.post("", response_model=Activity)
def create_activity(
    *,
    db: Session = Depends(deps.get_db),
    activity_in: ActivityCreate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.create_activity(db=db, activity=activity_in, user_id=current_user.id)
    return activity

@router.put("/{activity_id}", response_model=Activity)
def update_activity(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    activity_in: ActivityUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")
    if not current_user.is_superuser and activity.organizer_id != current_user.id:
        raise HTTPException(status_code=400, detail="权限不足")

    if activity.status == ActivityStatus.REJECTED and not current_user.is_superuser:
        activity_in.status = ActivityStatus.PENDING

    activity = crud_activity.update_activity(db=db, db_activity=activity, activity_update=activity_in)
    return activity

@router.get("", response_model=List[Activity])
def read_activities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="按分类筛选"),
    status: Optional[str] = Query(None, description="Filter by status"),
    only_public: bool = Query(False, description="Only show public activities (exclude my pending/rejected)"),
    current_user: Optional[UserModel] = Depends(deps.get_current_user_optional),
) -> Any:

    user_id = current_user.id if current_user else None
    is_superuser = current_user.is_superuser if current_user else False

    if not current_user:
        only_public = True

    activities = crud_activity.get_activities(
        db=db, 
        skip=skip, 
        limit=limit, 
        category=category,
        status=status,
        user_id=user_id,
        is_superuser=is_superuser,
        only_public=only_public
    )
    return activities

@router.post("/{activity_id}/join", response_model=Activity)
def join_activity(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    if activity.status != ActivityStatus.RECRUITING:
        pass

    if current_user in activity.participants:
        raise HTTPException(status_code=400, detail="已经参加了")

    if activity.team_limit and len(activity.participants) >= activity.team_limit:
        raise HTTPException(status_code=400, detail="活动名额已满")

    if not activity.is_team:

        activity.participants.append(current_user)

        if activity.organizer:
            activity.organizer.points += 2

            if activity.organizer_id != current_user.id:
                create_notification(
                    db=db,
                    user_id=activity.organizer_id,
                    sender_id=current_user.id,
                    type=NotificationType.ACTIVITY_JOIN,
                    content=f"{current_user.username} 参与了你发布的活动: {activity.title}",
                    target_id=activity.id,
                    target_type="activity"
                )
    else:

        raise HTTPException(status_code=400, detail="团队活动需要创建或加入队伍")

    db.commit()
    db.refresh(activity)
    return activity

@router.post("/{activity_id}/teams/create", response_model=Activity)
def become_captain(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    if activity.status != ActivityStatus.RECRUITING:

        pass

    if not activity.is_team:
        raise HTTPException(status_code=400, detail="非团队活动")

    if current_user in activity.participants:
        raise HTTPException(status_code=400, detail="已经参加了该活动")

    activity.participants.append(current_user)

    group_in = GroupCreate(
        name=f"队伍：{activity.title}",
        description=f"针对活动 {activity.title} 创建的队伍",
        type="study",
        is_public=1
    )
    group = crud_group.create_group(db=db, group_in=group_in, owner_id=current_user.id, activity_id=activity.id)

    db.commit()
    db.refresh(activity)
    return activity

from app.schemas.group import Group as GroupSchema
@router.get("/{activity_id}/teams", response_model=List[GroupSchema])
def get_activity_teams(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    from app.models.group import Group as GroupModel
    teams = db.query(GroupModel).filter(
        GroupModel.activity_id == activity_id,
        GroupModel.is_public == 1
    ).all()

    if activity.team_limit:
        available_teams = []
        for team in teams:

            from app.models.group import GroupMember, GroupMemberStatus
            member_count = db.query(GroupMember).filter(
                GroupMember.group_id == team.id,
                GroupMember.status == GroupMemberStatus.APPROVED
            ).count()
            if member_count < activity.team_limit:
                available_teams.append(team)
        return available_teams

    return teams

@router.post("/{activity_id}/teams/{group_id}/join")
def join_activity_team(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    group_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    if current_user in activity.participants:
        raise HTTPException(status_code=400, detail="已经参加了该活动")

    from app.models.group import Group as GroupModel, GroupMember, GroupMemberStatus
    team = db.query(GroupModel).filter(
        GroupModel.id == group_id,
        GroupModel.activity_id == activity_id
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="未找到该队伍")

    if activity.team_limit:
        member_count = db.query(GroupMember).filter(
            GroupMember.group_id == team.id,
            GroupMember.status == GroupMemberStatus.APPROVED
        ).count()
        if member_count >= activity.team_limit:
            raise HTTPException(status_code=400, detail="队伍名额已满")

    member = db.query(GroupMember).filter(
        GroupMember.group_id == team.id,
        GroupMember.user_id == current_user.id
    ).first()

    if member:
        if member.status == GroupMemberStatus.APPROVED:
            raise HTTPException(status_code=400, detail="已经是群成员")
        if member.status == GroupMemberStatus.PENDING:
            raise HTTPException(status_code=400, detail="加群请求待审核")

    crud_group.add_member(db=db, db_group=team, user_id=current_user.id, status=GroupMemberStatus.PENDING)

    create_notification(
        db=db,
        user_id=team.owner_id,
        sender_id=current_user.id,
        type=NotificationType.GROUP_JOIN_REQUEST,
        content=f"{current_user.username} 申请加入你的队伍: {team.name} (活动: {activity.title})",
        target_id=team.id,
        target_type="group"
    )

    db.commit()

    return {"message": "请求已发送"}

@router.get("/{activity_id}", response_model=Activity)
def read_activity(
    *,
    db: Session = Depends(deps.get_db),
    activity_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:

    activity = crud_activity.get_activity(db=db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")
    return activity