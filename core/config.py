import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

from langchain_openai import ChatOpenAI

def get_llm(role: str = None, model_name: str = None):
    """
    获取 LLM 实例。采用漏斗式（Cascading）回退策略：
    1. model_name 参数 (直接指定)
    2. role 对应的环境变量 (如 SUMMARIZER_MODEL)
    3. 全局 MODEL_NAME 环境变量
    4. 硬编码默认值 (gpt-4o-mini)
    """
    # 映射表
    role_env_map = {
        "planner": "PLANNER_MODEL",
        "researcher": "RESEARCHER_MODEL",
        "writer": "WRITER_MODEL",
        "reviewer": "REVIEWER_MODEL",
        "summarizer": "SUMMARIZER_MODEL"
    }

    # 1. 尝试直接指定的模型名
    final_model = model_name

    # 2. 如果没指定，尝试通过角色查找
    if not final_model and role:
        env_var = role_env_map.get(role)
        final_model = os.getenv(env_var) if env_var else None

    # 3. 最终兜底逻辑
    if not final_model:
        final_model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    print(f"      [🤖 模型分配]: {role or 'manual'} -> {final_model}")

    # 从环境变量读取超时时间，默认 120 秒
    llm_timeout = int(os.getenv("LLM_TIMEOUT", "120"))

    return ChatOpenAI(
        model=final_model,
        temperature=0.7,
        timeout=llm_timeout, # 💡 注入超时配置
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE") if os.getenv("OPENAI_API_BASE") else None
    )
