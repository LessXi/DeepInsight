from langgraph.graph import StateGraph, START, END
from core.state import ResearchState
from agents.planner import plan_node
from agents.researcher import research_node
from agents.writer import write_node
from agents.reviewer import reviewer_node

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
    workflow.add_node("reviewer", reviewer_node)

    # 2. 定义常规的线性执行流程
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "reviewer")

    # 3. 定义条件流转（循环机制）
    def check_approval(state: ResearchState) -> str:
        # 使用 is_ready 替代 is_approved
        if state.get("is_ready", True) or state.get("revision_count", 0) >= 3:
            return END
        else:
            print(f"      [⚠️ 审核不通过]: {state.get('review_feedback', '理由未知')}")
            return "researcher"

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
