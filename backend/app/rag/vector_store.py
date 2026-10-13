"""Milvus 向量库操作：建集合、插入块、删除块"""
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.core.config import settings

# BGE-base-zh-v1.5 的向量维度
EMBEDDING_DIM = 768


def _connect():
    """连接 Milvus（默认别名 default）"""
    connections.connect(
        alias="default",
        host=settings.milvus_host,
        port=settings.milvus_port,
    )


def init_collection() -> Collection:
    """初始化集合：不存在则创建并建索引，存在则直接返回"""
    _connect()
    name = settings.milvus_collection
    if utility.has_collection(name):
        return Collection(name)

    # 定义字段：id 主键自增，text 存原文块，doc_id 关联文档，vector 存向量
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="doc_id", dtype=DataType.INT64),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
    ]
    schema = CollectionSchema(fields, description="知识库文档块")
    collection = Collection(name, schema=schema)

    # 为向量字段建索引（余弦相似度 + IVF_FLAT）
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="vector", index_params=index_params)
    return collection


def insert_chunks(doc_id: int, chunks: list[str], vectors: list[list[float]]):
    """把一个文档的所有块插入 Milvus"""
    collection = init_collection()
    data = [
        chunks,                          # text
        [doc_id] * len(chunks),          # doc_id
        list(range(len(chunks))),        # chunk_index
        vectors,                         # vector
    ]
    collection.insert(data)
    collection.flush()


def delete_by_doc_id(doc_id: int):
    """删除某个文档的所有向量块"""
    collection = init_collection()
    collection.delete(expr=f"doc_id == {doc_id}")
    collection.flush()
