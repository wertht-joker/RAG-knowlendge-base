"""反馈接口（需登录）"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.schemas.feedback import FeedbackCreate
from app.services import feedback_service

router = APIRouter(tags=["反馈"])


@router.post("/feedback")
def add_feedback(
    req: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """回答反馈（type: up 有用 / down 无用）"""
    try:
        feedback_service.add_feedback(db, req.message_id, req.type)
        return {"code": 200, "message": "反馈成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"反馈失败: {e}", "data": None}


@router.get("/feedback/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """反馈统计"""
    return {"code": 200, "message": "ok", "data": feedback_service.stats(db)}
