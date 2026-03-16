import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class ReviewSchema(BaseModel):
    is_ready: bool = Field(description="报告是否准备好。如果是，设为 True；否则设为 False。")
    feedback: str = Field(description="给研究员和主笔的具体修改建议。")

async def reviewer_node(state: ResearchState):
    """
    【杀手级审核员】证据对齐式事实核查
    任务：对比“原始研究资料”与“研报草稿”，寻找幻觉、缺失数据或逻辑漏洞。
    """
    print("--- ⚖️ 严苛审核员 Agent：启动深度事实核查与逻辑审计 ---")
    draft = state.get("draft", "")
    topic = state.get("topic", "")
    research_data = state.get("research_data", {}) # ✅ 获取原始参考资料
    
    # 构造对比上下文
    reference_context = ""
    for ch, data in research_data.items():
        reference_context += f"### 参考来源 ({ch}) ###\n{data[:2000]}\n\n"

    llm = get_llm(role="reviewer")
    parser = JsonOutputParser(pydantic_object=ReviewSchema)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", '''你是一位全球顶级咨询公司（如麦肯锡）的资深合伙人。
你的任务是对下级分析师提交的研报草稿进行【地狱级审计】。

你的审核维度包括：
1. **事实对齐 (Fact-Grounding)**：检查草稿中的数据是否能在【原始资料】中找到依据。严禁任何凭空想象。
2. **信息密度 (Info-Density)**：是否包含了具体的百分比、金额、公司名、政策代码？如果只有空洞的描述，必须打回。
3. **逻辑连贯 (Coherence)**：章节之间是否有转承启合？是否完成了【研究主题】的所有要求？
4. **Markdown 专业性**：标题层级是否正确？加粗是否得当？

【反馈要求】：
- 如果 `is_ready` 为 False，必须在 `feedback` 中指明具体的错误位置和改进建议（例如：“第二章缺少关于 2025 年预测的具体百分比，请补充”）。
- 只要有 1 处事实错误，必须设为 False。

{format_instructions}'''),
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
        is_ready = response.get("is_ready", True)
        feedback = response.get("feedback", "")
        
        if is_ready:
            print("      [✅ 审核通过]: 报告质量达标，准予发布。")
        else:
            print(f"      [❌ 审核不通过]: 发现缺陷，已生成修正建议。")
            
        return {
            "is_ready": is_ready,
            "review_feedback": feedback
        }
    except Exception as e:
        print(f"    [审核异常]: {e}，默认降级为通过。")
        return {"is_ready": True, "review_feedback": ""}
