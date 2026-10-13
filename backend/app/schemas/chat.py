"""问答相关请求/响应模型"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """提问请求"""
    question: str
    # 会话ID，传入则续接多轮对话；不传则新建会话
    session_id: int | None = None


class Source(BaseModel):
    """引用来源"""
    doc_id: int
    doc_name: str
    chunk_index: int
    text: str
    score: float


class ChatResponse(BaseModel):
    """问答响应：答案 + 引用来源 + 会话/消息ID"""
    answer: str
    sources: list[Source]
    session_id: int
    message_id: int
