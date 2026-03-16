import os
from tavily import TavilyClient, AsyncTavilyClient

def search_web(query: str, max_results: int = 3) -> str:
    """同步搜索，保持向后兼容"""
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key or api_key == 'your_tavily_api_key_here':
        return f'[模拟结果] 关于 {query} 的重要信息：市场正在快速增长，技术突破明显。'
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth='advanced', max_results=max_results)
        return _format_results(response.get('results', []), query)
    except Exception as e:
        print(f'  [同步搜索失败] {e}')
        return '搜索服务当前不可用。'

async def async_search_web(query: str, max_results: int = 2) -> str:
    """异步搜索，用于并行加速"""
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key or api_key == 'your_tavily_api_key_here':
        return f'[模拟结果] 关于 {query} 的重要信息：市场正在快速增长，技术突破明显。'
    try:
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(query=query, search_depth='advanced', max_results=max_results)
        return _format_results(response.get('results', []), query)
    except Exception as e:
        print(f'  [异步搜索失败] {e}')
        return '搜索服务当前不可用。'

def _format_results(results, query):
    context = ''
    for res in results:
        context += f'【来源】: {res.get("url")}\n【摘要】: {res.get("content")}\n\n'
    return context if context else f'未搜索到关于 {query} 的相关结果。'
