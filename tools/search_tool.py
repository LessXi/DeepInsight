import os
from tavily import TavilyClient

def search_web(query: str, max_results: int = 3) -> str:
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key or api_key == 'your_tavily_api_key_here':
        print('  [警告] 未配置 TAVILY_API_KEY，返回模拟搜索结果。')
        return f'[模拟结果] 关于 {query} 的重要信息：市场正在快速增长，技术突破明显。'

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth='advanced', max_results=max_results)
        
        results = response.get('results', [])
        context = ''
        for res in results:
            context += f'【来源】: {res.get("url")}\n【摘要】: {res.get("content")}\n\n'
        return context if context else '未搜索到相关结果。'
    except Exception as e:
        print(f'  [搜索失败] {e}')
        return '搜索服务当前不可用。'
