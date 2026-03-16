import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

from langchain_openai import ChatOpenAI

def get_llm():
    """
    统一获取大模型实例。
    如果 .env 中配置了 OPENAI_API_BASE，它会自动使用该地址（比如支持 DeepSeek）。
    """
    # 你可以在这里调整 model 名称，比如 'gpt-4o' 或 'deepseek-chat'
    # 为了演示兼容性，默认写一个通用的。如果在 .env 配了 deepseek，这里可能需要改成 'deepseek-chat'
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini") 
    
    return ChatOpenAI(
        model=model_name,
        temperature=0.7, # Planner 需要一定的创造力，但又不能太发散
        # 这里的 api_key 和 base_url 会自动从环境变量获取，我们也可以显式传入以防万一
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE") if os.getenv("OPENAI_API_BASE") else None
    )
