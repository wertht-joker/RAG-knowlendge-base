"""会话/消息响应模型"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionOut(BaseModel):
    """会话响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime


class MessageOut(BaseModel):
    """消息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
