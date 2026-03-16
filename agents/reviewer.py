import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
from core.prompts import REVIEWER_SYSTEM_PROMPT # ✅ 引入
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class ReviewSchema(BaseModel):
    is_ready: bool = Field(description="报告是否准备好。如果是，设为 True；否则设为 False。")
    feedback: str = Field(description="给研究员和主笔的具体修改建议。")

async def reviewer_node(state: ResearchState):
    """【杀手级审核员】证据对齐式事实核查"""
    print("--- ⚖️ 严苛审核员 Agent：启动深度事实核查与逻辑审计 ---")
    draft = state.get("draft", "")
    topic = state.get("topic", "")
    research_data = state.get("research_data", {}) 
    
    reference_context = ""
    for ch, data in research_data.items():
        reference_context += f"### 参考来源 ({ch}) ###\n{data[:2000]}\n\n"

    llm = get_llm(role="reviewer")
    parser = JsonOutputParser(pydantic_object=ReviewSchema)
    
    # 引用外部 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", REVIEWER_SYSTEM_PROMPT),
        ("user", f'''
【研究主题】：{topic}
【原始研究资料】：
{reference_context}
【待审研报草稿】：
{draft}
''')
    ])
    
    chain = prompt | llm | parser

    @async_retry(max_retries=3, base_delay=5)
    async def _call_reviewer():
        return await chain.ainvoke({
            "topic": topic,
            "draft": draft,
            "format_instructions": parser.get_format_instructions()
        })

    try:
        response = await _call_reviewer()
        is_ready = response.get("is_ready", False)
        feedback = response.get("feedback", "未提供具体反馈。")
        
        if is_ready:
            print("      [✅ 审核通过]: 报告质量达标，准予发布。")
        else:
            print(f"      [❌ 审核不通过]: 发现缺陷，已生成修正建议。")
            
        return {"is_ready": is_ready, "review_feedback": feedback}
    except Exception as e:
        print(f"    [审核异常]: {e}，默认打回重做。")
        return {"is_ready": False, "review_feedback": f"审核节点发生异常: {str(e)}"}
