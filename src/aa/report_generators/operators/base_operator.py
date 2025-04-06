"""
操作符模块的基础类定义
提供了操作符的抽象基类和必要的方法声明
"""
import logging
from abc import ABC, abstractmethod
import pandas as pd

logger = logging.getLogger(__name__)
class BaseOperator(ABC):
    """操作符处理基类"""

    @classmethod
    @abstractmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        """
        处理操作符的抽象方法
        :param config: 操作符配置信息
        :return: 生成的文本内容
        """
        raise NotImplementedError("Operator must implement handle method")
