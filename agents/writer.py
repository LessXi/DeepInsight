from core.state import ResearchState
from core.config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools.summarizer import summarize_text
import time

def write_node(state: ResearchState):
    print('--- ✍️ 资深主笔 Agent：正在起草深度报告草稿 ---')
    
    topic = state.get('topic', '')
    outline = state.get('outline', [])
    research_data = state.get('research_data', {})
    feedback = state.get('review_feedback', '')
    
    context_str = ''
    for chapter, data in research_data.items():
        print(f'  [主笔] 正在处理章节资料: {chapter[:15]}... ({len(data)} 字符)')
        compressed_data = summarize_text(data, max_chars=2000)
        context_str += f'### 【参考资料】 {chapter} ###\n{compressed_data}\n\n'
        
    llm = get_llm()
    parser = StrOutputParser()
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是一家顶级商业智库的资深主笔（Writer）。
你的任务是根据提供的【大纲】和【参考资料】，撰写一篇逻辑严密、数据详实、排版精美的深度研究报告。

【排版要求】：
1. 必须使用 Markdown 格式。
2. 包含一级标题（报告名称）、二级标题（章节）、三级标题（子观点）以及加粗强调。
3. 必须在文中引用参考资料里的**具体数据**和**事实**。

【注意事项】：
1. 严禁编造数据（幻觉），所有数据必须来源于【参考资料】。如果资料里没有，请用专业的行业推测替代并说明。
2. 保持专业、客观的咨询公司语调。
'''),
        ('user', '''
【研究主题】：{topic}

【报告大纲】：
{outline}

【审核员修改意见（如果有，请务必针对性修改）】：
{feedback}

【参考资料】：
{context}

请开始撰写你的 Markdown 报告：
''')
    ])
    
    chain = prompt | llm | parser
    
    print('  ⏳ 正在拼命码字中，这可能需要几十秒...')
    
    draft_content = f'# 深度研究报告：{topic}\n\n（生成失败，请检查大模型 API 状态...）'
    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(2) # 基础缓冲
            draft_content = chain.invoke({
                'topic': topic,
                'outline': '\n'.join(outline),
                'feedback': feedback if feedback else '无修改意见，请发挥最佳水平起草初稿。',
                'context': context_str
            })
            print(f'  ✅ 草稿撰写完成！共计 {len(draft_content)} 字。')
            break
        except Exception as e:
            print(f'  [撰写尝试 {attempt+1} 失败]: {e}')
            if attempt < max_retries - 1:
                sleep_time = 15 * (attempt + 1)
                print(f'  ⏳ 触发限流，休眠 {sleep_time} 秒后重试...')
                time.sleep(sleep_time)
    
    return {'draft': draft_content}
