"""健康检查接口"""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["健康检查"])


@router.get("/health")
def health():
    """健康检查：返回服务状态与配置概况（用于验证骨架可跑）"""
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "app": settings.app_name,
            "deepseek_configured": bool(settings.deepseek_api_key),
            "deepseek_model": settings.deepseek_model,
            "milvus": f"{settings.milvus_host}:{settings.milvus_port}",
            "embedding_model": settings.embedding_model,
            "top_k": settings.top_k,
        },
    }
