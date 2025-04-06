"""
配置加载工具模块

该模块提供了从YAML文件加载配置的功能。主要包含load_config函数用于读取和解析YAML格式的配置文件。
"""
import logging
from typing import Dict, Any, Union
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

def load_config(path: Union[str, Path]) -> Dict[str, Any]:
    """
    从YAML文件加载配置
    
    Args:
        path: 配置文件路径
    
    Returns:
        配置字典
    
    Raises:
        FileNotFoundError: 文件不存在时
        yaml.YAMLError: YAML解析错误时
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"配置文件解析错误: {e}")
