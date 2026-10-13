"""问答服务：Agent 自主决策（工具调用循环）+ 流式输出

与旧版的区别：旧版链路是写死的「改写 → 检索 → 生成」，
现在由大模型自主决定调用哪个工具、用什么参数、调几轮，再汇总回答。
"""
import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag import generator
from app.schemas.chat import ChatResponse, Source
from app.services import session_service, tools

AGENT_SYSTEM_PROMPT = """你是企业的智能客服助手，可以调用工具获取信息后再回答用户。

可用工具：
1. search_knowledge_base —— 检索企业知识库。
2. query_order —— 按订单号查询订单状态和物流。

要求：
1. 涉及"规则/流程"类的问题（产品信息、售后政策、退换货流程、物流配送规则、支付方式、
   会员积分、公司介绍、订单如何查询等），必须先调用 search_knowledge_base 获取资料，
   只根据检索到的内容回答，不要编造；
2. 检索结果中没有答案时，明确回复"未找到相关答案"；
3. 只有用户提供了**具体订单号**、要查这一单的状态时，才调用 query_order；
   不要用 query_order 回答规则类问题，也不要凭空猜测订单状态；
4. 打招呼、闲聊、询问你能做什么这类不需要查资料的问题，可以直接回答；
5. 回答要简洁、准确、友好；可结合对话历史理解上下文，若用户用了"那这个呢"之类的指代，
   请自行改写成完整问题后再检索。"""


def _build_messages(history: list, question: str) -> list[dict]:
    """组装模型输入：系统提示 + 历史对话 + 当前问题"""
    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
    for m in history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": question})
    return messages


def _run_agent(messages: list[dict], db: Session, sources: list[dict], direct: list[str]):
    """ReAct 工具调用循环。

    每一轮让模型自主决定：调用工具（执行后把结果喂回模型，进入下一轮），
    还是直接给出答案（循环结束）。最多 agent_max_steps 轮，防止模型无限调用工具。

    每执行一次工具就 yield 一条展示文案，供流式接口推给前端；
    命中的引用来源就地累加到 sources。

    direct：单元素列表。若模型全程没调用任何工具就直接作答（如打招呼），
    把它的答案放进去，调用方据此省掉一次多余的模型调用。
    """
    called_tool = False
    for _ in range(settings.agent_max_steps):
        assistant_msg = generator.chat_with_tools(messages, tools.TOOLS)
        tool_calls = assistant_msg.get("tool_calls")

        # 模型没调工具 —— 说明它准备作答，循环结束。
        # 注意：这里绝不能把这条 assistant 消息追加进 messages，
        # 否则 messages 以 assistant 结尾，后续流式调用会变成「续写」而不是「回答」。
        if not tool_calls:
            if not called_tool:
                direct.append(assistant_msg.get("content") or "")
            return

        called_tool = True
        # 把模型的工具调用请求记入对话，再逐个执行
        messages.append(assistant_msg)
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = tools.parse_arguments(tc["function"]["arguments"])
            yield tools.tool_label(name, args)

            result_text, hit_sources = tools.execute_tool(name, args, db)
            sources.extend(hit_sources)

            # 工具结果以 tool 角色喂回模型，供其下一轮推理
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_text,
            })


def _dedup_sources(sources: list[dict]) -> list[dict]:
    """同一片段可能被多轮检索命中，按 (doc_id, chunk_index) 去重"""
    seen = set()
    result = []
    for s in sources:
        key = (s["doc_id"], s["chunk_index"])
        if key in seen:
            continue
        seen.add(key)
        result.append(s)
    return result


def ask(db: Session, question: str, session_id: int | None = None) -> ChatResponse:
    """问答主流程（Agent 版，一次性返回）"""
    # 1. 处理会话：没传 session_id 则新建
    if session_id is None:
        session = session_service.create_session(db, title=question[:20])
        session_id = session.id
        history = []
    else:
        history = session_service.get_history(db, session_id)

    # 2. Agent 循环：模型自主决定调用哪些工具
    messages = _build_messages(history, question)
    sources: list[dict] = []
    direct: list[str] = []
    for _ in _run_agent(messages, db, sources, direct):
        pass  # 非流式接口不展示中间步骤

    # 3. 生成最终答案：模型直接答完了就用它，否则基于工具结果再生成
    answer = direct[0] if direct else generator.generate_text(messages)

    # 4. 保存本轮消息（用户问题 + AI 回答）
    session_service.save_message(db, session_id, "user", question)
    msg = session_service.save_message(db, session_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        sources=[Source(**s) for s in _dedup_sources(sources)],
        session_id=session_id,
        message_id=msg.id,
    )


def ask_stream(db: Session, question: str, session_id: int | None = None):
    """流式问答：Agent 先自主调用工具，再流式输出答案（SSE 事件生成器）"""
    # 1. 会话处理
    if session_id is None:
        session = session_service.create_session(db, title=question[:20])
        session_id = session.id
        history = []
    else:
        history = session_service.get_history(db, session_id)

    # 2. Agent 循环：每执行一次工具就推一条 step 事件给前端
    messages = _build_messages(history, question)
    sources: list[dict] = []
    direct: list[str] = []
    for label in _run_agent(messages, db, sources, direct):
        yield f"data: {json.dumps({'type': 'step', 'label': label}, ensure_ascii=False)}\n\n"

    # 3. 保存用户消息
    session_service.save_message(db, session_id, "user", question)

    # 4. 先发 meta（会话ID + 引用来源）
    yield f"data: {json.dumps({'type': 'meta', 'sources': _dedup_sources(sources), 'session_id': session_id}, ensure_ascii=False)}\n\n"

    # 5. 输出最终答案
    full_answer = ""
    if direct:
        # 模型全程没查资料、已直接作答，不必再调一次模型
        full_answer = direct[0]
        yield f"data: {json.dumps({'type': 'delta', 'content': full_answer}, ensure_ascii=False)}\n\n"
    else:
        # 流式生成（失败则降级为一次性返回）
        try:
            for chunk in generator.stream_answer(messages):
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'delta', 'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception:
            full_answer = generator.generate_text(messages)
            yield f"data: {json.dumps({'type': 'delta', 'content': full_answer}, ensure_ascii=False)}\n\n"

    # 6. 保存 AI 回答，发 done
    msg = session_service.save_message(db, session_id, "assistant", full_answer)
    yield f"data: {json.dumps({'type': 'done', 'message_id': msg.id}, ensure_ascii=False)}\n\n"
