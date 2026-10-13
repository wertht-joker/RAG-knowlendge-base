"""订单模型（供 Agent 的订单查询工具使用）"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Order(Base):
    """订单信息（演示用，真实系统由业务库提供）"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 订单号，对外查询的唯一标识
    order_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    # 商品名称
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 订单金额（元）
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    # 状态：待付款 / 待发货 / 已发货 / 已完成 / 已取消
    status: Mapped[str] = mapped_column(String(20), default="待付款")
    # 物流信息，未发货时为空
    logistics: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
