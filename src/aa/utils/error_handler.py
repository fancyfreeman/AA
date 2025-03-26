from functools import wraps
from typing import Callable, TypeVar
import logging
import sys

logger = logging.getLogger(__name__)

R = TypeVar('R')

class ApplicationError(Exception):
    """应用基础异常类"""
    def __init__(self, message: str, error_code: int = 1):
        super().__init__(message)
        self.error_code = error_code
        self.message = message

def handle_errors(func: Callable[..., R]) -> Callable[..., R]:
    """统一错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"[{e.error_code}] {e.message}")
            sys.exit(e.error_code)
        except Exception as e:
            logger.exception(f"未捕获的异常发生 {str(e)}")
            sys.exit(99)
    return wrapper