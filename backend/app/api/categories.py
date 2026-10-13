"""分类接口（需管理员权限）"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.models.database import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut
from app.services import category_service

router = APIRouter(tags=["知识分类"])


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), user: User = Depends(get_current_admin)):
    categories = category_service.list_categories(db)
    data = [CategoryOut.model_validate(c).model_dump() for c in categories]
    return {"code": 200, "message": "ok", "data": data}


@router.post("/categories")
def create_category(req: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_admin)):
    c = category_service.create_category(db, req.name, req.parent_id, req.sort)
    return {"code": 200, "message": "创建成功", "data": CategoryOut.model_validate(c).model_dump()}


@router.put("/categories/{category_id}")
def update_category(category_id: int, req: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_admin)):
    try:
        c = category_service.update_category(db, category_id, req.name, req.parent_id, req.sort)
        return {"code": 200, "message": "更新成功", "data": CategoryOut.model_validate(c).model_dump()}
    except Exception as e:
        return {"code": 500, "message": f"更新失败: {e}", "data": None}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_admin)):
    try:
        category_service.delete_category(db, category_id)
        return {"code": 200, "message": "删除成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除失败: {e}", "data": None}
