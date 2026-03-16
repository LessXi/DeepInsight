import asyncio
import os
import sys
from core.graph import build_graph

async def main():
    print("🚀 启动 DeepInsight 多智能体研报系统...")
    app = build_graph()
    
    # 支持命令行参数输入主题
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "2026年AI空间计算硬件发展趋势"
    
    print(f"\n💡 研究主题: {topic}\n" + "="*50)
    
    # 初始化状态并触发图的运行
    initial_state = {
        "topic": topic,
        "revision_count": 0
    }
    
    final_state = None
    # astream() 是异步流式调用，支持图中包含 async 节点
    async for output in app.astream(initial_state):
        for node_name, value in output.items():
            print(f"\n>>>> [节点流转] 🚩 进入节点: {node_name.upper()}")
            # 增量更新状态
            if final_state is None:
                final_state = initial_state.copy()
            final_state.update(value)
            
            # 特殊打印：如果是 planner 节点，打印生成的大纲
            if node_name == "planner" and "outline" in value:
                print(f"      [📊 大纲规划完成]:")
                for i, ch in enumerate(value["outline"], 1):
                    print(f"        {i}. {ch}")

    print("\n" + "="*50)
    
    # 最终成文导出
    if final_state and final_state.get("draft"):
        output_file = os.path.join(os.path.dirname(__file__), "output_report.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_state["draft"])
        print(f"🎉 任务完成！深度研报已生成并保存至：\n   {output_file}")
    else:
        print("⚠️ 未能成功生成草稿，请检查流程输出。")

if __name__ == "__main__":
    # 使用 Windows 下兼容的事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
