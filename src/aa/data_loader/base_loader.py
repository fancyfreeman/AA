"""数据加载器模块

该模块提供了数据加载的基础抽象类，用于定义数据加载的标准接口。
所有具体的数据加载器都应该继承这个基类并实现其抽象方法。
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)
class BaseDataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self, config: dict):
        """Load data from configured source."""
