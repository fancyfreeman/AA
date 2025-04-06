"""零售业务分析报告生成工具

该模块提供了零售业务分析报告的生成功能，包括数据预处理和报告生成两个主要功能。
通过命令行参数控制执行不同的任务，支持灵活的配置文件设置。
"""
import logging
import argparse
from pathlib import Path
from aa.report_generators.report_generator import ReportGenerator
from aa.data_loader.data_preprocessor import DataPreprocessor
from aa.utils.error_handler import handle_errors
import sys
# from aa.utils.config_loader import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """程序的主入口，解析命令行参数，执行数据预处理任务或者报告生成任务"""
    parser = argparse.ArgumentParser(description="生成零售业务分析报告")
    parser.add_argument(
        "--task", "-T",
        type=str,
        default="2",
        choices=["1", "2"],
        help="1:准备数据 2:生成报告 默认执行2:生成报告任务",
    )
    parser.add_argument(
        "--report_config_file",
        type=str,
        default="config/report_config.yaml",
        help="报告配置文件路径",
    )
    parser.add_argument(
        "--data_extraction_config_file",
        type=str,
        default="config/data_extraction_config.xlsx",
        help="数据预处理配置文件路径",
    )
    args = parser.parse_args()

    # 使用常量定义路径
    DATA_OUTPUT_FILE = "data/processed/data_preprocessed.xlsx"
    report_config_file = Path(args.report_config_file)
    data_extraction_config_file = Path(args.data_extraction_config_file)
    data_path = Path(DATA_OUTPUT_FILE)

    # 使用match语句处理任务选择
    match args.task:
        case "1":
            if not data_extraction_config_file.exists():
                logger.error(f"数据预处理配置文件不存在：{data_extraction_config_file}")
                return 1
            handle_data_preprocessing(data_extraction_config_file)
        case "2":
            if not report_config_file.exists():
                logger.error(f"报告配置文件不存在：{report_config_file}")
                return 1
            if not data_path.exists():
                logger.error(f"预处理数据不存在：{data_path}")
                return 1
            if not data_extraction_config_file.exists():
                logger.error(f"数据预处理配置文件不存在：{data_extraction_config_file}")
                return 1
            handle_report_generation(
                data_extraction_config_file, 
                report_config_file,
                data_path
            )

    return 0


@handle_errors
def handle_data_preprocessing(data_extraction_config_file: Path):
    """执行数据预处理任务"""
    processor = DataPreprocessor(
        data_extraction_config_file=str(data_extraction_config_file)
    )
    result = processor.load()
    logger.info("数据预处理完成：%s", result)


@handle_errors
def handle_report_generation(data_extraction_config_file: Path, report_config_file: Path, data_output_file: Path):
    """执行报告生成任务"""
    generator = ReportGenerator(
        data_extraction_config_file=str(data_extraction_config_file),
        report_config_file=str(report_config_file),
        data_output_file=str(data_output_file) # 中间数据预处理后的数据文件
    )
    report = generator.generate({})
    logger.info("报告生成完成：%s", report)


if __name__ == "__main__":
    sys.exit(main())
