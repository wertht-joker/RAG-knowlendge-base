"""DeepSeek 生成：调用大模型生成答案"""
from openai import OpenAI

from app.core.config import settings

# 模块级缓存客户端
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        # DeepSeek 兼容 OpenAI 接口
        _client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _client


def generate(system_prompt: str, user_prompt: str) -> str:
    """调用 DeepSeek 生成回答文本"""
    client = _get_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # 低温度，减少幻觉、更稳定
    )
    return resp.choices[0].message.content


def generate_stream(system_prompt: str, user_prompt: str):
    """流式生成，逐段返回增量文本（用于 SSE 流式输出）"""
    client = _get_client()
    stream = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# ===== 以下为 Agent（工具调用）相关 =====


def chat_with_tools(messages: list[dict], tools: list[dict]) -> dict:
    """带工具定义调用模型，返回可直接追加回 messages 的 assistant 消息。

    返回结构：{"role": "assistant", "content": "...", "tool_calls": [...]}
    模型若决定调用工具，tool_calls 非空；若决定直接回答，content 非空、tool_calls 缺省。
    """
    client = _get_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # 由模型自主决定调不调、调哪个工具
        temperature=0.3,
    )
    msg = resp.choices[0].message
    result: dict = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        # 转成普通 dict，方便后续原样回传给模型
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return result


def stream_answer(messages: list[dict]):
    """流式生成最终答案（不带工具），逐段返回增量文本"""
    client = _get_client()
    stream = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.3,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def generate_text(messages: list[dict]) -> str:
    """非流式生成完整答案，流式失败时兜底"""
    client = _get_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""
