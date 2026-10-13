"""BGE-reranker 重排序：对检索结果精排，提升答案准确率"""
import os

# 国内下载模型走镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import CrossEncoder

from app.core.config import settings

_model = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(settings.reranker_model)
    return _model


def rerank(query: str, passages: list[str]) -> list[tuple[int, float]]:
    """对候选段落重排序，返回 [(原始索引, 相关度分数)]，按分数降序"""
    if not passages:
        return []
    model = _get_model()
    pairs = [[query, p] for p in passages]
    scores = model.predict(pairs)
    # 分数归一化到 0~1，便于展示
    return sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
