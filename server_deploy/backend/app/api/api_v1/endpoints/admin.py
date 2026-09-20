from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Date
from app.api import deps
from app.crud import post as crud_post
from app.crud import activity as crud_activity
from app.crud import comment as crud_comment
from app.models.post import Post
from app.models.activity import Activity, ActivityStatus
from app.models.comment import Comment
from app.models.feedback import Feedback, FeedbackStatus
from app.schemas import post as schemas_post
from app.schemas import activity as schemas_activity
from app.schemas import comment as schemas_comment
from app.schemas import feedback as schemas_feedback
from datetime import datetime, timedelta
from app.crud.notification import create_notification
from app.models.notification import NotificationType

router = APIRouter()

@router.get("/feedbacks", response_model=List[schemas_feedback.Feedback])
def get_all_feedbacks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    feedbacks = db.query(Feedback).options(joinedload(Feedback.user)).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    return feedbacks

@router.put("/feedbacks/{feedback_id}/resolve")
def resolve_feedback(
    *,
    db: Session = Depends(deps.get_db),
    feedback_id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="未找到该反馈")

    feedback.status = FeedbackStatus.RESOLVED
    db.commit()
    db.refresh(feedback)
    return {"message": "Success"}

@router.get("/stats/daily", response_model=dict)
def get_daily_stats(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)

    posts_stats = db.query(
        cast(Post.created_at, Date).label('date'),
        func.count(Post.id).label('count')
    ).filter(
        Post.created_at >= start_date
    ).group_by(
        cast(Post.created_at, Date)
    ).all()

    activities_stats = db.query(
        cast(Activity.created_at, Date).label('date'),
        func.count(Activity.id).label('count')
    ).filter(
        Activity.created_at >= start_date
    ).group_by(
        cast(Activity.created_at, Date)
    ).all()

    result = {
        "dates": [],
        "posts": [],
        "activities": []
    }

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        result["dates"].append(date_str)

        post_count = 0
        for p in posts_stats:
            if p.date == current:
                post_count = p.count
                break
        result["posts"].append(post_count)

        activity_count = 0
        for a in activities_stats:
            if a.date == current:
                activity_count = a.count
                break
        result["activities"].append(activity_count)

        current += timedelta(days=1)

    return result

@router.get("/activities", response_model=List[schemas_activity.Activity])
def get_all_activities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    activities = db.query(Activity).options(joinedload(Activity.organizer)).order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()

    for act in activities:
        if act.category is None:
            act.category = "其他"
        if act.location is None:
            act.location = "未指定"
        if act.description is None:
            act.description = ""

    return activities

@router.put("/activities/{id}/approve", response_model=schemas_activity.Activity)
def approve_activity(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    activity = db.query(Activity).options(joinedload(Activity.organizer)).filter(Activity.id == id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    if activity.status != ActivityStatus.RECRUITING and activity.status != ActivityStatus.ONGOING and activity.status != ActivityStatus.ENDED:
        activity.status = ActivityStatus.RECRUITING

        if activity.organizer:
            activity.organizer.points += 10

            create_notification(
                db=db,
                user_id=activity.organizer_id,
                type=NotificationType.ACTIVITY_APPROVAL,
                content=f"恭喜！你发布的活动 '{activity.title}' 已通过审核。",
                target_id=activity.id,
                target_type="activity"
            )

    db.commit()
    db.refresh(activity)
    return activity

@router.put("/activities/{id}/reject", response_model=schemas_activity.Activity)
def reject_activity(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    activity = db.query(Activity).options(joinedload(Activity.organizer)).filter(Activity.id == id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")

    activity.status = ActivityStatus.REJECTED

    create_notification(
        db=db,
        user_id=activity.organizer_id,
        type=NotificationType.ACTIVITY_REJECTION,
        content=f"很抱歉，你发布的活动 '{activity.title}' 未通过审核。",
        target_id=activity.id,
        target_type="activity"
    )

    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/activities/{id}")
def delete_admin_activity(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    activity = db.query(Activity).filter(Activity.id == id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="未找到该活动")
    db.delete(activity)
    db.commit()
    return {"id": id, "message": "Deleted successfully"}

@router.get("/posts", response_model=List[schemas_post.Post])
def get_admin_posts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    query = db.query(Post)
    if search:
        query = query.filter(
            (Post.title.ilike(f"%{search}%")) | 
            (Post.content.ilike(f"%{search}%"))
        )
    return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

@router.delete("/posts/{id}")
def delete_admin_post(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="未找到该帖子")
    db.delete(post)
    db.commit()
    return {"id": id, "message": "Deleted successfully"}

@router.get("/comments", response_model=List[schemas_comment.Comment])
def get_admin_comments(
    db: Session = Depends(deps.get_db),
    post_id: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    query = db.query(Comment).options(joinedload(Comment.author))
    if post_id:
        query = query.filter(Comment.post_id == post_id)
    return query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()

@router.delete("/comments/{id}")
def delete_admin_comment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user = Depends(deps.get_current_active_superuser),
) -> Any:

    comment = db.query(Comment).filter(Comment.id == id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="未找到该评论")
    db.delete(comment)
    db.commit()
    return {"id": id, "message": "Deleted successfully"}