import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
from core.prompts import WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT # ✅ 引入
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools.summarizer import async_summarize

async def write_node(state: ResearchState):
    """异步主笔 Agent：基于摘要信息撰写整篇报告"""
    print('--- ✍️ 智能主笔 Agent：正在高效起草深度报告 ---')
    
    topic = state.get('topic', '')
    outline = state.get('outline', [])
    research_data = state.get('research_data', {})
    feedback = state.get('review_feedback', '')
    
    async def process_chapter_data(chapter, data):
        compressed_data = await async_summarize(data, topic=topic, chapter=chapter)
        return f'### 【参考资料】 章节：{chapter} ###\n{compressed_data}\n\n'

    # 并行处理资料
    tasks = [process_chapter_data(chapter, data) for chapter, data in research_data.items()]
    context_list = await asyncio.gather(*tasks)
    context_str = "".join(context_list)
        
    llm = get_llm(role="writer")
    parser = StrOutputParser()
    
    # 💡 引用外部 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ('system', WRITER_SYSTEM_PROMPT),
        ('user', WRITER_USER_PROMPT)
    ])
    
    chain = prompt | llm | parser
    
    async def _stream_writer():
        print(f'\n      [🚀 流式写作中] 请在下方查看实时生成的 Markdown 正文预览：\n' + '-'*40)
        full_content = ""
        async for chunk in chain.astream({
            'topic': topic,
            'outline': '\n'.join(outline),
            'feedback': feedback if feedback else '暂无反馈，请直接生成初稿。',
            'context': context_str
        }):
            print(chunk, end="", flush=True)
            full_content += chunk
        print('\n' + '-'*40 + f'\n      [✅ 生成完毕] 报告主体已撰写完成，共 {len(full_content)} 字符。')
        return full_content

    try:
        @async_retry(max_retries=3, base_delay=10)
        async def _call_writer_streaming():
            return await _stream_writer()

        draft = await _call_writer_streaming()
        return {"draft": draft}
    except Exception as e:
        print(f"      [❌ 撰写异常]: {e}")
        return {"draft": "生成失败，请检查 API 状态。"}
