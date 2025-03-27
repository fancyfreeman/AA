from pathlib import Path
from typing import Dict
import logging
import numpy as np
import pandas as pd
from aa.data_loader.base_loader import BaseDataLoader

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

        self.data_config_df_dict = self._parse_config()

    def load(self, config: dict = None) -> dict:
        """主处理入口"""
        try:
            df_dict = self.process_multi_sheets()
            self._save_output(df_dict)
            return {
                "status": "success",
                "record_count": len(df_dict),
                "data_output_dir": str(self.data_output_dir),
            }
        except Exception as e:
            logger.error("处理失败: %s", str(e))
            return {"status": "error", "message": str(e)}

    def process_multi_sheets(self) -> Dict[str, pd.DataFrame]:
        """处理多sheet配置，返回字典结构{multi_sheet_df: dataframe}"""
        # 从data_config_df_dict取出要用的df
        multi_config = self.data_config_df_dict["multi_sheet_df"]
        single_config = self.data_config_df_dict["single_sheet_df"]

        # 准备返回变量
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
                file_path = self.raw_data_dir / f"{row['file_name']}"
                if not file_path.exists():
                    logger.warning("文件不存在: %s", file_path)
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

                # 构建文件路径
                file_path = self.raw_data_dir / f"{file_name}"

                if not file_path.exists():
                    logger.warning("文件不存在: %s", file_path)
                    continue

                # 直接加载整个sheet（不依赖single_config）
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name
                )

                df = self._clean_org_column(df)

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

            # 从文件名解析数据日期（格式：XXXYYYY-MM-DD.xlsx XXX可以是任意字符，文件必须以YYYY-MM-DD结尾，必须按次格式，否则无法识别数据日期）
            # date_str = file_path.stem.replace("月报", "")
            date_part = file_path.stem.split(".")[0][-10:]
            df.columns = list(col_mapping.keys())
            df["数据日期"] = pd.to_datetime(date_part, format="%Y-%m-%d")
            # 使用 pop() 方法移除 'A' 列
            a_column = df.pop("数据日期")
            # 将 'A' 列添加到 DataFrame 的第一列
            df.insert(0, "数据日期", a_column)
            df = self._clean_org_column(df)
            return df

        except Exception as e:
            logger.error("加载{file_path}失败: %s", {str(e)})
            return pd.DataFrame()

    def _clean_org_column(self, df:pd.DataFrame) -> pd.DataFrame:
        """清洗机构名称字段"""
        if "机构名称" in df.columns:
            # 机构名映射替换逻辑
            org_mapping_df = self.data_config_df_dict.get("机构名替换")

            if org_mapping_df is not None \
                and "原机构名称" in org_mapping_df.columns \
                and "新机构名称" in org_mapping_df.columns:

                replace_dict = dict(zip(
                    org_mapping_df["原机构名称"], 
                    org_mapping_df["新机构名称"]
                ))
                df["机构名称"] = df["机构名称"].replace(replace_dict)

                # 记录未匹配项（替换后仍存在的旧名称）
                unmatched = df[df["机构名称"].isin(replace_dict.keys())]
                if not unmatched.empty:
                    logger.warning("发现%s条未成功替换的机构名称", len(unmatched))
        return df
    def _col_to_index(self, col_letter: str) -> int:
        """可以识别字母索引"""
        return col_letter

    def _excel_column_number(self, s) -> int:
        num = 0
        for i, c in enumerate(reversed(s.upper())):  # 处理大小写并反向遍历字符
            num += (ord(c) - ord("A") + 1) * (26**i)
        return num

    def _parse_config(self) -> dict:
        """解析新版配置文件"""
        multi_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="multi_sheet_df"
        )
        single_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="single_sheet_df"
        )
        groups_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="机构分组"
        )
        filter_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="过滤机构"
        )
        replacement_df = pd.read_excel(
            self.data_extraction_config_file, sheet_name="机构名替换"
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
        required_groups = ["机构分组", "机构名称"]

        if not all(col in multi_df.columns for col in required_multi):
            raise ValueError("配置缺少必要multi_sheet字段")
        if not all(col in single_df.columns for col in required_single):
            raise ValueError("配置缺少必要single_sheet字段")
        if not all(col in groups_df.columns for col in required_groups):
            raise ValueError("配置缺少必要机构分组页字段")
        return {"multi_sheet_df":multi_df,"single_sheet_df":single_df,"机构分组":groups_df,"过滤机构":filter_df,"机构名替换":replacement_df}

    def _save_output(self, data_dict: dict):
        """保存结果到Excel"""
        # pylint: disable=abstract-class-instantiated
        # 使用openpyxl引擎时ExcelWriter需要忽略抽象类实例化警告
        groups_config = self.data_config_df_dict["机构分组"]
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
                base_columns = ["数据日期", "机构分组", "机构名称"]
                other_columns = [
                    col for col in merged_df.columns if col not in base_columns
                ]
                merged_df = merged_df.reindex(columns=base_columns + other_columns)

                # 保存合并后的宽表
                merged_df.to_excel(writer, sheet_name="ALL_DATA", index=False)

                # 转换窄表格式
                id_vars = ["数据日期", "机构分组", "机构名称"]
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
                    ["数据日期", "机构分组", "机构名称", "指标名称"]
                ).reset_index(drop=True)

                # 保存合并结果
                final_df.to_excel(writer, sheet_name="ALL_DATA_MELTED", index=False)

    def _derive_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
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
            logger.error("指标衍生失败: %s", str(e))

        return df
