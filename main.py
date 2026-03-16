from core.graph import build_graph
import os
import sys

def main():
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
    # stream() 可以让我们实时看到状态在哪个节点流转
    for output in app.stream(initial_state):
        for key, value in output.items():
            print(f"\n[✅ 节点完成]: {key}")
            final_state = value # 持续记录最新的状态

    print("\n" + "="*50)
    
    # 最终成文导出
    if final_state and "draft" in final_state:
        output_file = os.path.join(os.path.dirname(__file__), "output_report.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_state["draft"])
        print(f"🎉 任务完成！深度研报已生成并保存至：\n   {output_file}")
    else:
        print("⚠️ 未能成功生成草稿，请检查API配置和网络连接。")
        sys.exit(1)

if __name__ == "__main__":
    main()
