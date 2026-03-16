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
    """异步并行研究员 Agent：具备统一重试能力"""
    print('--- 🕵️‍♂️ 并行研究员 Agent：正在全网同步检索深度资料 ---')
    
    topic = state.get('topic', '')
    outline = state.get('outline', [])
    revision_count = state.get('revision_count', 0)
    research_data = state.get('research_data', {})
    
    llm = get_llm(role="researcher")
    parser = JsonOutputParser(pydantic_object=SearchQuerySchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是顶尖的情报研究员。针对总主题【{topic}】，你需要为当前指定的【大纲章节】生成几个精准的搜索关键词（Query）。\n{format_instructions}'''),
        ('user', '当前章节：{chapter}')
    ])
    
    chain = prompt | llm | parser

    @async_retry(max_retries=3, base_delay=5)
    async def _process_chapter_with_retry(chapter: str):
        print(f'      [🔍 启动搜索] 章节: {chapter[:20]}...')

        # 1. 异步生成搜索词
        query_response = await chain.ainvoke({
            'topic': topic,
            'chapter': chapter,
            'format_instructions': parser.get_format_instructions()
        })
        # 💡 demo版本，仅取前 2 个核心关键词，减少token压力
        queries = query_response.get('queries', [chapter])[:2]
        print(f'      [📡 生成核心关键词]: {", ".join(queries)}')

        # 每个关键词只取 1 条最相关的结果，共 2 条
        search_tasks = [async_search_web(q, max_results=1) for q in queries]
        search_results = await asyncio.gather(*search_tasks)

        context = ""
        for q, res in zip(queries, search_results):
            context += f'【搜索词】: {q}\n{res}\n'

        print(f'      [✅ 章节就绪]: {chapter[:20]}... (已获取 2 条核心资料)')
        return chapter, context


    # 并发执行所有章节
    tasks = [_process_chapter_with_retry(chapter) for chapter in outline]
    try:
        results = await asyncio.gather(*tasks)
        for chapter, context in results:
            research_data[chapter] = context
    except Exception as e:
        print(f"      [研究节点部分失效]: {e}")

    return {
        'research_data': research_data,
        'revision_count': revision_count + 1
    }
