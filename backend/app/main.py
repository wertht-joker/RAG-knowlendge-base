"""FastAPI 主入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, categories, chat, documents, feedback, health, sessions
from app.core.config import settings
from app.models.database import init_db


def create_default_admin():
    """创建默认管理员账号（admin / admin123），方便首次登录管理"""
    from app.models.database import SessionLocal
    from app.models.user import User
    from app.utils import security

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                password_hash=security.hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("已创建默认管理员账号: admin / admin123")
    finally:
        db.close()


def seed_demo_orders():
    """写入演示订单（仅当订单表为空时），供 Agent 的订单查询工具演示"""
    from app.models.database import SessionLocal
    from app.models.order import Order

    db = SessionLocal()
    try:
        if db.query(Order).first():
            return
        demo = [
            Order(
                order_no="DD20260901001",
                product_name="智能空气净化器",
                amount=899.0,
                status="已发货",
                logistics="顺丰速运 SF1234567890",
            ),
            Order(
                order_no="DD20260912002",
                product_name="智能音箱",
                amount=299.0,
                status="已完成",
                logistics="京东物流 JD9876543210",
            ),
            Order(
                order_no="DD20260920003",
                product_name="智能台灯",
                amount=159.0,
                status="待付款",
                logistics="",
            ),
        ]
        db.add_all(demo)
        db.commit()
        print("已写入演示订单数据，共 3 条")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表 + 创建默认管理员 + 写入演示订单"""
    init_db()
    create_default_admin()
    seed_demo_orders()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="企业客服知识库系统（RAG 智能问答）",
    lifespan=lifespan,
)

# CORS：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")


@app.get("/", tags=["根路由"])
def root():
    """根路径：返回服务概览"""
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
