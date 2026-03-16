import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
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
        # 保持定向摘要
        compressed_data = await async_summarize(data, topic=topic, chapter=chapter)
        return f'### 【参考资料】 章节：{chapter} ###\n{compressed_data}\n\n'

    # 并行处理所有章节资料
    tasks = [process_chapter_data(chapter, data) for chapter, data in research_data.items()]
    context_list = await asyncio.gather(*tasks)
    context_str = "".join(context_list)
        
    llm = get_llm(role="writer")
    parser = StrOutputParser()
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是一位来自顶级商业咨询机构（如 McKinsey 或 Gartner）的资深合伙人级分析师。
你的任务是撰写一份具有行业深度、逻辑无懈可击、且具备极高决策参考价值的研究报告。

【写作准则】：
1. **数据为王**：严禁空谈。必须从【参考资料】中挖掘具体的百分比、市场规模、增长率、公司名称等事实。如果资料中出现具体数字，务必将其体现在报告中。
2. **逻辑严密**：章节之间必须有内在的因果或递进逻辑。
3. **专业语调**：使用冷静、客观、专业且极具穿透力的行文风格。避免使用“非常”、“惊人”等感性词汇。
4. **核心观点突出**：每个章节都必须有一个核心观点，并且用 **加粗** 的方式突出显示。
5. **Markdown 审美**：
   - 使用一级标题作为报告封面。
   - 使用二级标题区分大章节，三级标题细化核心观点。
   - 对关键结论、核心数据、专家预测使用 **加粗**。
   - 适当使用无序列表归纳要点。
6. **严禁幻觉**：所有的事实和数据必须基于提供的【参考资料】。如果资料不足，请基于现有事实进行合理的专业推测，并注明“行业普遍预期”或“根据现状推断”。'''),
        ('user', '''
你现在需要为客户撰写一份关于【{topic}】的深度研究报告。

【报告大纲】：
{outline}

【审核专家反馈】（若有，请务必在撰写时针对性优化）：
{feedback}

【已筛选的高纯度参考资料】：
{context}

---
请开始你的创作。请确保报告从引人入胜的“执行摘要”开始，以深刻的“行业展望”结束。
请直接输出 Markdown 内容：
''')
    ])
    
    chain = prompt | llm | parser
    
    # 💡 杀手级优化：流式撰写，实时预览
    async def _stream_writer():
        print(f'\n      [🚀 流式写作中] 请在下方查看实时生成的 Markdown 正文预览：\n' + '-'*40)
        full_content = ""
        # 针对 writer 节点直接开启 astream
        async for chunk in chain.astream({
            'topic': topic,
            'outline': '\n'.join(outline),
            'feedback': feedback if feedback else '暂无反馈，请直接生成初稿。',
            'context': context_str
        }):
            # 实时流式输出到控制台
            print(chunk, end="", flush=True)
            full_content += chunk
        print('\n' + '-'*40 + f'\n      [✅ 生成完毕] 报告主体已撰写完成，共 {len(full_content)} 字符。')
        return full_content

    try:
        # 这里为了保持 @async_retry 的风格，我们可以将流式逻辑包裹在重试装饰器下
        # 但要注意：如果重试触发，会打印两遍预览
        @async_retry(max_retries=3, base_delay=10)
        async def _call_writer_streaming():
            return await _stream_writer()

        draft = await _call_writer_streaming()
        return {"draft": draft}
    except Exception as e:
        print(f"      [❌ 撰写异常]: {e}")
        return {"draft": "生成失败，请检查 API 状态。"}
