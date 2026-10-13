"""文档管理接口（需管理员权限）"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.models.database import get_db
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import document_service

router = APIRouter(tags=["文档管理"])


@router.post("/documents/upload")
def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """上传文档并入库（管理员）"""
    try:
        doc = document_service.upload_document(db, file)
        return {"code": 200, "message": "文档入库成功", "data": DocumentOut.model_validate(doc).model_dump()}
    except Exception as e:
        return {"code": 500, "message": f"文档入库失败: {e}", "data": None}


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
    keyword: str = "",
):
    """文档列表，支持关键词搜索（管理员）"""
    docs = document_service.list_documents(db, keyword or None)
    data = [DocumentOut.model_validate(d).model_dump() for d in docs]
    return {"code": 200, "message": "ok", "data": data}


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """删除文档（管理员）"""
    try:
        document_service.delete_document(db, doc_id)
        return {"code": 200, "message": "删除成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除失败: {e}", "data": None}
