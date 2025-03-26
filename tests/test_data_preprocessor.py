import pytest
from pathlib import Path
# from unittest.mock import patch
import pandas as pd
from aa.data_loader.data_preprocessor import DataPreprocessor
import logging
logging.basicConfig(level=logging.DEBUG)

#############################################
# 单元测试（使用模拟数据）
#############################################

# @pytest.fixture
# def test_normal_processing(test_config, test_raw_data, tmp_path):
#     """测试正常数据处理流程"""
#     processor = DataPreprocessor(
#         config_path=test_config,
#         raw_data_dir=str(test_raw_data),
#         output_dir=str(tmp_path / "processed")
#     )

#     result = processor.load()
#     assert result["status"] == "success"

#     output_path = tmp_path / "processed" / "data_preprocessed.xlsx"
#     assert output_path.exists()

#     # 验证all_data sheet
#     df = pd.read_excel(output_path, sheet_name="all_data")
#     assert df.shape == (2, 3)  # 机构+日期+数值
#     # assert df["数值字段"].sum() == pytest.approx(1234.5 + 2345.6 + 3456.7 + 4567.8)

#############################################
# 集成测试（使用真实数据）
#############################################

@pytest.mark.integration
def test_real_data_processing():
    """使用实际项目配置和数据测试"""
    processor = DataPreprocessor(
        data_extraction_config_file="config/data_extraction_config.xlsx",
        raw_data_dir="data/raw",
        data_output_dir="data/processed",
    )

    result = processor.load()
    assert result['status'] == 'success'

    output_path = Path("data/processed/data_preprocessed.xlsx")
    assert output_path.exists()

    # 基础数据验证
    with pd.ExcelFile(output_path) as xls:
        sheets = xls.sheet_names
        assert len(sheets) >= 1
        assert "ALL_DT_AUM时点" in sheets

        df = pd.read_excel(xls, sheet_name="ALL_DT_AUM时点")
        assert not df.empty
        assert "机构名称" in df.columns
        # assert "data_dt" in df.columns

    # 清理测试文件
    # output_path.unlink()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
