from core.config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time

def summarize_text(text: str, max_chars: int = 2000) -> str:
    if len(text) <= max_chars:
        return text
    
    print('      [触发摘要] 检测到超长文本，正在提取核心信息...')
    llm = get_llm()
    parser = StrOutputParser()
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''你是一个专业的信息提取员。
请将下面这段冗长的网页抓取内容进行高度浓缩（控制在800字以内）。
要求：
1. 必须保留所有具体的【数据、年份、公司名、专家观点】。
2. 剔除广告、导航栏等无关的网页噪音。'''),
        ('user', '{text}')
    ])
    
    chain = prompt | llm | parser
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(2) # 基础缓冲
            summary = chain.invoke({'text': text[:15000]})
            return summary
        except Exception as e:
            print(f'      [摘要尝试 {attempt+1} 失败]: {e}')
            if attempt < max_retries - 1:
                sleep_time = 10 * (attempt + 1)
                print(f'      ⏳ 触发限流，休眠 {sleep_time} 秒后重试...')
                time.sleep(sleep_time)
            
    print('      [最终摘要失败，降级为暴力截断]')
    return text[:max_chars]
