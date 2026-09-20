from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, Table, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class GroupType(str, enum.Enum):
    STUDY = "study"
    COMPETITION = "competition"
    HOBBY = "hobby"

class GroupMemberStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class GroupMember(Base):
    __tablename__ = "group_members"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    status = Column(Enum(GroupMemberStatus), default=GroupMemberStatus.APPROVED) 
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    group = relationship("Group")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(GroupType), default=GroupType.STUDY)
    tags = Column(String(255), nullable=True) 
    is_public = Column(Integer, default=1) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="owned_groups")
    members = relationship("User", secondary="group_members", back_populates="groups", viewonly=True)
    membership = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="group")
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True) 
    activity = relationship("Activity", back_populates="teams", foreign_keys=[activity_id])