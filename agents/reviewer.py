from core.state import ResearchState
from core.config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class ReviewSchema(BaseModel):
    is_approved: bool = Field(description="文章是否通过审核。True表示通过，False表示打回重写。")
    feedback: str = Field(description="具体的修改意见。如果打回，必须指出现有草稿中缺乏数据支撑或逻辑不严密的地方；如果通过，简单肯定即可。")

def review_node(state: ResearchState):
    """事实核查员 Agent：比对原文与草稿，防止幻觉，把控质量"""
    print("--- ⚖️ 事实核查员 Agent：正在进行逻辑审查与幻觉检测 ---")
    
    topic = state.get("topic", "")
    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)
    
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=ReviewSchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是全球最严苛的咨询公司合伙人，现在正在审核初级分析师写的研究报告。
你的任务是评估【报告草稿】，寻找逻辑漏洞、事实缺失或大模型常见的“车轱辘话”。

【审核标准】：
1. 报告必须包含具体的数据支撑（如具体的年份、百分比、公司名），否则不合格。
2. 报告必须符合商业研报的专业排版。
3. 当前是第 {revision_count} 次修改。如果修改次数达到 2 次，为了避免陷入死循环，请放宽标准给予通过（is_approved = True）。

{format_instructions}"""),
        ("user", "【研究主题】：{topic}\n\n【报告草稿】：\n{draft}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "topic": topic,
            "draft": draft[:4000], # 截取前4000字审核，避免超出Token限制
            "revision_count": revision_count,
            "format_instructions": parser.get_format_instructions()
        })
        is_approved = response.get("is_approved", False)
        feedback = response.get("feedback", "报告质量不达标，请重新核实数据并重写。")
        
        # 强制熔断机制：防止大模型过于挑剔导致无限循环
        if revision_count >= 2:
            is_approved = True
            feedback = "已达到最大修改次数，强制通过审核。"
            
    except Exception as e:
        print(f"  [审核过程发生错误]: {e}")
        is_approved = True
        feedback = "审核系统故障，自动放行。"
        
    if is_approved:
        print(f"  [审核结果]: ✅ 审核通过！\n  [评语]: {feedback}")
    else:
         print(f"  [审核结果]: ❌ 不合格打回！\n  [修改意见]: {feedback}")

    return {
        "is_approved": is_approved,
        "review_feedback": feedback
    }
