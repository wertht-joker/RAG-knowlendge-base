"""全局配置管理：从 .env / 环境变量读取配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 应用 =====
    app_name: str = "企业客服知识库"

    # ===== DeepSeek 对话模型 =====
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ===== Milvus 向量库 =====
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "kb_documents"

    # ===== 本地 Embedding 模型 =====
    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    embedding_device: str = "cpu"

    # ===== 数据库 =====
    database_url: str = "sqlite:///./kb.db"

    # ===== JWT =====
    jwt_secret: str = "kb-jwt-secret-please-change-in-production-0123456789"
    jwt_expire_hours: int = 24

    # ===== 检索参数 =====
    top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 50
    # 向量检索先召回的数量，再交给 reranker 精排
    retrieve_top_k: int = 20

    # ===== Rerank 模型 =====
    reranker_model: str = "BAAI/bge-reranker-base"

    # ===== Agent 参数 =====
    # 工具调用循环的最大轮数，防止模型陷入无限调用
    agent_max_steps: int = 5


# 全局单例，供各模块 import
settings = Settings()
