from core.state import ResearchState
from core.config import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# 1. 定义大模型需要输出的数据结构（Schema）
# 这非常关键！它能强制大模型输出格式化的 JSON，而不是一堆散乱的文本
class OutlineSchema(BaseModel):
    chapters: List[str] = Field(
        description="研究报告的章节大纲列表，每一项是一个具体的章节标题。"
    )

def plan_node(state: ResearchState):
    """主编 Agent：负责将模糊输入拆解为结构化大纲"""
    print("--- 🧠 主编 Agent：正在制定研究大纲 ---")
    topic = state["topic"]
    
    # 2. 获取大模型实例
    llm = get_llm()
    
    # 3. 设置 JSON 解析器
    parser = JsonOutputParser(pydantic_object=OutlineSchema)
    
    # 4. 编写 Prompt (提示词)
    # 给 Agent 赋予一个人设，并明确告诉它输入和输出要求
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一家顶级商业智库的首席研究员（Planner）。
你的任务是根据用户给定的【研究主题】，拆解出一份具有深度、逻辑严密的研究报告大纲。

大纲必须包含 4 到 6 个核心章节，通常应包含：背景介绍、技术/市场现状、核心分析（竞品/痛点等）、未来展望与结论。

{format_instructions}"""),
        ("user", "研究主题：{topic}")
    ])
    
    # 5. 构建 LangChain 链 (Chain)
    chain = prompt | llm | parser
    
    # 6. 调用模型并解析结果
    try:
        response = chain.invoke({
            "topic": topic,
            "format_instructions": parser.get_format_instructions()
        })
        # 提取模型生成的章节列表
        outline = response.get("chapters", [])
        print(f"  [生成大纲成功]: 包含 {len(outline)} 个章节。")
        for idx, chapter in enumerate(outline, 1):
            print(f"    {idx}. {chapter}")
            
    except Exception as e:
        print(f"  [生成大纲失败]: {e}")
        # 如果大模型调用失败，给出兜底的 fallback 大纲，防止工作流中断
        outline = [
            f"1. {topic}的背景与定义",
            "2. 核心分析",
            "3. 市场规模与关键玩家",
            "4. 风险提示与未来展望"
        ]
    
    # 7. 返回更新后的状态（覆盖原有的 outline 字段）
    return {"outline": outline}
