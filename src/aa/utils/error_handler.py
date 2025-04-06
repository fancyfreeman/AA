"""错误处理模块

该模块提供了一套统一的错误处理机制，包括:
- 自定义异常类
- 错误处理装饰器
- 日志记录功能
"""
import logging
import sys
from functools import wraps
from typing import Any, Callable, TypeVar, cast

logger = logging.getLogger(__name__)

# 使用泛型提高类型安全性
R = TypeVar('R')

class ApplicationError(Exception):
    """应用程序异常基类"""
    
    def __init__(self, message: str, error_code: int = 1):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(ApplicationError):
    """配置错误"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=2)


class DataProcessingError(ApplicationError):
    """数据处理错误"""
    
    def __init__(self, message: str):
        super().__init__(message, error_code=3)


def handle_errors(func: Callable[..., R]) -> Callable[..., R]:
    """错误处理装饰器"""
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"[{e.error_code}] {e.message}")
            sys.exit(e.error_code)
        except Exception as e:
            logger.exception(f"未捕获的异常发生: {str(e)}")
            sys.exit(99)
    
    return cast(Callable[..., R], wrapper)