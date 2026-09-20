from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base

class TaskType(str, enum.Enum):
    READING = "reading" 
    PRACTICE = "practice" 
    QUIZ = "quiz" 

class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True) 
    type = Column(Enum(TaskType), default=TaskType.READING)
    is_completed = Column(Boolean, default=False)
    scheduled_date = Column(DateTime(timezone=True), index=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("LearningPlan", back_populates="daily_tasks")