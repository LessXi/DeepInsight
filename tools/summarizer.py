import asyncio
import os
import re
from core.config import get_llm
from core.utils import async_retry
from core.prompts import SUMMARIZER_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 🚀 异步模型资源池 (Model Resource Pool)
# 职责：管理多个摘要并发槽位，实现跨模型负载均衡
_SUM_MODEL_POOL = asyncio.Queue()
_POOL_INITIALIZED = False

async def _ensure_pool_ready():
    """初始化摘要模型池，从环境变量加载多个模型名"""
    global _POOL_INITIALIZED
    if _POOL_INITIALIZED: return
    
    models_str = os.getenv("SUMMARIZER_MODELS", "qwen/Qwen2.5-7B-Instruct")
    model_list = [m.strip() for m in models_str.split(",") if m.strip()]
    
    for m in model_list:
        await _SUM_MODEL_POOL.put(m)
    
    _POOL_INITIALIZED = True
    print(f"      [🔋 模型池就绪]: 已加载 {len(model_list)} 个并发槽位。")

def _clean_text(text: str) -> str:
    """文本脱水预处理"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def async_summarize(text: str, topic: str = "", chapter: str = "", max_chars: int = 1500) -> str:
    """
    基于负载均衡模型池的异步摘要。
    融合了：模型池调度 + 定向情报提取 + 统一重试装饰器。
    """
    if not text or len(text) <= 500:
        return text
    
    if not _POOL_INITIALIZED:
        await _ensure_pool_ready()

    # 1. 租借一个模型名
    model_to_use = await _SUM_MODEL_POOL.get()
    
    try:
        print(f"      [🎰 池化调度]: 使用槽位 {model_to_use} 处理章节 《{chapter[:10]}...》")
        
        cleaned_text = _clean_text(text)[:12000]
        llm = get_llm(model_name=model_to_use)
        parser = StrOutputParser()
        
        prompt = ChatPromptTemplate.from_messages([
            ('system', SUMMARIZER_SYSTEM_PROMPT),
            ('user', '研究主题：{topic}\n目标章节：{chapter}\n资料内容：\n{text}')
        ])
        
        chain = prompt | llm | parser

        @async_retry(max_retries=3, base_delay=5)
        async def _call_llm_with_pool():
            return await chain.ainvoke({
                'text': cleaned_text,
                'topic': topic,
                'chapter': chapter,
                'max_chars': max_chars
            })

        try:
            return await _call_llm_with_pool()
        except Exception:
            # 最终降级：暴力截断
            return cleaned_text[:max_chars]
            
    finally:
        # 2. 无论成败，必须归还模型名到池子，防止资源泄露
        await _SUM_MODEL_POOL.put(model_to_use)
