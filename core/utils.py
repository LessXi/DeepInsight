import asyncio
import random
import functools
from typing import Callable, Any

def async_retry(max_retries: int = 3, base_delay: float = 2.0, jitter: bool = True):
    """
    通用异步重试装饰器（增强可观测性版）。
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        if jitter:
                            delay += random.uniform(0, 1)

                        print(f"      [🔄 重试] 函数 `{func.__name__}` 第 {attempt + 1} 次尝试失败。")
                        print(f"      [❌ 错误]: {str(e)}...")
                        print(f"      [⏳ 等待]: 正在休眠 {delay:.2f}s 后重试...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"      [🚫 失败]: `{func.__name__}` 在 {max_retries} 次重试后彻底失败。")

            raise last_exception

        return wrapper
    return decorator

