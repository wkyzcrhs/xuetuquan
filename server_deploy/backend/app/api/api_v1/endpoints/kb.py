import os
import shutil
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.document import Document
from app.crud import document as crud_document
from app.schemas.document import DocumentCreate
from app.models.user import User
from app.core.rag_processor import process_document
from app.schemas.query import QueryRequest, QueryResponse
from app.core.chroma_client import chroma_client
from app.core.ai_client import ai_client
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistoryCreate, ChatHistoryResponse
from sqlalchemy import desc
from app.crud.notification import create_notification
from app.models.notification import NotificationType
from app.models.group import Group

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.post("/upload", response_model=Document)
def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None), 
    group_id: Optional[int] = Form(None), 
    background_tasks: BackgroundTasks
) -> Any:

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    safe_filename = file.filename

    file_location = os.path.join(UPLOAD_DIR, f"{current_user.id}_{safe_filename}")
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        print(f"文件保存错误: {e}")
        raise HTTPException(status_code=500, detail="保存文件失败")

    doc_title = title if title else file.filename
    doc_in = DocumentCreate(
        title=doc_title,
        file_url=file_location,
        group_id=group_id
    )
    document = crud_document.create_document(db=db, document=doc_in, user_id=current_user.id)

    background_tasks.add_task(process_document, document.id)

    if group_id:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            for member in group.membership:
                if member.user_id != current_user.id and member.status == "approved":
                    create_notification(
                        db=db,
                        user_id=member.user_id,
                        sender_id=current_user.id,
                        type=NotificationType.GROUP_FILE_UPLOAD,
                        content=f"{current_user.username} 在小组 '{group.name}' 中上传了新文件: {doc_title}",
                        target_id=group.id,
                        target_type="group"
                    )

            if group.owner_id != current_user.id:
                create_notification(
                    db=db,
                    user_id=group.owner_id,
                    sender_id=current_user.id,
                    type=NotificationType.GROUP_FILE_UPLOAD,
                    content=f"{current_user.username} 在小组 '{group.name}' 中上传了新文件: {doc_title}",
                    target_id=group.id,
                    target_type="group"
                )

    return document

@router.get("/", response_model=List[Document])
def read_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    group_id: Optional[int] = None, 
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    if group_id:
        documents = crud_document.get_documents_by_group(
            db=db, group_id=group_id, skip=skip, limit=limit
        )
    else:
        documents = crud_document.get_documents_by_user(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
    return documents

@router.get("/{document_id}/content")
def get_document_content(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    document = crud_document.get_document(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="未找到该文档")

    if document.user_id != current_user.id:
        if not document.group_id:
            raise HTTPException(status_code=403, detail="权限不足")
        from app.crud import group as crud_group
        group = crud_group.get_group(db, id=document.group_id)
        if not group:
            raise HTTPException(status_code=404, detail="未找到该群组")

        if current_user.id != group.owner_id and current_user.id not in [m.id for m in group.members]:
            raise HTTPException(status_code=403, detail="不是该群组的成员")

    content = ""
    if document.chunks:
        content = "\n\n".join([chunk.content for chunk in document.chunks])
    elif document.status == "processing":
        content = "文档正在处理中，请稍后再试..."
    else:

        try:
            if document.file_url.lower().endswith(('.doc', '.docx')):
                try:
                    import docx2txt
                    content = docx2txt.process(document.file_url)
                except ImportError:
                    content = "无法解析 Word 文档，请确保已安装 docx2txt"
            else:
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(document.file_url, encoding="utf-8")
                docs = loader.load()
                content = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"读取文件后备方案出错: {e}")
            content = "无文本内容或文件已丢失"

    return {"content": content}

@router.post("/query_stream")
def query_knowledge_base_stream(
    *,
    db: Session = Depends(deps.get_db),
    query_in: QueryRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    if query_in.group_id:

        from app.crud import group as crud_group
        group = crud_group.get_group(db, id=query_in.group_id)
        if not group or current_user not in group.members:
            raise HTTPException(status_code=403, detail="不是该群组的成员")

        results = chroma_client.query_documents(
            query_text=query_in.query,
            group_id=query_in.group_id,
            n_results=3
        )
    else:
        results = chroma_client.query_documents(
            query_text=query_in.query,
            user_id=current_user.id,
            n_results=3
        )

    documents = results['documents'][0] if results['documents'] else []

    if not documents:
        context = "无相关上下文。"
        sources = []
    else:
        context = "\n\n".join(documents)
        sources = [doc[:50] + "..." for doc in documents]

    def generate():

        yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"

        for chunk in ai_client.get_answer_stream(query=query_in.query, context=context):
            yield json.dumps({"type": "chunk", "data": chunk}, ensure_ascii=False) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@router.post("/chat_history", response_model=ChatHistoryResponse)
def save_chat_history(
    *,
    db: Session = Depends(deps.get_db),
    chat_in: ChatHistoryCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    sources_str = json.dumps(chat_in.sources, ensure_ascii=False) if chat_in.sources else "[]"
    chat_record = ChatHistory(
        user_id=current_user.id,
        group_id=chat_in.group_id,
        query=chat_in.query,
        answer=chat_in.answer,
        sources=sources_str
    )
    db.add(chat_record)

    current_user.ai_chat_count += 1

    db.commit()
    db.refresh(chat_record)
    return chat_record

@router.get("/chat_history", response_model=List[ChatHistoryResponse])
def get_chat_history(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:

    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(desc(ChatHistory.created_at)).offset(skip).limit(limit).all()
    return history
