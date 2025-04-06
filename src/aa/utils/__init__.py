"""AA工具包

这个模块包含了AA项目中使用的各种工具函数。

Exports:
    load_config: 加载配置文件的函数
"""

from .config_loader import load_config

__all__ = ['load_config']