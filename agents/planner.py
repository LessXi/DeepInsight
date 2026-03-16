import asyncio
from core.state import ResearchState
from core.config import get_llm
from core.utils import async_retry
from core.prompts import PLANNER_SYSTEM_PROMPT # ✅ 引入
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

class OutlineSchema(BaseModel):
    chapters: List[str] = Field(
        description="研究报告的章节大纲列表，每一项是一个具体的章节标题。"
    )

async def plan_node(state: ResearchState):
    """异步主编 Agent：负责将模糊输入拆解为结构化大纲"""
    print("--- 🧠 主编 Agent：正在制定研究大纲 ---")
    topic = state["topic"]
    
    llm = get_llm(role="planner")
    parser = JsonOutputParser(pydantic_object=OutlineSchema)
    
    # 💡 逻辑与内容分离：引用外部 Prompts
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("user", "研究主题：{topic}")
    ])
    
    chain = prompt | llm | parser

    @async_retry(max_retries=3, base_delay=5)
    async def _call_llm():
        return await chain.ainvoke({
            "topic": topic,
            "format_instructions": parser.get_format_instructions()
        })

    try:
        response = await _call_llm()
        outline = response.get("chapters", [])
        print(f"  [生成大纲成功]: 包含 {len(outline)} 个章节。")
    except Exception as e:
        print(f"  [最终生成大纲失败，进入兜底逻辑]: {e}")
        outline = [
            f"1. {topic}的背景与定义",
            "2. 核心分析与现状",
            "3. 市场规模与关键玩家",
            "4. 风险提示与未来展望"
        ]
    
    return {"outline": outline}
