from sqlalchemy.orm import Session
from app.models.mistake import Mistake
from app.schemas.mistake import MistakeCreate, MistakeUpdate

def get_mistake(db: Session, mistake_id: int):
    return db.query(Mistake).filter(Mistake.id == mistake_id).first()

def get_mistakes_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Mistake).filter(Mistake.user_id == user_id).order_by(Mistake.created_at.desc()).offset(skip).limit(limit).all()

def create_mistake(db: Session, mistake: MistakeCreate, user_id: int):
    db_mistake = Mistake(
        **mistake.model_dump(),
        user_id=user_id
    )
    db.add(db_mistake)
    db.commit()
    db.refresh(db_mistake)
    return db_mistake

def update_mistake(db: Session, db_mistake: Mistake, mistake_update: MistakeUpdate):
    update_data = mistake_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_mistake, field, value)
    db.add(db_mistake)
    db.commit()
    db.refresh(db_mistake)
    return db_mistake