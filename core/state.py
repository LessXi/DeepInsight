from typing import TypedDict, Annotated, List, Dict, Any
import operator

# 定义我们在 Agent 之间传递的状态数据结构
# 任何在 Node 中 return 的字段，都会自动合并（或覆盖）到这个大 State 中
class ResearchState(TypedDict):
    topic: str                    # 用户最初始输入的研究主题
    outline: List[str]            # 主编(Planner)拆解后的大纲结构
    # 使用 Annotated 确保字典在节点返回时执行增量合并 (Merge) 而不是全量覆盖
    research_data: Annotated[Dict[str, str], operator.ior] 
    draft: str                    # 资深主笔(Writer)撰写的完整初稿
    review_feedback: str          # 事实核查员(Fact-Checker)给出的修改建议
    is_ready: bool                # 💡 统一字段名：是否准备好发布
    revision_count: int           # 当前重写/审核循环的次数，防止死循环
