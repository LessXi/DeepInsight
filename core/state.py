from typing import TypedDict, Annotated, List, Dict, Any
import operator

# 定义我们在 Agent 之间传递的状态数据结构
# 任何在 Node 中 return 的字段，都会自动合并（或覆盖）到这个大 State 中
class ResearchState(TypedDict):
    topic: str                    # 用户最初始输入的研究主题
    outline: List[str]            # 主编(Planner)拆解后的大纲结构
    research_data: Dict[str, str] # 各章节对应的收集到的研究数据资料
    draft: str                    # 资深主笔(Writer)撰写的完整初稿
    review_feedback: str          # 事实核查员(Fact-Checker)给出的修改建议
    is_approved: bool             # 是否通过了最终审核
    revision_count: int           # 当前重写/审核循环的次数，防止死循环
