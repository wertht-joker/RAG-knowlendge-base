"""注册/登录接口"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.utils import security

router = APIRouter(tags=["认证"])


@router.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册（普通用户）"""
    if not req.username or not req.password:
        return {"code": 400, "message": "用户名和密码不能为空", "data": None}
    if db.query(User).filter(User.username == req.username).first():
        return {"code": 500, "message": "用户名已存在", "data": None}

    user = User(
        username=req.username,
        password_hash=security.hash_password(req.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"code": 200, "message": "注册成功", "data": UserOut.model_validate(user).model_dump()}


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """登录，返回 JWT"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not security.verify_password(req.password, user.password_hash):
        return {"code": 401, "message": "用户名或密码错误", "data": None}

    token = security.create_token(user.id, user.role)
    data = TokenResponse(token=token, user=UserOut.model_validate(user)).model_dump()
    return {"code": 200, "message": "登录成功", "data": data}
