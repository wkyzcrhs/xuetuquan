from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.chroma_client import chroma_client
from app.models.document import DocStatus
from app.crud import document as crud_document
from sqlalchemy.orm import Session
import os
import uuid

from app.db.session import SessionLocal

def process_document(document_id: int):

    db = SessionLocal()
    try:
        document = crud_document.get_document(db, document_id)
        if not document:
            return

        file_path = document.file_url
        if not os.path.exists(file_path):
            print(f"错误: 未找到文件 {file_path}")
            from app.schemas.document import DocumentUpdate
            crud_document.update_document(
                db, document, DocumentUpdate(status=DocStatus.FAILED)
            )
            return

        if file_path.lower().endswith((".doc", ".docx")):

            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(file_path)
            except ImportError:
                print("未安装 Docx2txtLoader 依赖。降级为纯文本处理。")
                loader = TextLoader(file_path, encoding="utf-8")
        else:

            loader = TextLoader(file_path, encoding="utf-8")

        docs = loader.load()
        if not docs:
            print(f"警告: 文档 {document_id} 没有可读页面/内容。")
            from app.schemas.document import DocumentUpdate
            crud_document.update_document(
                db, document, DocumentUpdate(status=DocStatus.FAILED)
            )
            return False

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.split_documents(docs)

        if not chunks:
            print(f"警告: 文档 {document_id} 分割后为空。")
            from app.schemas.document import DocumentUpdate
            crud_document.update_document(
                db, document, DocumentUpdate(status=DocStatus.FAILED)
            )
            return

        texts = [doc.page_content for doc in splits]
        metadatas = [
            {"user_id": document.user_id, "doc_id": document.id, "group_id": document.group_id if document.group_id else 0} 
            for _ in splits
        ]
        ids = [str(uuid.uuid4()) for _ in splits]

        from app.models.document import DocumentChunk
        for i, text in enumerate(texts):
            chunk = DocumentChunk(
                doc_id=document.id,
                content=text,
                vector_id=ids[i]
            )
            db.add(chunk)
        db.commit()

        chroma_client.add_documents(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        from app.schemas.document import DocumentUpdate
        crud_document.update_document(
            db, document, DocumentUpdate(status=DocStatus.COMPLETED)
        )
        try:
            print(f"文档 {document_id} 处理成功。")
        except UnicodeEncodeError as ue:
            print(f"文档 {document_id} 处理成功 (忽略 Unicode 错误)。")

    except Exception as e:
        try:
            print(f"Error processing document {document_id}: {e}")
        except UnicodeEncodeError:
            print(f"Error processing document {document_id}: {repr(e)}")

        from app.schemas.document import DocumentUpdate
        if 'document' in locals() and document:
            crud_document.update_document(
                db, document, DocumentUpdate(status=DocStatus.FAILED)
            )
    finally:
        db.close()