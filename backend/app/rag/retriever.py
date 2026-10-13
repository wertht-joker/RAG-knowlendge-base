"""语义检索：向量召回 + Rerank 精排"""
from app.core.config import settings
from app.rag import embedding, reranker, vector_store

# BGE 中文模型的 query 前缀，提升召回
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："


def search(query: str, top_k: int | None = None) -> list[dict]:
    """检索与问题最相关的文档块（先向量召回 N 条，再 rerank 精排取 top_k）"""
    k = top_k or settings.top_k

    # 1. 问题向量化
    query_vector = embedding.embed([QUERY_PREFIX + query])[0]

    # 2. 向量召回（先多召回一些，交给 reranker）
    collection = vector_store.init_collection()
    collection.load()
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}
    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param=search_params,
        limit=settings.retrieve_top_k,
        output_fields=["text", "doc_id", "chunk_index"],
    )

    hits = []
    for hit in results[0]:
        hits.append({
            "text": hit.entity.get("text"),
            "doc_id": hit.entity.get("doc_id"),
            "chunk_index": hit.entity.get("chunk_index"),
            "score": float(hit.score),
        })

    if not hits:
        return []

    # 3. Rerank 精排：用 reranker 对召回结果重新打分，取前 k 条
    passages = [h["text"] for h in hits]
    try:
        ranked = reranker.rerank(query, passages)
        top_hits = []
        for idx, score in ranked[:k]:
            h = dict(hits[idx])
            h["score"] = round(float(score), 4)
            top_hits.append(h)
        return top_hits
    except Exception:
        # reranker 不可用则降级为向量检索结果
        return hits[:k]
