"""文档元数据模型"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Document(Base):
    """知识文档元数据（向量数据单独存 Milvus）"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 原始文件名
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 文件格式：pdf / docx / xlsx / md
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 文件大小（字节）
    size: Mapped[int] = mapped_column(Integer, default=0)
    # 切分后的块数量
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    # 所属分类ID（可空）
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 状态：processing 处理中 / done 已完成 / failed 失败
    status: Mapped[str] = mapped_column(String(20), default="processing")
    # 上传时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
