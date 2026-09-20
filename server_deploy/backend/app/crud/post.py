from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100, category: str = None):
    query = db.query(Post)
    if category:
        query = query.filter(Post.category == category)
    else:

        query = query.filter(Post.category.notin_(['learning_square', 'activity']))
    return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, user_id: int):
    db_post = Post(
        title=post.title,
        content=post.content,
        category=post.category,
        tags=post.tags,
        author_id=user_id
    )
    db.add(db_post)

    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.points += 5

    db.commit()
    db.refresh(db_post)
    return db_post

def update_post(db: Session, db_post: Post, post_update: PostUpdate):
    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, db_post: Post):
    db.delete(db_post)
    db.commit()
    return db_post