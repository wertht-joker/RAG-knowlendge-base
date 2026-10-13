"""鉴权依赖：从请求头解析 JWT，获取当前用户"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.user import User
from app.utils import security


def get_current_user(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户（未登录抛 401）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    token = authorization[7:]
    try:
        payload = security.decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """获取当前管理员（非管理员抛 403）"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
