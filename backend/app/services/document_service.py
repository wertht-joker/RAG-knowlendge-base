"""文档管理服务：编排「上传 → 解析 → 切分 → 向量化 → 入库」全流程"""
import os
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.rag import embedding, loader, splitter, vector_store

# 上传文件保存目录（相对 backend 运行目录）
UPLOAD_DIR = "uploads"

# 支持的文件类型
SUPPORTED_TYPES = {"pdf", "docx", "xlsx", "md", "txt"}


def _file_type(filename: str) -> str:
    """根据扩展名返回文件类型"""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _save_file(file: UploadFile) -> tuple[str, int]:
    """保存上传文件，返回 (路径, 大小)"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, file.filename)
    content = file.file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path, len(content)


def upload_document(db: Session, file: UploadFile) -> Document:
    """完整入库流程"""
    file_type = _file_type(file.filename)
    if file_type not in SUPPORTED_TYPES:
        raise ValueError(f"不支持的文件格式: {file_type}，仅支持 {SUPPORTED_TYPES}")

    # 1. 先写元数据（状态 processing）
    doc = Document(
        name=file.filename,
        type=file_type,
        size=0,
        chunk_count=0,
        status="processing",
        created_at=datetime.now(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # 2. 保存文件
        path, size = _save_file(file)
        doc.size = size
        db.commit()

        # 3. 解析 → 文本
        text = loader.load_document(path, file_type)
        if not text.strip():
            raise ValueError("文档解析结果为空，无法入库")

        # 4. 切分 → 块
        chunks = splitter.split_text(text)
        if not chunks:
            raise ValueError("文档切分后没有内容")

        # 5. 向量化
        vectors = embedding.embed(chunks)

        # 6. 插入 Milvus
        vector_store.insert_chunks(doc.id, chunks, vectors)

        # 7. 更新元数据为完成态
        doc.chunk_count = len(chunks)
        doc.status = "done"
        db.commit()
        db.refresh(doc)
    except Exception as e:
        # 失败：标记状态，并向上抛出
        doc.status = "failed"
        db.commit()
        db.refresh(doc)
        raise e

    return doc


def list_documents(db: Session, keyword: str | None = None) -> list[Document]:
    """文档列表（按上传时间倒序，支持按名称关键词搜索）"""
    query = db.query(Document)
    if keyword:
        query = query.filter(Document.name.like(f"%{keyword}%"))
    return query.order_by(Document.created_at.desc()).all()


def delete_document(db: Session, doc_id: int) -> None:
    """删除文档（元数据 + Milvus 向量）"""
    doc = db.get(Document, doc_id)
    if not doc:
        raise ValueError("文档不存在")

    # 先删 Milvus 向量（Milvus 不可用时仍要能删元数据）
    try:
        vector_store.delete_by_doc_id(doc_id)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
