from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api import deps
from app.models.learning_plan import LearningPlan, PlanStatus
from app.models.daily_task import DailyTask, TaskType
from app.models.mistake import Mistake
from app.models.user import User
from app.core.ai_client import ai_client
from pydantic import BaseModel

router = APIRouter()

class PlanCreate(BaseModel):
    title: str
    description: str

class TaskUpdate(BaseModel):
    is_completed: bool

class PlanResponse(BaseModel):
    id: int
    title: str
    description: str
    content: str
    status: str
    created_at: datetime
    progress: float  

class TaskResponse(BaseModel):
    id: int
    plan_id: int
    title: str
    content: Optional[str]
    type: str
    is_completed: bool
    scheduled_date: Optional[datetime]

@router.post("/", response_model=PlanResponse)
def create_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: PlanCreate,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks
) -> Any:

    ai_content = ai_client.generate_plan(plan_in.description)

    db_plan = LearningPlan(
        title=plan_in.title,
        description=plan_in.description,
        content=ai_content,
        user_id=current_user.id
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    import json
    tasks_data = ai_client.generate_daily_tasks(ai_content, day_offset=0)
    for task in tasks_data:
        content = task.get("content", "")
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
        db_task = DailyTask(
            plan_id=db_plan.id,
            title=task.get("title", "未命名任务"),
            content=content,
            type=task.get("type", "reading"),
            scheduled_date=datetime.now()
        )
        db.add(db_task)
    db.commit()

    return PlanResponse(
        id=db_plan.id,
        title=db_plan.title,
        description=db_plan.description,
        content=db_plan.content,
        status=db_plan.status,
        created_at=db_plan.created_at,
        progress=0.0
    )

@router.get("/active", response_model=Optional[PlanResponse])
def get_active_plan(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user.id,
        LearningPlan.status == PlanStatus.ACTIVE
    ).first()

    if not plan:
        return None

    total_tasks = db.query(DailyTask).filter(DailyTask.plan_id == plan.id).count()
    completed_tasks = db.query(DailyTask).filter(
        DailyTask.plan_id == plan.id,
        DailyTask.is_completed == True
    ).count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    return PlanResponse(
        id=plan.id,
        title=plan.title,
        description=plan.description,
        content=plan.content,
        status=plan.status,
        created_at=plan.created_at,
        progress=progress
    )

@router.post("/active/abandon")
def abandon_active_plan(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user.id,
        LearningPlan.status == PlanStatus.ACTIVE
    ).first()

    if plan:
        plan.status = PlanStatus.ARCHIVED
        db.commit()

    return {"status": "success"}

@router.get("/{plan_id}/tasks/today", response_model=List[TaskResponse])
def get_today_tasks(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id, LearningPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="未找到该计划")

    from datetime import date
    import json
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    tasks = db.query(DailyTask).filter(
        DailyTask.plan_id == plan_id,
        DailyTask.scheduled_date >= today_start,
        DailyTask.scheduled_date <= today_end
    ).order_by(DailyTask.id.asc()).all()

    if not tasks:

        day_offset = (date.today() - plan.created_at.date()).days
        if day_offset < 0:
            day_offset = 0

        tasks_data = ai_client.generate_daily_tasks(plan.content, day_offset=day_offset)
        new_tasks = []
        for task_data in tasks_data:
            content = task_data.get("content", "")
            if isinstance(content, dict) or isinstance(content, list):
                content = json.dumps(content, ensure_ascii=False)
            db_task = DailyTask(
                plan_id=plan.id,
                title=task_data.get("title", "未命名任务"),
                content=content,
                type=task_data.get("type", "reading"),
                scheduled_date=datetime.now()
            )
            db.add(db_task)
            new_tasks.append(db_task)
        db.commit()
        for task in new_tasks:
            db.refresh(task)
        tasks = new_tasks

    return tasks

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="未找到该任务")

    task.is_completed = task_update.is_completed
    db.commit()
    db.refresh(task)
    return task

class WrongQuestionCreate(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    explanation: str

class QuizResultCreate(BaseModel):
    is_correct: bool
    wrong_questions: Optional[List[WrongQuestionCreate]] = None

@router.post("/tasks/{task_id}/quiz_result")
def submit_quiz_result(
    task_id: int,
    result: QuizResultCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task or task.type != TaskType.QUIZ:
        raise HTTPException(status_code=400, detail="无效的测验任务")

    task.is_completed = True

    mistakes_added = False
    if not result.is_correct and result.wrong_questions:

        for wq in result.wrong_questions:
            mistake = Mistake(
                user_id=current_user.id,
                subject="AI 学习计划", 
                raw_text=f"题目：{wq.question}\n你的答案：{wq.user_answer}\n正确答案：{wq.correct_answer}",
                ai_analysis=wq.explanation or "自动添加的错题，请稍后查看 AI 详细解析。"
            )
            db.add(mistake)
        mistakes_added = True

    db.commit()
    return {"status": "success", "mistake_added": mistakes_added}