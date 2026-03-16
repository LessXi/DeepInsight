import asyncio
import os
import sys
from core.graph import build_graph

async def main():
    print("🚀 启动 DeepInsight 多智能体研报系统...")
    app = build_graph()
    
    # 1. 动态主题获取逻辑
    topic = ""
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    
    if not topic:
        print("\n🔎 请输入你想深入研究的主题（例如：'2026年AI空间计算硬件发展趋势'）：")
        topic = input(">> ").strip()
    
    if not topic:
        topic = "2026年AI空间计算硬件发展趋势"
        print(f"      [ℹ️ 提示]: 未输入主题，已使用默认主题: {topic}")
    
    print(f"\n💡 最终确定的研究主题: {topic}\n" + "="*50)
    
    # 2. 初始化状态与配置
    # 即使是内存模式，指定 thread_id 也是最佳实践，方便后续扩展持久化
    config = {"configurable": {"thread_id": "main_thread"}}
    initial_state = {
        "topic": topic,
        "revision_count": 0
    }
    
    # 3. 运行图并实时流式输出
    # 💡 优化：使用 stream_mode="updates" 获得更清晰的节点增量输出
    async for event in app.astream(initial_state, config=config, stream_mode="updates"):
        for node_name, payload in event.items():
            print(f"\n>>>> [节点流转] 🚩 节点完成: {node_name.upper()}")
            
            # 特殊打印：展示 Planner 生成的大纲预览
            if node_name == "planner" and "outline" in payload:
                print(f"      [📊 大纲规划完成]:")
                for i, ch in enumerate(payload["outline"], 1):
                    print(f"        {i}. {ch}")

    print("\n" + "="*50)
    
    # 4. 获取最终状态
    state_snapshot = await app.aget_state(config)
    final_state = state_snapshot.values
    
    # 5. 最终成文导出
    if final_state and final_state.get("draft"):
        output_file = os.path.join(os.path.dirname(__file__), "output_report.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_state["draft"])
        print(f"🎉 任务完成！深度研报已生成并保存至：\n   {output_file}")
    else:
        print("⚠️ 未能从最终状态中提取到草稿内容，请检查流程输出。")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
