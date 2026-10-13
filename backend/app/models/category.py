"""知识分类模型"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Category(Base):
    """知识分类（支持二级：parent_id=0 为一级）"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 父分类ID，0 表示一级分类
    parent_id: Mapped[int] = mapped_column(Integer, default=0)
    # 排序值
    sort: Mapped[int] = mapped_column(Integer, default=0)
