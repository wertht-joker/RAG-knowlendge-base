"""反馈请求模型"""
from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    """回答反馈"""
    message_id: int
    # 类型：up 有用 / down 无用
    type: str
