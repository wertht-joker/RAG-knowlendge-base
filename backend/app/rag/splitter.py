"""文本切分：将长文档切成带重叠的块"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


def split_text(text: str) -> list[str]:
    """按语义切分文本，返回块列表"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        # 优先按段落、换行、中文标点切分，尽量保证语义完整
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        length_function=len,
    )
    return splitter.split_text(text)
