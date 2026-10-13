"""数据库连接与会话管理（SQLAlchemy + SQLite）"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite 需要 check_same_thread=False，否则 FastAPI 多线程下会报错
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """ORM 基类，所有模型继承它"""
    pass


def init_db():
    """创建所有表（启动时调用一次）"""
    # 导入模型，确保它们注册到 Base.metadata
    from app.models import category, document, feedback, order, session, user  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖：提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
