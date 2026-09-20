from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import comment as crud_comment
from app.schemas import comment as schemas_comment
from app.models.user import User
from app.models.post import Post
from app.crud.notification import create_notification
from app.models.notification import NotificationType

router = APIRouter()

@router.post("/", response_model=schemas_comment.Comment)
def create_comment(
    *,
    db: Session = Depends(deps.get_db),
    comment_in: schemas_comment.CommentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    comment = crud_comment.create_comment(db=db, comment=comment_in, user_id=current_user.id)

    post = db.query(Post).filter(Post.id == comment_in.post_id).first()
    if post and post.author_id != current_user.id:
        create_notification(
            db=db,
            user_id=post.author_id,
            sender_id=current_user.id,
            type=NotificationType.COMMENT,
            content=f"{current_user.username} 评论了你的帖子: {post.title}",
            target_id=post.id,
            target_type="post"
        )

    return comment

@router.get("/", response_model=List[schemas_comment.Comment])
def read_comments(
    db: Session = Depends(deps.get_db),
    post_id: int = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:

    if post_id:
        comments = crud_comment.get_comments_by_post(db=db, post_id=post_id, skip=skip, limit=limit)
    else:

        comments = crud_comment.get_all_comments(db=db, skip=skip, limit=limit)
    return comments

@router.delete("/{id}")
def delete_comment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    comment = crud_comment.get_comment(db=db, comment_id=id)
    if not comment:
        raise HTTPException(status_code=404, detail="未找到该评论")
    if not deps.is_superuser(current_user) and (comment.author_id != current_user.id):
        raise HTTPException(status_code=400, detail="权限不足")
    crud_comment.delete_comment(db=db, db_comment=comment)
    return {"id": id, "message": "Deleted successfully"}