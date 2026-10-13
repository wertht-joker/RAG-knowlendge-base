"""Agent 工具定义与执行器

Agent 能自主决定调用哪些工具、以什么参数调用：
- search_knowledge_base：检索企业知识库（向量召回 + Rerank）
- query_order：按订单号查询订单状态与物流
"""
import json

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.order import Order
from app.rag import retriever

# ===== 工具声明（OpenAI / DeepSeek function-calling 格式）=====

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "在企业知识库中检索资料。当用户询问产品信息、售后政策、"
                "退换货、物流配送、支付方式、会员积分、公司介绍等企业知识时调用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "检索用的查询语句。必须是完整、独立、不含代词指代的问题，"
                            "例如用户问「那多久到账」，应改写为「退货退款多久到账」再检索。"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": (
                "根据订单号查询该订单的实时状态与物流信息。"
                "当用户询问某个具体订单发货没、到哪了、什么状态时调用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_no": {
                        "type": "string",
                        "description": "订单号，例如 DD20260901001",
                    }
                },
                "required": ["order_no"],
            },
        },
    },
]


def tool_label(name: str, args: dict) -> str:
    """生成给前端展示的工具调用步骤文案"""
    if name == "search_knowledge_base":
        return f"🛠 检索知识库：{args.get('query', '')}"
    if name == "query_order":
        return f"🛠 查询订单：{args.get('order_no', '')}"
    return f"🛠 调用工具：{name}"


def _search_knowledge_base(args: dict, db: Session) -> tuple[str, list[dict]]:
    """检索知识库：返回给模型看的文本 + 给前端的引用来源"""
    query = (args.get("query") or "").strip()
    if not query:
        return "未提供检索关键词。", []

    hits = retriever.search(query)
    if not hits:
        return "知识库中未检索到相关内容。", []

    lines = []
    sources = []
    for i, h in enumerate(hits):
        lines.append(f"[片段{i + 1}] {h['text']}")
        doc = db.get(Document, h["doc_id"])
        sources.append({
            "doc_id": h["doc_id"],
            "doc_name": doc.name if doc else "未知文档",
            "chunk_index": h["chunk_index"],
            "text": h["text"],
            "score": h["score"],
        })
    return "\n\n".join(lines), sources


def _query_order(args: dict, db: Session) -> tuple[str, list[dict]]:
    """按订单号查询订单（无来源引用）"""
    order_no = (args.get("order_no") or "").strip()
    if not order_no:
        return "未提供订单号。", []

    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        return f"未查询到订单号 {order_no} 对应的订单，请核对订单号是否正确。", []

    info = (
        f"订单号：{order.order_no}\n"
        f"商品：{order.product_name}\n"
        f"金额：¥{order.amount}\n"
        f"状态：{order.status}\n"
        f"物流：{order.logistics or '暂无物流信息'}"
    )
    return info, []


def execute_tool(name: str, args: dict, db: Session) -> tuple[str, list[dict]]:
    """执行工具，返回 (给模型看的结果文本, 引用来源列表)"""
    if name == "search_knowledge_base":
        return _search_knowledge_base(args, db)
    if name == "query_order":
        return _query_order(args, db)
    return f"未知工具：{name}", []


def parse_arguments(raw: str | None) -> dict:
    """解析模型给出的工具参数（JSON 字符串），解析失败返回空字典"""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
