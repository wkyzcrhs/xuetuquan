from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api import deps
from app.models.user import User
from app.models.document import Document
from app.models.mistake import Mistake
from app.core.ai_client import ai_client
from pydantic import BaseModel
from fastapi import HTTPException
from app.schemas.learning import LearningSummary, LearningRecord, LearningProgress

router = APIRouter()

class ExtractResponse(BaseModel):
    points: List[str]
    quiz: List[dict]

@router.post("/extract/{doc_id}", response_model=ExtractResponse)
def extract_knowledge_points(
    doc_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="未找到该文档")

    if document.user_id != current_user.id:

        pass

    try:

        content = ""
        if document.chunks:
            content = "\n\n".join([chunk.content for chunk in document.chunks])
        else:
            file_path = document.file_url

            import os
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

            if file_path.lower().endswith(".txt") or file_path.lower().endswith(".md"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif file_path.lower().endswith(('.doc', '.docx')):
                 try:
                     import docx2txt
                     content = docx2txt.process(file_path)
                     if not content.strip():
                         raise HTTPException(status_code=400, detail="Word文档内容为空")
                 except ImportError:
                     raise HTTPException(status_code=500, detail="服务器未安装 docx2txt，无法解析 Word 文档")
            else:
                raise HTTPException(status_code=400, detail="不支持的文件格式，无法提取内容")

        result = ai_client.extract_points(content)

        current_user.ai_extract_count += 1
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        try:
                print(f"读取文件出错: {e}")
        except UnicodeEncodeError:
                print(f"读取文件出错: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"处理文档失败: {type(e).__name__}")

class SaveKbRequest(BaseModel):
    points: List[str]
    title: str = None

@router.post("/save_to_kb/{doc_id}")
def save_extract_to_kb(
    doc_id: int,
    request_data: SaveKbRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    original_doc = db.query(Document).filter(Document.id == doc_id).first()
    if not original_doc:
        raise HTTPException(status_code=404, detail="未找到原始文档")

    content = "\n\n".join(request_data.points)

    import os
    import uuid

    file_name = f"extract_{uuid.uuid4()}.txt"
    upload_dir = "uploads" 
    file_path = os.path.join(upload_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    doc_title = request_data.title if request_data.title else f"提炼：{original_doc.title}"
    new_doc = Document(
        title=doc_title,
        file_url=file_path,
        user_id=current_user.id,
        status="completed" 
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    from app.core.rag_processor import process_document

    return {"status": "success", "id": new_doc.id}

from datetime import datetime, date, timedelta
from app.models.learning_plan import LearningPlan, PlanStatus
from app.models.daily_task import DailyTask

@router.get("/summary", response_model=LearningSummary)
def get_learning_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = today_start + timedelta(days=1)

    active_plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user.id,
        LearningPlan.status == PlanStatus.ACTIVE
    ).first()

    completed = 0
    total = 0

    if active_plan:

        today_tasks = db.query(DailyTask).filter(
            DailyTask.plan_id == active_plan.id
        ).order_by(desc(DailyTask.id)).limit(5).all()

        total = len(today_tasks)
        completed = sum(1 for t in today_tasks if t.is_completed)
    else:

        completed = 0
        total = 0

    recent_docs = db.query(Document).filter(Document.user_id == current_user.id)        .order_by(desc(Document.created_at)).limit(5).all()

    recent_mistakes = db.query(Mistake).filter(Mistake.user_id == current_user.id)        .order_by(desc(Mistake.created_at)).limit(5).all()

    records = []
    for doc in recent_docs:
        records.append(LearningRecord(
            id=doc.id,
            type="document",
            content=f"上传文档：{doc.title}",
            created_at=doc.created_at
        ))

    for mistake in recent_mistakes:
        records.append(LearningRecord(
            id=mistake.id,
            type="mistake",
            content=f"添加错题：{mistake.subject}",
            created_at=mistake.created_at
        ))

    records.sort(key=lambda x: x.created_at, reverse=True)
    records = records[:5]

    return LearningSummary(
        progress=LearningProgress(
            completed=completed,
            total=total,
            percentage=(completed / total) * 100 if total > 0 else 0
        ),
        recent_records=records
    )