"""会话接口（需登录）"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.schemas.session import MessageOut, SessionOut
from app.services import session_service

router = APIRouter(tags=["会话"])


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """会话列表"""
    sessions = session_service.list_sessions(db)
    data = [SessionOut.model_validate(s).model_dump() for s in sessions]
    return {"code": 200, "message": "ok", "data": data}


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """某会话的消息历史"""
    msgs = session_service.get_history(db, session_id, limit=100)
    data = [MessageOut.model_validate(m).model_dump() for m in msgs]
    return {"code": 200, "message": "ok", "data": data}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """删除会话"""
    try:
        session_service.delete_session(db, session_id)
        return {"code": 200, "message": "删除成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除失败: {e}", "data": None}
