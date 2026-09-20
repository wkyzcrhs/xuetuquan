from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.group import Group, GroupCreate, GroupUpdate
from app.crud import group as crud_group
from app.models.user import User
from app.models.group import GroupMember, GroupMemberStatus
from app.crud.notification import create_notification
from app.models.notification import NotificationType
from pydantic import BaseModel

router = APIRouter()

class InviteRequest(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

class ApproveRequest(BaseModel):
    user_id: int
    approve: bool

@router.post("", response_model=Group)
def create_group(
    *,
    db: Session = Depends(deps.get_db),
    group_in: GroupCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    group = crud_group.create_group(db=db, group_in=group_in, owner_id=current_user.id)
    return group

@router.put("/{group_id}", response_model=Group)
def update_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    group_in: GroupUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    if group.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")

    group = crud_group.update_group(db=db, db_group=group, group_update=group_in)
    return group

@router.get("", response_model=List[Group])
def read_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    groups = crud_group.get_user_groups(db=db, user_id=current_user.id)
    return groups

@router.get("/discover", response_model=List[Group])
def discover_groups(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    from app.models.group import Group as GroupModel
    from sqlalchemy import or_

    query = db.query(GroupModel).filter(GroupModel.owner_id != current_user.id)
    user_membership_ids = [m.group_id for m in db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()]
    if user_membership_ids:
        query = query.filter(GroupModel.id.notin_(user_membership_ids))

    if current_user.preferences:
        prefs = [p.strip() for p in current_user.preferences.split(',') if p.strip()]
        if prefs:
            conditions = []
            for pref in prefs:
                conditions.append(GroupModel.tags.ilike(f"%{pref}%"))
                conditions.append(GroupModel.name.ilike(f"%{pref}%"))
                conditions.append(GroupModel.description.ilike(f"%{pref}%"))
            query = query.filter(or_(*conditions))

    return query.limit(20).all()

@router.post("/{group_id}/join")
def join_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    if group.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="群主已经是群成员")

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()

    if member:
        if member.status == GroupMemberStatus.APPROVED:
            raise HTTPException(status_code=400, detail="已经是群成员")
        if member.status == GroupMemberStatus.PENDING:
            raise HTTPException(status_code=400, detail="加群请求待审核")

    crud_group.add_member(db=db, db_group=group, user_id=current_user.id, status=GroupMemberStatus.PENDING)

    create_notification(
        db=db,
        user_id=group.owner_id,
        sender_id=current_user.id,
        type=NotificationType.GROUP_JOIN_REQUEST,
        content=f"{current_user.username} 申请加入你的小组: {group.name}",
        target_id=group.id,
        target_type="group"
    )

    return {"message": "Request sent"}

@router.post("/{group_id}/approve")
def approve_join_request(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    approve_in: ApproveRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    if group.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")

    status = GroupMemberStatus.APPROVED if approve_in.approve else GroupMemberStatus.REJECTED
    member = crud_group.update_member_status(db=db, group_id=group_id, user_id=approve_in.user_id, status=status)

    if not member:
        raise HTTPException(status_code=404, detail="未找到加群请求")

    from app.models.notification import Notification, NotificationType
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.sender_id == approve_in.user_id,
        Notification.type == NotificationType.GROUP_JOIN_REQUEST,
        Notification.target_id == group_id,
        Notification.target_type == "group"
    ).update({Notification.status: status, Notification.is_read: True}, synchronize_session=False)

    notif_type = NotificationType.GROUP_JOIN_APPROVAL if approve_in.approve else NotificationType.GROUP_JOIN_REJECTION
    status_text = "已通过" if approve_in.approve else "被拒绝"
    create_notification(
        db=db,
        user_id=approve_in.user_id,
        sender_id=current_user.id,
        type=notif_type,
        content=f"你加入小组 '{group.name}' 的申请{status_text}。",
        target_id=group.id,
        target_type="group"
    )

    return {"message": f"Join request {status_text}"}

@router.get("/{group_id}", response_model=Group)
def read_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    is_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.status == GroupMemberStatus.APPROVED
    ).first()

    if not is_member and group.owner_id != current_user.id and not current_user.is_superuser:
         raise HTTPException(status_code=403, detail="不是该群组的成员")
    return group

@router.post("/{group_id}/invite", response_model=Group)
def invite_member(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    invite_in: InviteRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    if group.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有群主可以邀请成员")

    if invite_in.user_id:
        group = crud_group.add_member(db=db, db_group=group, user_id=invite_in.user_id)
    elif invite_in.username:
        group = crud_group.add_member_by_username(db=db, db_group=group, username=invite_in.username)
        if not group:
            raise HTTPException(status_code=404, detail="未找到该用户")
    else:
        raise HTTPException(status_code=400, detail="必须提供用户ID或用户名")

    return group

@router.delete("/{group_id}/members/{user_id}", response_model=Group)
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    group = crud_group.get_group(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="未找到该群组")

    if group.owner_id != current_user.id and current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")

    crud_group.remove_member(db=db, db_group=group, user_id=user_id)
    return crud_group.get_group(db=db, id=group_id)