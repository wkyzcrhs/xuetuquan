from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class NotificationType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    ACTIVITY_APPROVAL = "activity_approval"
    ACTIVITY_REJECTION = "activity_rejection"
    ACTIVITY_JOIN = "activity_join"
    GROUP_FILE_UPLOAD = "group_file_upload"
    GROUP_JOIN_REQUEST = "group_join_request"
    GROUP_JOIN_APPROVAL = "group_join_approval"
    GROUP_JOIN_REJECTION = "group_join_rejection"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    type = Column(Enum(NotificationType), nullable=False)
    content = Column(String(255), nullable=True)
    status = Column(String(20), default="pending") 
    target_id = Column(Integer, nullable=True) 
    target_type = Column(String(50), nullable=True) 
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    sender = relationship("User", foreign_keys=[sender_id])