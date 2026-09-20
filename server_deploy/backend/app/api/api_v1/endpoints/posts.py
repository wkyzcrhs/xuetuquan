from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.post import Post, PostCreate, PostUpdate
from app.crud import post as crud_post
from app.models.user import User
from app.crud.notification import create_notification
from app.models.notification import NotificationType

router = APIRouter()

@router.post("/", response_model=Post)
def create_post(
    *,
    db: Session = Depends(deps.get_db),
    post_in: PostCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    post = crud_post.create_post(db=db, post=post_in, user_id=current_user.id)
    return post

@router.get("/recommended", response_model=List[Post])
def read_recommended_posts(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="按分类筛选推荐"),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
) -> Any:

    from app.models.post import Post as PostModel
    from sqlalchemy import or_

    recommended = []

    base_query = db.query(PostModel)
    if category:
        base_query = base_query.filter(PostModel.category == category)
    else:

        base_query = base_query.filter(PostModel.category.notin_(['learning_square']))

    if current_user and current_user.preferences:
        prefs = [p.strip() for p in current_user.preferences.split(',') if p.strip()]
        if prefs:
            conditions = []
            for pref in prefs:
                conditions.append(PostModel.title.ilike(f"%{pref}%"))
                conditions.append(PostModel.content.ilike(f"%{pref}%"))
                if hasattr(PostModel, 'tags'):
                    conditions.append(PostModel.tags.ilike(f"%{pref}%"))

            matched_posts = base_query.filter(or_(*conditions)).order_by(PostModel.like_count.desc()).limit(5).all()
            recommended.extend(matched_posts)

    if len(recommended) < 5:
        needed = 5 - len(recommended)
        recommended_ids = [p.id for p in recommended]

        hot_query = base_query
        if recommended_ids:
            hot_query = hot_query.filter(~PostModel.id.in_(recommended_ids))

        hot_posts = hot_query.order_by(PostModel.like_count.desc()).limit(needed).all()
        recommended.extend(hot_posts)

    return recommended

@router.get("/", response_model=List[Post])
def read_posts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="按分类筛选"),
    user_id: Optional[int] = Query(None, description="按作者筛选"),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
) -> Any:

    posts = crud_post.get_posts(db=db, skip=skip, limit=limit, category=category)

    from app.models.post import PostLike
    for post in posts:
        like = db.query(PostLike).filter(PostLike.user_id == current_user.id, PostLike.post_id == post.id).first()
        post.is_liked = bool(like)

    return posts

@router.get("/{post_id}", response_model=Post)
def read_post(
    *,
    db: Session = Depends(deps.get_db),
    post_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    post = crud_post.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="未找到该帖子")

    from app.models.post import PostLike
    like = db.query(PostLike).filter(PostLike.user_id == current_user.id, PostLike.post_id == post.id).first()
    post.is_liked = bool(like)

    return post

@router.put("/{post_id}", response_model=Post)
def update_post(
    *,
    db: Session = Depends(deps.get_db),
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    post = crud_post.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="未找到该帖子")
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="权限不足")
    post = crud_post.update_post(db=db, db_post=post, post_update=post_in)
    return post

@router.post("/{post_id}/like", response_model=Post)
def like_post(
    *,
    db: Session = Depends(deps.get_db),
    post_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    post = crud_post.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="未找到该帖子")

    from app.models.post import PostLike
    like = db.query(PostLike).filter(PostLike.user_id == current_user.id, PostLike.post_id == post_id).first()

    if like:

        db.delete(like)
        post.like_count = max(0, post.like_count - 1)

        current_user.points = max(0, current_user.points - 1)
        if post.author_id != current_user.id:
            author = db.query(User).filter(User.id == post.author_id).first()
            if author:
                author.points = max(0, author.points - 1)

        db.commit()
        db.refresh(post)
        post.is_liked = False
    else:

        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        post.like_count += 1

        current_user.points += 1

        if post.author_id != current_user.id:
            author = db.query(User).filter(User.id == post.author_id).first()
            if author:
                author.points += 1

                create_notification(
                    db=db,
                    user_id=author.id,
                    sender_id=current_user.id,
                    type=NotificationType.LIKE,
                    content=f"{current_user.username} 点赞了你的帖子: {post.title}",
                    target_id=post.id,
                    target_type="post"
                )

        db.commit()
        db.refresh(post)
        post.is_liked = True

    return post

@router.delete("/{post_id}")
def delete_post(
    *,
    db: Session = Depends(deps.get_db),
    post_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    post = crud_post.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="未找到该帖子")
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="权限不足")
    crud_post.delete_post(db=db, db_post=post)
    return {"id": post_id, "message": "Deleted successfully"}