"""反馈服务"""
from sqlalchemy.orm import Session

from app.models.feedback import Feedback


def add_feedback(db: Session, message_id: int, feedback_type: str) -> Feedback:
    """添加反馈（up/down）"""
    if feedback_type not in ("up", "down"):
        raise ValueError("反馈类型只能是 up 或 down")
    f = Feedback(message_id=message_id, type=feedback_type)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def stats(db: Session) -> dict:
    """反馈统计"""
    up = db.query(Feedback).filter(Feedback.type == "up").count()
    down = db.query(Feedback).filter(Feedback.type == "down").count()
    return {"up": up, "down": down, "total": up + down}
