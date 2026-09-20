import enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, func, Table
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

activity_participants = Table(
    "activity_participants",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id"), primary_key=True),
)

class ActivityStatus(str, enum.Enum):
    PENDING = "PENDING" 
    REJECTED = "REJECTED" 
    RECRUITING = "RECRUITING"
    ONGOING = "ONGOING"
    ENDED = "ENDED"

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    cover_url = Column(String(255), nullable=True)
    is_team = Column(Integer, default=0) 
    team_limit = Column(Integer, nullable=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ActivityStatus), default=ActivityStatus.PENDING) 
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organizer = relationship("User", back_populates="activities")
    group = relationship("Group", foreign_keys=[group_id])
    teams = relationship("Group", back_populates="activity", foreign_keys="[Group.activity_id]")
    participants = relationship("User", secondary=activity_participants, back_populates="participated_activities")