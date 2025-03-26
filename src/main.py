import argparse
from aa.report_generators.report_generator import ReportGenerator
import os
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from aa.data_loader.data_preprocessor import DataPreprocessor
def main():
    parser = argparse.ArgumentParser(description='生成零售业务分析报告')
    parser.add_argument(
        "--command", "-C", # 支持长短两种命令参数
        type=str,
        default="2",
        choices=["2", "1"],
        help="1:准备数据 2:生成报告 默认执行2:报告生成任务",
    )
    parser.add_argument('--report_config_file', type=str, default='config/report_config.yaml',
                       help='报告配置文件路径')

    args = parser.parse_args()

    data_output_file = "data/processed/data_preprocessed.xlsx"

    # 检查配置文件和数据文件
    if args.command == "2":

        if not os.path.exists(args.report_config_file):
            raise FileNotFoundError(f"报告配置文件不存在：{args.report_config_file}")
        if not os.path.exists(data_output_file):
            raise FileNotFoundError(
                f"预处理数据不存在，请先执行PD命令，进行数据预处理：{data_output_file}"
            )
    elif args.command == "1":
        data_extraction_config_file = "config/data_extraction_config.xlsx"
        if not os.path.exists(data_extraction_config_file):
            raise FileNotFoundError(f"数据预处理配置文件不存在：{args.pd_config}")

    try:
        match args.command:
            case "1":
                processor = DataPreprocessor()  # 不传入参数值，参数使用默认值
                result = processor.load()
                logger.info(f"数据预处理完成，结果保存至：{data_output_file}")
                logger.info(f"处理结果：{result}")
            case "2":
                # 初始化报告生成器
                generator = ReportGenerator(args.report_config_file, data_output_file)
                report = generator.generate({})
                logger.info(f"处理结果：{report}")
    except FileNotFoundError as e:
        print(f"文件不存在：{e}")
    except Exception as e:
        print(f"程序执行错误：{str(e)}")

if __name__ == "__main__":
    main()
