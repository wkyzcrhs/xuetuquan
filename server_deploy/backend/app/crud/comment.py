from sqlalchemy.orm import Session, joinedload
from app.models.comment import Comment
from app.schemas.comment import CommentCreate

def get_comment(db: Session, comment_id: int):
    return db.query(Comment).options(joinedload(Comment.author)).filter(Comment.id == comment_id).first()

def get_comments_by_post(db: Session, post_id: int, skip: int = 0, limit: int = 100):
    return db.query(Comment).options(joinedload(Comment.author)).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()

def create_comment(db: Session, comment: CommentCreate, user_id: int):
    db_comment = Comment(
        content=comment.content,
        post_id=comment.post_id,
        author_id=user_id
    )
    db.add(db_comment)

    from app.models.user import User
    from app.models.post import Post

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.points += 2

    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if post and post.author_id != user_id:
        author = db.query(User).filter(User.id == post.author_id).first()
        if author:
            author.points += 2

    db.commit()
    db.refresh(db_comment)
    return db_comment

def delete_comment(db: Session, db_comment: Comment):
    db.delete(db_comment)
    db.commit()
    return db_comment

def get_all_comments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Comment).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()