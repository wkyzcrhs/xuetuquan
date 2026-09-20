from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, users, kb, posts, mistakes, learning, activity, plans, comments, admin, group, notifications

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(kb.router, prefix="/kb", tags=["kb"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(mistakes.router, prefix="/mistakes", tags=["mistakes"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(activity.router, prefix="/activities", tags=["activities"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(group.router, prefix="/groups", tags=["groups"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])