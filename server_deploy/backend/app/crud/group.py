from typing import List, Optional, Union
from sqlalchemy.orm import Session
from app.models.group import Group, GroupMember, GroupMemberStatus
from app.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate

def get_group(db: Session, id: int) -> Optional[Group]:
    return db.query(Group).filter(Group.id == id).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100) -> List[Group]:
    return db.query(Group).offset(skip).limit(limit).all()

def get_user_groups(db: Session, user_id: int) -> List[Group]:

    owned = db.query(Group).filter(Group.owner_id == user_id).all()
    joined = db.query(Group).join(GroupMember, Group.id == GroupMember.group_id)        .filter(GroupMember.user_id == user_id, GroupMember.status == GroupMemberStatus.APPROVED).all()

    all_groups = list(set(owned + joined))
    return all_groups

def create_group(db: Session, *, group_in: GroupCreate, owner_id: int, activity_id: Optional[int] = None) -> Group:
    db_group = Group(
        name=group_in.name,
        description=group_in.description,
        type=group_in.type,
        owner_id=owner_id,
        activity_id=activity_id,
        is_public=getattr(group_in, 'is_public', 1)
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    add_member(db, db_group=db_group, user_id=owner_id, status=GroupMemberStatus.APPROVED)
    return db_group

def update_group(db: Session, *, db_group: Group, group_update: GroupUpdate) -> Group:
    update_data = group_update.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_group, field, update_data[field])
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def add_member(db: Session, *, db_group: Group, user_id: int, status: GroupMemberStatus = GroupMemberStatus.PENDING) -> GroupMember:

    member = db.query(GroupMember).filter(
        GroupMember.group_id == db_group.id,
        GroupMember.user_id == user_id
    ).first()

    if not member:
        member = GroupMember(
            user_id=user_id,
            group_id=db_group.id,
            status=status
        )
        db.add(member)
        db.commit()
        db.refresh(member)
    elif member.status != status:
        member.status = status
        db.add(member)
        db.commit()
        db.refresh(member)

    return member

def add_member_by_username(db: Session, *, db_group: Group, username: str) -> Optional[GroupMember]:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return add_member(db, db_group=db_group, user_id=user.id, status=GroupMemberStatus.APPROVED)
    return None

def remove_member(db: Session, *, db_group: Group, user_id: int) -> Optional[GroupMember]:
    member = db.query(GroupMember).filter(
        GroupMember.group_id == db_group.id,
        GroupMember.user_id == user_id
    ).first()
    if member:
        db.delete(member)
        db.commit()
    return member

def update_member_status(db: Session, *, group_id: int, user_id: int, status: GroupMemberStatus) -> Optional[GroupMember]:
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if member:
        member.status = status
        db.add(member)
        db.commit()
        db.refresh(member)
    return member