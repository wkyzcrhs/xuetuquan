import os
import shutil
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.mistake import Mistake, MistakeCreate
from app.crud import mistake as crud_mistake
from app.models.user import User
from app.core.mistake_analyzer import analyze_mistake

router = APIRouter()

UPLOAD_DIR = "uploads/mistakes"

@router.post("/", response_model=Mistake)
def create_mistake(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    subject: str = Form(...),
    raw_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks
) -> Any:

    image_url = None
    if file:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
        file_location = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        image_url = file_location

    mistake_in = MistakeCreate(
        subject=subject,
        raw_text=raw_text,
        image_url=image_url
    )

    mistake = crud_mistake.create_mistake(db=db, mistake=mistake_in, user_id=current_user.id)

    background_tasks.add_task(analyze_mistake, db, mistake.id)

    return mistake

@router.get("/", response_model=List[Mistake])
def read_mistakes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    mistakes = crud_mistake.get_mistakes_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return mistakes

@router.get("/{mistake_id}", response_model=Mistake)
def read_mistake(
    *,
    db: Session = Depends(deps.get_db),
    mistake_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    mistake = crud_mistake.get_mistake(db=db, mistake_id=mistake_id)
    if not mistake:
        raise HTTPException(status_code=404, detail="未找到该错题")
    if mistake.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="权限不足")
    return mistake