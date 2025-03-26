from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging
from aa.data_loader.base_loader import BaseDataLoader

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DataPreprocessor(BaseDataLoader):
    """数据预处理模块，支持新旧两种配置格式"""

    def __init__(
        self,
        data_extraction_config_file = "config/data_extraction_config.xlsx",
        raw_data_dir = "data/raw",
        data_output_dir = "data/processed",
    ):
        super().__init__()
        self.data_extraction_config_file = data_extraction_config_file
        self.raw_data_dir = Path(raw_data_dir)
        self.data_output_dir = Path(data_output_dir)
        self.data_output_file = Path(data_output_dir) / "data_preprocessed.xlsx"
        self.data_output_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self, config: dict = None) -> dict:
        """主处理入口"""
        try:
            # 尝试新版配置格式
            try:
                multi_config, single_config, gourps_config = self._parse_config()
                df_dict = self.process_multi_sheets(multi_config, single_config)
                self._save_output(df_dict, gourps_config)
                return {
                    "status": "success",
                    "record_count": len(df_dict),
                    "data_output_dir": str(self.data_output_dir),
                }
            except ValueError as e:
                logger.info(f"尝试新版配置格式: {e}")

        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            return {"status": "error", "message": str(e)}

    def process_multi_sheets(
        self, multi_config: pd.DataFrame, single_config: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """处理多sheet配置，返回字典结构{multi_sheet_df: dataframe}"""
        result_dict = {}

        # 1.先处理 type == "manual" 的配置
        manual_multi_sheet_df = multi_config[multi_config["type"] == "manual"]
        # 将manual_multi_sheet_df按照multi_sheet_df分组，然后处理每个分组
        for group_name, group in manual_multi_sheet_df.groupby(
            "multi_sheet_df", sort=False
        ):
            merged_dfs = []

            for _, row in group.iterrows():
                # 获取字段定义
                field_defs = single_config[
                    single_config["single_sheet_df"] == row["single_sheet_df"]
                ].sort_values(
                    by="column_index", key=lambda x: x.map(self._excel_column_number)
                )
                if field_defs.empty:
                    # 修改第68-70行代码为：
                    logger.warning(
                        "未找到single_sheet_df配置: %s", row['single_sheet_df']
                    )
                    continue

                col_mapping = {
                    f["field"]: f["column_index"] for _, f in field_defs.iterrows()
                }

                # 加载数据
                file_path = self.raw_data_dir / f"{row['file_name']}.xlsx"
                if not file_path.exists():
                    logger.warning(f"文件不存在: {file_path}")
                    continue

                df = self._load_sheet_data(
                    file_path=file_path,
                    sheet_name=row["sheet_name"],
                    col_mapping=col_mapping,
                    start_row=row["start_row"],
                    end_row=row["end_row"],
                )
                if not df.empty:
                    merged_dfs.append(df)

            if merged_dfs:
                result_dict[group_name] = pd.concat(merged_dfs).reset_index(drop=True)

        # 2.继续处理 type == "standard" 的配置
        standard_multi_sheet_df = multi_config[multi_config["type"] == "standard"]

        for _, row in standard_multi_sheet_df.iterrows():
            try:
                # 直接读取配置字段
                file_name = row['file_name']
                sheet_name = row['sheet_name']
                # start_row = row['start_row']
                # end_row = row['end_row']

                # 构建文件路径
                file_path = self.raw_data_dir / f"{file_name}.xlsx"

                if not file_path.exists():
                    logger.warning("文件不存在: %s", file_path)
                    continue

                # 直接加载整个sheet（不依赖single_config）
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name
                )

                df = self.clean_org_column(df)

                # 存储结果
                result_dict["ALL_DT_"+sheet_name] = df

            except Exception as e:
                logger.error("处理standard配置[%s]失败: %s", sheet_name, str(e))

        return result_dict

    def _load_sheet_data(
        self,
        file_path: Path,
        sheet_name: str,
        col_mapping: dict,
        start_row: int,
        end_row: int,
    ) -> pd.DataFrame:
        """加载单个sheet数据"""
        try:
            # 转换列字母为索引
            indices_lst = [self._col_to_index(c) for c in col_mapping.values()]
            col_indices = ", ".join(indices_lst)

            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=None,
                usecols=col_indices,
                skiprows=start_row - 1,
                nrows=end_row - start_row + 1,
            )

            # 从文件名解析数据日期（格式：月报YYYY-MM-DD.xlsx）
            date_str = file_path.stem.replace("月报", "")
            df.columns = list(col_mapping.keys())
            df["数据日期"] = pd.to_datetime(date_str, format="%Y-%m-%d")
            # 使用 pop() 方法移除 'A' 列
            a_column = df.pop("数据日期")
            # 将 'A' 列添加到 DataFrame 的第一列
            df.insert(0, "数据日期", a_column)
            df = self.clean_org_column(df)
            return df
            # if "机构名称" in df.columns:
            #     df["机构名称"] = df["机构名称"].replace("全行合计", "全行")
            #     df["机构名称"] = df["机构名称"].replace("分行端合计", "分行合计")
            #     df["机构名称"] = df["机构名称"].replace("合计", "全行")
            # return df

        except Exception as e:
            logger.error(f"加载{file_path}失败: {str(e)}")
            return pd.DataFrame()

    def clean_org_column(self, df:pd.DataFrame) -> pd.DataFrame:
        """清洗机构名称字段"""
        if "机构名称" in df.columns:
            df["机构名称"] = df["机构名称"].replace("全行合计", "全行")
            df["机构名称"] = df["机构名称"].replace("分行端合计", "分行合计")
            df["机构名称"] = df["机构名称"].replace("合计", "全行")
        return df
    def _col_to_index(self, col_letter: str) -> int:
        """可以识别字母索引"""
        return col_letter

    def _excel_column_number(self, s) -> int:
        num = 0
        for i, c in enumerate(reversed(s.upper())):  # 处理大小写并反向遍历字符
            num += (ord(c) - ord("A") + 1) * (26**i)
        return num

    def _parse_config(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """解析新版配置文件"""
        multi_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="multi_sheet_df"
        )
        single_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="single_sheet_df"
        )
        groups_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="分行分组"
        )

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
        required_groups = ["分行分组", "机构名称"]

        if not all(col in multi_df.columns for col in required_multi):
            raise ValueError("新版配置缺少必要multi_sheet字段")
        if not all(col in single_df.columns for col in required_single):
            raise ValueError("新版配置缺少必要single_sheet字段")
        if not all(col in groups_df.columns for col in required_groups):
            raise ValueError("新版配置缺少必要分行分组页字段")
        return multi_df, single_df, groups_df

    def _save_output(self, data_dict: dict, groups_config: pd.DataFrame):
        """保存结果到Excel"""
        # pylint: disable=abstract-class-instantiated
        # 使用openpyxl引擎时ExcelWriter需要忽略抽象类实例化警告
        with pd.ExcelWriter(self.data_output_file, engine="openpyxl", mode="w") as writer:  # type: ignore[abstract]
            # 保存原始各sheet数据
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

            # 合并所有DataFrame并保存到ALL_DATA页
            if data_dict:
                # 初始化合并基准
                merged_df = next(iter(data_dict.values()))

                # 逐个合并剩余DataFrame
                for df in list(data_dict.values())[1:]:
                    merged_df = pd.merge(
                        merged_df,
                        df,
                        on=["数据日期", "机构名称"],
                        how="outer",
                        suffixes=("", "_DROP"),
                    )
                    # 去除重复列
                    merged_df = merged_df.loc[
                        :, ~merged_df.columns.str.endswith("_DROP")
                    ]

                # 关联 分组配置df
                merged_df = pd.merge(
                    merged_df,
                    groups_config,
                    on="机构名称",
                    how="left",
                    suffixes=("", "_DROP"),
                )
                # 去除重复列
                merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith("_DROP")]

                # 调整列顺序
                base_columns = ["数据日期", "分行分组", "机构名称"]
                other_columns = [
                    col for col in merged_df.columns if col not in base_columns
                ]
                merged_df = merged_df.reindex(columns=base_columns + other_columns)

                # 保存合并后的宽表
                merged_df.to_excel(writer, sheet_name="ALL_DATA", index=False)

                # 转换窄表格式
                id_vars = ["数据日期", "分行分组", "机构名称"]
                measure_columns = [
                    col for col in merged_df.columns if col not in id_vars
                ]

                melted_df = merged_df.melt(
                    id_vars=id_vars,
                    value_vars=measure_columns,
                    var_name="指标名称",
                    value_name="指标值",
                ).dropna(subset=["指标值"])

                # 按日期和机构名称排序
                final_df = melted_df.sort_values(
                    ["数据日期", "分行分组", "机构名称", "指标名称"]
                ).reset_index(drop=True)

                # 保存合并结果
                final_df.to_excel(writer, sheet_name="ALL_DATA_MELTED", index=False)

    def derive_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """指标衍生函数占位实现
        Args:
            df: 需要衍生指标的数据框
            新增逻辑：
            1. 检查A/B列是否存在
            2. 处理除零异常
            3. 处理缺失值
            4. 添加异常处理机制
        Returns:
            添加衍生指标后的数据框
        """
        try:
            # 检查必要列是否存在
            if "A" not in df.columns or "B" not in df.columns:
                missing_cols = [col for col in ["A", "B"] if col not in df.columns]
                raise ValueError(f"缺失必要列: {', '.join(missing_cols)}")

            # 转换数据类型为数值型
            df[["A", "B"]] = df[["A", "B"]].apply(pd.to_numeric, errors="coerce")

            # 处理除零和无效值
            with np.errstate(divide="ignore", invalid="ignore"):
                c_values = np.divide(df["A"], df["B"])

            # 处理异常情况
            c_values = np.where(
                (df["B"] == 0) | (df["A"].isna()) | (df["B"].isna()), np.nan, c_values
            )

            df["C"] = c_values
        except Exception as e:
            logger.error(f"指标衍生失败: {str(e)}")

        return df
