from sqlalchemy.orm import Session, joinedload
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate

def get_document(db: Session, document_id: int):
    return db.query(Document).options(joinedload(Document.user), joinedload(Document.chunks)).filter(Document.id == document_id).first()

def get_documents_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Document).options(joinedload(Document.user)).filter(Document.user_id == user_id, Document.group_id == None).offset(skip).limit(limit).all()

def get_documents_by_group(db: Session, group_id: int, skip: int = 0, limit: int = 100):
    return db.query(Document).options(joinedload(Document.user)).filter(Document.group_id == group_id).offset(skip).limit(limit).all()

def create_document(db: Session, document: DocumentCreate, user_id: int):
    db_document = Document(
        **document.model_dump(),
        user_id=user_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document(db: Session, db_document: Document, document_update: DocumentUpdate):
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document