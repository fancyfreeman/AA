import argparse
from aa.report_generators.report_generator import ReportGenerator
import os
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
def main():
    parser = argparse.ArgumentParser(description='生成零售业务分析报告')
    parser.add_argument('--config_file', type=str, default='config/report_config.yaml',
                       help='报告配置文件路径')
    parser.add_argument(
        "--data_file",
        type=str,
        default="data/processed/data_preprocessed.xlsx",
        help="报告配置文件路径",
    )
    args = parser.parse_args()

    # 检查配置文件和数据文件
    if not os.path.exists(args.config_file):
        raise FileNotFoundError(f"配置文件不存在：{args.config_file}")
    if not os.path.exists(args.data_file):
        raise FileNotFoundError(f"数据文件不存在：{args.data_file}")

    try:
        # 初始化报告生成器
        generator = ReportGenerator(args.config_file, args.data_file)
        report = generator.generate({} )
        logger.info("报告生成完毕")
    except FileNotFoundError as e:
        print(f"配置文件不存在：{e}")
    except Exception as e:
        print(f"报告生成失败：{str(e)}")

if __name__ == "__main__":
    main()
