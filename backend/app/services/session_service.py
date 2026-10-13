"""会话管理：创建会话、保存消息、读取历史"""
from sqlalchemy.orm import Session

from app.models.session import Message, Session as SessionModel


def create_session(db: Session, title: str = "新对话") -> SessionModel:
    """新建会话"""
    s = SessionModel(title=title or "新对话")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get_session(db: Session, session_id: int) -> SessionModel | None:
    return db.get(SessionModel, session_id)


def save_message(db: Session, session_id: int, role: str, content: str) -> Message:
    """保存一条消息"""
    m = Message(session_id=session_id, role=role, content=content)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_history(db: Session, session_id: int, limit: int = 6) -> list[Message]:
    """读取最近 N 条消息（按时间正序返回，便于拼接上下文）"""
    msgs = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(msgs))


def list_sessions(db: Session) -> list[SessionModel]:
    """会话列表（按时间倒序）"""
    return db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()


def delete_session(db: Session, session_id: int) -> None:
    """删除会话及其所有消息"""
    s = db.get(SessionModel, session_id)
    if not s:
        raise ValueError("会话不存在")
    # 先删该会话的所有消息
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(s)
    db.commit()
