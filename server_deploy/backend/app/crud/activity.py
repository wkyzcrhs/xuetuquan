from sqlalchemy.orm import Session, joinedload
from app.models.activity import Activity, ActivityStatus
from app.schemas.activity import ActivityCreate, ActivityUpdate
from datetime import datetime
from typing import Optional

def get_activity(db: Session, activity_id: int):
    return db.query(Activity).options(joinedload(Activity.organizer)).filter(Activity.id == activity_id).first()

def get_activities(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    is_superuser: bool = False,
    only_public: bool = False
):
    query = db.query(Activity).options(joinedload(Activity.organizer))

    if category:
        query = query.filter(Activity.category == category)

    if status:
        query = query.filter(Activity.status == status)
    elif not is_superuser:

        from sqlalchemy import or_

        if only_public or not user_id:

            query = query.filter(Activity.status.in_([ActivityStatus.RECRUITING, ActivityStatus.ONGOING, ActivityStatus.ENDED]))
        else:

            query = query.filter(
                or_(
                    Activity.status.in_([ActivityStatus.RECRUITING, ActivityStatus.ONGOING, ActivityStatus.ENDED]),
                    Activity.organizer_id == user_id
                )
            )

    return query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()

def create_activity(db: Session, activity: ActivityCreate, user_id: int):

    db_activity = Activity(
        **activity.model_dump(),
        organizer_id=user_id,
        status=ActivityStatus.PENDING,
        created_at=datetime.utcnow()  
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def update_activity(db: Session, db_activity: Activity, activity_update: ActivityUpdate):
    update_data = activity_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_activity, field, value)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity