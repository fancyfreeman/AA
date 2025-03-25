import sys
import os
import pytest
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aa.report_generators.report_generator import ReportGenerator
from pathlib import Path
# import tempfile
import yaml


#############################################
# 集成测试（使用真实数据）
#############################################

@pytest.mark.integration
def test_integration_with_real_config():
    """使用实际配置文件进行集成测试"""
    config_path = Path("config/report_config.yaml")
    data_path = Path("data/processed/data_preprocessed.xlsx")

    if not config_path.exists():
        pytest.skip("缺少配置文件 config/report_config.yaml")
    if not data_path.exists():
        pytest.skip("缺少数据文件 data/processed/data_preprocessed.xlsx")

    generator = ReportGenerator(str(config_path), str(data_path))
    report = generator.generate({} )

if __name__ == "__main__":
    pytest.main(["-v", __file__])
