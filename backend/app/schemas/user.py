"""用户认证相关模型"""
from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class TokenResponse(BaseModel):
    token: str
    user: UserOut
