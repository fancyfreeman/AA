import logging
import argparse
from pathlib import Path
from aa.report_generators.report_generator import ReportGenerator
from aa.data_loader.data_preprocessor import DataPreprocessor
from aa.utils.error_handler import handle_errors

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """程序的主入口，解析命令行参数，执行数据预处理任务或者报告生成任务
    """
    parser = argparse.ArgumentParser(description='生成零售业务分析报告')
    parser.add_argument(
        "--task", "-T", # 支持长短两种命令参数
        type=str,
        default="2",
        choices=["2", "1"],
        help="1:准备数据 2:生成报告 默认执行2:报告生成任务",
    )
    parser.add_argument('--report_config_file', type=str, default='config/report_config.yaml',
                       help='报告配置文件路径')
    args = parser.parse_args()
    data_output_file = "data/processed/data_preprocessed.xlsx"
    config_path = Path(args.report_config_file)
    data_path = Path(data_output_file)

    match args.task:
        case "1":
            data_extraction_config = Path("config/data_extraction_config.xlsx")
            if not data_extraction_config.exists():
                raise FileNotFoundError(
                    f"数据预处理配置文件不存在：{data_extraction_config}"
                )
            handle_data_preprocessing()
        case "2":
            if not config_path.exists():
                raise FileNotFoundError(f"报告配置文件不存在：{config_path}")
            if not data_path.exists():
                raise FileNotFoundError(f"预处理数据不存在：{data_path}")
            handle_report_generation(args.report_config_file, data_output_file)

@handle_errors
def handle_data_preprocessing():
    """执行数据预处理任务"""
    processor = DataPreprocessor()
    result = processor.load()
    logger.info("数据预处理完成：%s", result)

@handle_errors
def handle_report_generation(config_file: str, data_file: str):
    """执行报告生成任务"""
    generator = ReportGenerator(config_file, data_file)
    report = generator.generate({})
    logger.info("报告生成完成：%s", report)

if __name__ == "__main__":
    main()
