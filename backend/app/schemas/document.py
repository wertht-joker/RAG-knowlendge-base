"""文档相关请求/响应模型"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    """文档响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    size: int
    chunk_count: int
    status: str
    category_id: int | None
    created_at: datetime
