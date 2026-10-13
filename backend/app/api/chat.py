"""智能问答接口（需登录）"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services import chat_service

router = APIRouter(tags=["智能问答"])


@router.post("/chat/stream")
def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """流式问答（SSE，答案逐字输出）"""
    return StreamingResponse(
        chat_service.ask_stream(db, req.question, req.session_id),
        media_type="text/event-stream",
    )


@router.post("/chat")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """提问并获取带引用来源的答案"""
    try:
        resp = chat_service.ask(db, req.question, req.session_id)
        return {"code": 200, "message": "ok", "data": resp.model_dump()}
    except Exception as e:
        return {"code": 500, "message": f"问答失败: {e}", "data": None}
