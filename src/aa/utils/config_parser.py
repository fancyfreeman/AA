"""配置文件解析工具

提供解析数据提取配置文件的通用功能，支持多个模块共享使用。
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Union

logger = logging.getLogger(__name__)

def parse_data_extraction_config(config_file: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """
    解析数据提取配置文件
    
    Args:
        config_file: 数据提取配置文件路径
        
    Returns:
        包含各配置表的字典
    
    Raises:
        ValueError: 当配置文件缺少必要字段时
    """
    config_file = Path(config_file)

    # 读取各配置表
    multi_df = pd.read_excel(
        config_file, sheet_name="multi_sheet_df"
    )
    single_df = pd.read_excel(
        config_file, sheet_name="single_sheet_df"
    )
    groups_df = pd.read_excel(
        config_file, sheet_name="机构分组"
    )
    filter_df = pd.read_excel(
        config_file, sheet_name="过滤机构"
    )
    replacement_df = pd.read_excel(
        config_file, sheet_name="机构名替换"
    )
    ASC_ORDERED_KEYWORDS_df = pd.read_excel(config_file, sheet_name="ASC_ORDERED_KEYWORDS")
    PERCENTAGE_KEYWORDS_df = pd.read_excel(config_file, sheet_name="PERCENTAGE_KEYWORDS")
    # 验证必要字段
    required_multi = [
        "multi_sheet_df",
        "single_sheet_df",
        "file_name",
        "sheet_name",
        "start_row",
        "end_row",
    ]
    required_single = ["single_sheet_df", "field", "column_index", "type", "dtype"]
    required_groups = ["机构分组", "机构名称"]

    if not all(col in multi_df.columns for col in required_multi):
        raise ValueError("配置缺少必要multi_sheet字段")
    if not all(col in single_df.columns for col in required_single):
        raise ValueError("配置缺少必要single_sheet字段")
    if not all(col in groups_df.columns for col in required_groups):
        raise ValueError("配置缺少必要机构分组页字段")

    return {
        "multi_sheet_df": multi_df,
        "single_sheet_df": single_df,
        "机构分组": groups_df,
        "过滤机构": filter_df,
        "机构名替换": replacement_df,
        "ASC_ORDERED_KEYWORDS": ASC_ORDERED_KEYWORDS_df,
        "PERCENTAGE_KEYWORDS": PERCENTAGE_KEYWORDS_df,
    }
