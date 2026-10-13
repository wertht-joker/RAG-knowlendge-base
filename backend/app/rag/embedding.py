"""本地 Embedding：使用 BGE 模型做文本向量化（离线，免 API）"""
import os

# 国内访问 huggingface.co 会超时，走镜像加速下载
# 用 setdefault 保证：用户若已设 HF_ENDPOINT 则尊重其配置
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import SentenceTransformer

from app.core.config import settings

# 模块级缓存，避免每次请求都重新加载模型（模型加载较慢）
_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # 首次调用会从 HuggingFace 下载模型（约 400MB），国内可设 HF_ENDPOINT 镜像
        _model = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device,
        )
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """批量生成向量（归一化，便于用余弦相似度检索）"""
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()
