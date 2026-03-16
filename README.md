# DeepInsight 🧠

> 基于 LangGraph 的多智能体深度研报生成系统

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-green.svg)](https://www.langchain.com/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目简介

DeepInsight 是一个基于**多智能体协作架构**的深度研究报告生成系统。它通过分工明确的不同 Agent 角色协作，自动完成从主题输入到最终成文的全流程，生成结构严谨、数据支撑的专业深度研报。

### 核心架构

本项目采用当前最流行的 **LangGraph** 状态图架构，实现了多智能体的协作流水线：

```mermaid
graph LR
    START[START] --> Planner[Planner<br/>(主编 - 生成大纲)]
    Planner --> Researcher[Researcher<br/>(研究员 - 联网搜索)]
    Researcher --> Writer[Writer<br/>(主笔 - 撰写草稿)]
    Writer --> Reviewer[Reviewer<br/>(审核员 - 事实核查)]
    Reviewer -- 通过 --> END[END]
    Reviewer -- 不通过 --> Researcher
```

### 角色分工

| 角色 | 职责 |
|------|------|
| 🧠 **Planner 主编** | 将用户输入的模糊主题拆解为结构化的报告大纲 |
| 🕵️ **Researcher 研究员** | 根据大纲每个章节，生成搜索词并联网查找最新资料 |
| ✍️ **Writer 主笔** | 根据大纲和收集到的资料，撰写完整的Markdown格式研报 |
| ⚖️ **Reviewer 审核员** | 检查报告是否有足够数据支撑，不合格则打回重写 |

## ✨ 项目特色

- **清晰的多agent协作架构**：基于LangGraph状态管理，支持条件循环（审核不通过自动返工）
- **工程化完善**：完整的错误重试、限流退避、熔断机制，防止死循环
- **灵活配置**：支持任何OpenAI兼容接口（OpenAI、DeepSeek、ModelScope等）
- **联网搜索**：集成Tavily搜索引擎，获取最新数据
- **输出规范**：强制生成格式化Markdown，便于阅读和分享

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>/DeepInsight.git
cd DeepInsight
```

### 2. 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或者 .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并填写你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# OpenAI API 密钥（或兼容接口的密钥）
OPENAI_API_KEY=your_api_key_here

# （可选）自定义API地址，用于DeepSeek/ModelScope等
OPENAI_API_BASE=https://api.openai.com/v1/

# 模型名称
MODEL_NAME=gpt-4o-mini

# Tavily 搜索API密钥（获取地址：https://tavily.com/）
TAVILY_API_KEY=your_tavily_key_here
```

### 4. 运行生成

```bash
python main.py
```

默认会生成一篇关于"2026年AI空间计算硬件发展趋势"的研报，你可以修改 `main.py` 中的主题，或者后续我们会加上命令行参数支持任意主题。

生成完成后，结果会保存在 `output_report.md`。

## 📦 项目结构

```
DeepInsight/
├── agents/             # 各个智能体实现
│   ├── planner.py      # 主编 - 生成大纲
│   ├── researcher.py   # 研究员 - 搜索资料
│   ├── writer.py       # 主笔 - 撰写草稿
│   └── reviewer.py     # 审核员 - 质量检查
├── core/               # 核心基础设施
│   ├── config.py       # 大模型配置
│   ├── graph.py        # LangGraph 状态图构建
│   └── state.py        # 状态定义
├── tools/              # 工具函数
│   ├── search_tool.py  # 联网搜索工具
│   └── summarizer.py  # 文本摘要工具
├── main.py             # 入口文件
├── requirements.txt    # 依赖列表
├── .env                # 环境变量（gitignore）
└── README.md           # 项目文档
```

## 🛠️ 技术栈

- **LangGraph**: 多智能体状态编排
- **LangChain**: LLM 应用框架
- **Tavily**: 专业AI搜索引擎
- **Pydantic**: 数据验证
- **OpenAI API**: 大模型调用（兼容所有OpenAI格式接口）

## 🎯 设计思路

### 为什么用多Agent而不是单Agent？

- **职责分离**：每个Agent只做一件事，prompt更精简，准确率更高
- **可观测性**：每个步骤都可以单独调试、输出日志
- **可扩展性**：方便增加新的角色（比如插画师、校对员等）
- **质量可控**：通过审核-返工循环，提升输出质量

### 工程亮点

1. **限流退避重试**：API限流时自动等待重试，提高成功率
2. **死循环保护**：最大重试次数限制，避免无限循环
3. **兜底机制**：LLM调用失败时提供默认输出，保证流程不中断
4. **Token控制**：审核时截断过长文本，避免超出上下文窗口

## 📝 示例输出

TODO: 添加生成好的研报示例截图

## 🤝 贡献

欢迎提Issue和PR！

## 📄 License

MIT License

---

*Built with ❤️ for Agent development learning*
