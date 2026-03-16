from langgraph.graph import StateGraph, START, END
from core.state import ResearchState
from agents.planner import plan_node
from agents.researcher import research_node
from agents.writer import write_node
from agents.reviewer import review_node

def build_graph():
    """
    构建 LangGraph 的状态图
    定义了四个关键节点(Node) 以及它们之间的流转逻辑(Edge)
    """
    workflow = StateGraph(ResearchState)

    # 1. 注册所有的 Agent 节点
    workflow.add_node("planner", plan_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("writer", write_node)
    workflow.add_node("reviewer", review_node)

    # 2. 定义常规的线性执行流程
    workflow.add_edge(START, "planner")      # 入口 -> 主编生成大纲
    workflow.add_edge("planner", "researcher") # 大纲 -> 研究员去搜索资料
    workflow.add_edge("researcher", "writer")  # 资料 -> 主笔开始写草稿
    workflow.add_edge("writer", "reviewer")    # 草稿 -> 审核员进行事实核查

    # 3. 定义条件流转（循环机制）：核心亮点
    def check_approval(state: ResearchState) -> str:
        """
        根据审核结果决定下一步去哪：
        - 如果通过(is_approved为True)，或者修改次数超过 3 次，就结束生成。
        - 如果不通过，打回给研究员补充资料/或者主笔重新改写。
        """
        if state.get("is_approved", False) or state.get("revision_count", 0) >= 3:
            return END
        else:
            return "researcher"  # 不合格则重新补充研究数据

    # 将条件判断绑定到 reviewer 节点之后
    workflow.add_conditional_edges(
        "reviewer",
        check_approval,
        {
            END: END,
            "researcher": "researcher"
        }
    )

    return workflow.compile()
