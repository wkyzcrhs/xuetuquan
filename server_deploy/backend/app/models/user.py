from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(255), nullable=True)
    major = Column(String(100), nullable=True)
    learning_goal = Column(String(255), nullable=True)
    preferences = Column(String(255), nullable=True)

    points = Column(Integer, default=0)
    ai_chat_count = Column(Integer, default=0)
    ai_extract_count = Column(Integer, default=0)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    mistakes = relationship("Mistake", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="organizer", cascade="all, delete-orphan")
    participated_activities = relationship("Activity", secondary="activity_participants", back_populates="participants")
    owned_groups = relationship("Group", back_populates="owner", cascade="all, delete-orphan")
    groups = relationship("Group", secondary="group_members", back_populates="members", viewonly=True)
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlan", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")