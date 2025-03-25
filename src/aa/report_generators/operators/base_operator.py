from abc import ABC, abstractmethod
import pandas as pd

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
