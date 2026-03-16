from core.state import ResearchState
from core.config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from tools.search_tool import search_web
import time

class SearchQuerySchema(BaseModel):
    queries: List[str] = Field(
        description='为了深入研究该章节，需要向搜索引擎输入的具体、独立的搜索关键词列表（至少2个）。'
    )

def research_node(state: ResearchState):
    print('--- 🕵️‍♂️ 研究员 Agent：正在全网检索深度资料 ---')
    
    topic = state.get('topic', '')
    outline = state.get('outline', [])
    revision_count = state.get('revision_count', 0)
    
    research_data = state.get('research_data', {})
    
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=SearchQuerySchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是顶尖的情报研究员。
针对总主题【{topic}】，你需要为当前指定的【大纲章节】生成几个精准的、用于谷歌/Tavily等搜索引擎的搜索关键词（Query）。
要求：关键词要足够专业、长尾，能搜出研报、数据和深度分析。

{format_instructions}'''),
        ('user', '当前需要搜索的章节是：\n{chapter}')
    ])
    
    chain = prompt | llm | parser
    
    print(f'  [共收到 {len(outline)} 个章节的大纲，开始逐一检索...]')
    
    chapters_to_search = outline
    
    for chapter in chapters_to_search:
        print(f'\n  🔍 正在分析章节: {chapter}')
        
        # 加入带退避的重试机制
        max_retries = 3
        queries = [chapter]  # 默认兜底
        for attempt in range(max_retries):
            try:
                time.sleep(2) # 基础缓冲
                query_response = chain.invoke({
                    'topic': topic,
                    'chapter': chapter,
                    'format_instructions': parser.get_format_instructions()
                })
                queries = query_response.get('queries', [chapter])
                break
            except Exception as e:
                print(f'    [生成搜索词尝试 {attempt+1} 失败]: {e}')
                if attempt < max_retries - 1:
                    sleep_time = 10 * (attempt + 1)
                    print(f'    ⏳ 触发限流，休眠 {sleep_time} 秒后重试...')
                    time.sleep(sleep_time)
                else:
                    print('    [最终生成搜索词失败，使用默认章节名兜底]')
            
        print(f'    [生成的搜索词]: {queries}')
        
        chapter_context = ''
        for q in queries[:2]:
            print(f'    ⏳ 正在搜索: {q} ...')
            search_result = search_web(query=q, max_results=2)
            chapter_context += f'【搜索词】: {q}\n{search_result}\n'
            
        research_data[chapter] = chapter_context
        print(f'    ✅ 该章节资料收集完成，共获取 {len(chapter_context)} 字符的摘要。')

    print('\n--- 🕵️‍♂️ 研究员 Agent：资料检索完成 ---')
    
    return {
        'research_data': research_data,
        'revision_count': revision_count + 1
    }
