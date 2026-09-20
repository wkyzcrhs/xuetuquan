from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType

def create_notification(
    db: Session,
    user_id: int,
    type: NotificationType,
    content: str,
    target_id: int = None,
    target_type: str = None,
    sender_id: int = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        sender_id=sender_id,
        type=type,
        content=content,
        target_id=target_id,
        target_type=target_type
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification