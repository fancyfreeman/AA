import pandas as pd
from typing import Any
from pathlib import Path
import re
from aa.report_generators.base_generator import BaseReportGenerator
from aa.utils.config_loader import load_config
from aa.report_generators.operators.default_operators import (
    CurrentValueOperator,
    RankingOperator,
    TrendOperator,
    CompletionRateOperator,
    YearOverYearOperator,
    MonthOverMonthOperator
)


# 创建空的 DataFrame，指定列名和数据类型
indicator_rank_df = pd.DataFrame(columns=["维度", "指标名称", "组内排名"], dtype="string")

# 当前一级标题
current_level_title = ""

class ReportGenerator(BaseReportGenerator):
    """配置驱动的分析报告生成器"""

    def __init__(self, config_path: str, data_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = load_config(config_path)
        try:
            self.all_data_df = pd.read_excel(data_path, sheet_name="ALL_DATA")
            self.all_data_metled_df = pd.read_excel(
                data_path, sheet_name="ALL_DATA_MELTED"
            )
        except FileNotFoundError as e:
            raise RuntimeError(f"数据文件未找到: {e.filename}") from e
        except Exception as e:
            raise RuntimeError(f"初始化数据失败: {str(e)}") from e

    def generate(self, analysis_results: Any) -> dict:
        """
        生成报告主入口
        :param analysis_results: 分析结果数据（暂未使用）
        :return: 生成报告内容字符串
        """
        report_content = []

        # 处理报告头部信息
        if 'head' in self.config:
            # 如配置了多个机构，则逐一生成报告
            org_name_list = self.config["head"]["org_name"].split()
            for _ in org_name_list:
                report_content = []
                self.config["head"]["org_name"] = _
                report_content.append(self._process_head(self.config['head']))

                # 处理主体章节
                report_content.append(self._process_sections(self.config.get('sections', [])))

                res = "\n".join(report_content)

                # 保存Markdown文件
                report_dir = Path("reports/")
                # report_dir = Path("/Users/chenxin/Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault/12 工作/项目/经营分析/AA分析报告")
                report_dir.mkdir(parents=True, exist_ok=True)

                # 清理文件名中的特殊字符
                safe_title = self.config['head']['title'].replace(" ", "_").replace(":", "-")
                safe_org = self.config['head']['org_name'].replace(" ", "_").replace(":", "-")
                safe_date = self.config['head']['data_dt'].replace(" ", "_").replace(":", "-")

                filename = f"{safe_title}_{safe_org}_{safe_date}.md"
                filepath = report_dir / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(res)

        return {
            "status": "success",
            "org_name": org_name_list,
            "report_dir": str(report_dir)
        }

    def _process_head(self, head: dict) -> str:
        """处理报告头部信息"""
        header = []
        v1 = v2 = v3 = ""
        if 'title' in head:
            suffix = "分行" if "全行" not in head["org_name"] else "全行"
            # header.append(f"# {head['org_name']}{suffix}{head['title']}")
        if 'data_dt' in head:
            v1 = f"【数据日期】{head['data_dt']}"
        if 'org_name' in head:
            v2 = f"【机构名称】{head['org_name']}"
        if 'author' in head:
            v3 = f"【报告作者】{head['author']}"

        header.append(
            f"> [!INFO] {v1}        {v2}        {v3}"
        )
        # header.append(f"---")
        return '\n'.join(header)

    def _process_sections(self, sections: list, level: int = 1) -> str:
        """递归处理章节结构"""
        content = []
        for section in sections:
            # 处理章节标题
            if 'section_title' in section:
                content.append(f"{'#' * (level+1)} {section['section_title']}\n")
                if level == 1:
                    global current_level_title
                    current_level_title = section['section_title']
            # 处理普通内容
            if 'content' in section:
                content.append(section['content'] + "\n")

            # 处理indicator_rank
            if 'indicator_rank' in section:
                content.append(self._process_indicator_rank()+ "")

            # 处理指标项
            if 'indicators' in section:
                content.extend(self._process_indicators(section['indicators']))

            # 递归处理子章节
            if 'sections' in section:
                content.append(self._process_sections(section['sections'], level + 1))

        return '\n'.join(content)

    def _process_indicator_rank(self) -> str:
        global indicator_rank_df

        if indicator_rank_df.empty:
            return ""

        output = []
        # 按维度字段分组处理
        for dimension in indicator_rank_df['维度'].unique():
            # 添加小标题
            dimension_sub = re.sub(r"[\d\s]", "", dimension)
            output.append(f"#### {dimension_sub}\n")
            # 过滤当前维度的数据
            df_filtered = indicator_rank_df[indicator_rank_df['维度'] == dimension].copy()
            # df_filtered["指标名称"] = df_filtered["指标名称"].str[:30].str.ljust(30).str.replace(' ', '&nbsp;')
            # 生成表格
            output.append(
                df_filtered[
                    ["指标名称", "组内排名"]
                ].to_markdown(index=False, tablefmt="pipe", stralign="left")
            )

        return "\n".join(output)# + "\n"

    def _process_indicators(self, indicators: list) -> list:
        """处理指标集合"""
        output = []
        operator_handlers = {
            "当期值": CurrentValueOperator,
            "组内排名": RankingOperator,
            "近期趋势": TrendOperator,
            "年度计划完成率": CompletionRateOperator,
            "同比": YearOverYearOperator,
            "环比": MonthOverMonthOperator
        }

        for indicator in indicators:
            note = " " + indicator["note"] if 'note' in indicator else ""
            output.append(f"**{indicator['name']}{note}**")

            for operator_config in indicator.get('operators', []):
                # 解析操作符类型和配置
                operator_type, _, config_str = operator_config.partition(':')
                handler_class = operator_handlers.get(operator_type.strip())

                if handler_class:
                    # 构造配置字典（示例实现）
                    # config = {'value': 'XX'}
                    config = {
                        **self.config.get('head', {}),
                        'indicator': indicator['name'],
                        'format': 'A'
                    }

                    text_A = f"- {handler_class.handle(config, self.all_data_df, self.all_data_metled_df)}"
                    output.append(text_A)

                    if operator_type == "组内排名":
                        config = {
                            **self.config.get('head', {}),
                            'indicator': indicator['name'],
                            'format': 'B'
                        }

                        text_B = f"{handler_class.handle(config, self.all_data_df, self.all_data_metled_df)}"
                        # 要插入的数据
                        new_data = {"维度":current_level_title, "指标名称": indicator["name"], "组内排名": text_B}
                        # 获取当前 DataFrame 的长度作为新行的索引
                        new_index = len(indicator_rank_df)
                        indicator_rank_df.loc[new_index] = new_data

                else:
                    output.append(f"- 未知操作符: {operator_type}")

            output.append("")  # 空行分隔
        return output
