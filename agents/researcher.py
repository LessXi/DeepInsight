import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from tools.search_tool import async_search_web

class SearchQuerySchema(BaseModel):
    queries: List[str] = Field(
        description='为了深入研究该章节，需要向搜索引擎输入的具体、独立的搜索关键词列表（至少2个）。'
    )

async def research_node(state: ResearchState):
    """异步并行研究员 Agent：具备跨章节知识去重能力"""
    print('--- 🕵️‍♂️ 并行研究员 Agent：正在检索深度资料 (Deduplication Enabled) ---')
    
    topic = state.get('topic', '')
    outline = state.get('outline', [])
    revision_count = state.get('revision_count', 0)
    research_data = state.get('research_data', {})
    
    # 💡 杀手级设计：跨章节去重池与同步锁
    # 确保同一个搜索 Query 带来的重复信息在整个状态中只保留一份副本
    seen_queries = set()
    dedup_lock = asyncio.Lock()
    
    llm = get_llm(role="researcher")
    parser = JsonOutputParser(pydantic_object=SearchQuerySchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是一位顶尖的情报研究员。针对主题【{topic}】，你需要为指定大纲章节生成精准的搜索词。'''),
        ('user', '当前章节：{chapter}\n\n{format_instructions}')
    ])
    
    chain = prompt | llm | parser

    @async_retry(max_retries=3, base_delay=5)
    async def _process_chapter_with_retry(chapter: str):
        # 1. 异步生成搜索词
        query_response = await chain.ainvoke({
            'topic': topic,
            'chapter': chapter,
            'format_instructions': parser.get_format_instructions()
        })
        # 限制生成词数量，减少冗余
        queries = query_response.get('queries', [chapter])[:2]
        
        chapter_context = ""
        for q in queries:
            # 💡 跨章节去重检查
            async with dedup_lock:
                if q in seen_queries:
                    chapter_context += f'【搜索词】: {q}\n(该维度资料已在其他章节中覆盖，跳过重复抓取)\n'
                    continue
                seen_queries.add(q)
            
            # 2. 执行实际搜索
            print(f'      [📡 实时抓取]: {q[:20]}...')
            res = await async_search_web(q, max_results=1)
            chapter_context += f'【搜索词】: {q}\n{res}\n'
            
        return chapter, chapter_context

    # 3. 并发执行所有章节
    tasks = [_process_chapter_with_retry(ch) for ch in outline]
    results = await asyncio.gather(*tasks)
    
    new_data = {}
    for ch, content in results:
        new_data[ch] = content

    print(f'\n--- ✅ 研究完成：共处理 {len(outline)} 个章节 ---')
    
    return {
        'research_data': new_data,
        'revision_count': revision_count + 1
    }
