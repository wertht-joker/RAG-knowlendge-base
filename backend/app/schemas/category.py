"""分类请求/响应模型"""
from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    """新增/修改分类"""
    name: str
    parent_id: int = 0
    sort: int = 0


class CategoryOut(BaseModel):
    """分类响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int
    sort: int
