import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import re

# from aa.utils.config_loader import load_config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

input_file = "/Users/chenxin/Dev/AA/data/raw/A股上市银行年报_银行业/wind.xlsx"

output_file = "/Users/chenxin/Dev/AA/data/raw/A股上市银行年报_银行业/wind_reshaped.xlsx"

sheet_name = "业务指标"

def main():
    """主函数"""
    df1 = pd.read_excel(input_file, sheet_name=sheet_name)

    # 使用melt将宽表转换为长表
    melted = df1.melt(
        id_vars=["代码", "名称"], var_name="指标_单位_报告期_类型", value_name="指标值"
    )
    melted["指标_单位_报告期_类型"] = melted["指标_单位_报告期_类型"].str.replace("\n", "_").str.replace(r"\[单位\].*?_", "",regex=True)

    # tmp = re.sub(r'\[单位\].*?_', '', '贷款总额_[单位]亿元_[报告期]2024-12-31_[报表类型]合并报表')

    # 拆分复合列名
    split_cols = melted["指标_单位_报告期_类型"].str.split("_", expand=True)
    melted["指标"] = split_cols[0]
    # melted["单位"] = split_cols[1].str.replace("[单位]", "")
    melted["数据日期"] = split_cols[1].str.replace(
        r"\[报告期\]|\[年度\]", "", regex=True
    )
    # 将年份转换为年末日期格式
    melted["数据日期"] = melted["数据日期"].apply(
        lambda x: f"{x}-12-31" if x.isdigit() else x
    )
    # melted["报表类型"] = split_cols[2].str.replace("[报表类型]", "")

    # 数据透视
    # 使用pivot_table函数将长表转换为宽表
    # index参数指定作为行索引的列: 代码、名称、数据日期、报表类型和单位
    # columns参数指定要转换为列的值: 指标 (这里会变成"贷款总额"和"存款总额"两列)
    # values参数指定要聚合的值: 指标值
    # reset_index()将索引转换为普通列
    # 不使用reset_index()的话,pivot_table返回的是一个MultiIndex的DataFrame
    # MultiIndex会让数据访问和后续处理变得复杂
    # reset_index()可以将层级索引转换为普通列,使数据结构更简单直观
    # 在pivot_table中,columns参数指定的列("指标")会成为新的列名
    result = melted.pivot_table(
        index=["代码", "名称", "数据日期"],
        columns="指标",
        values="指标值",
    ).reset_index()

    # 删除不需要的列
    result = result.drop(['代码'], axis=1)

    # 重命名列
    result = result.rename(columns={"名称": "机构名称"})

    result["数据日期"] = result["数据日期"].str.replace("-", "/")

    with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:  # type: ignore[abstract]
        result.to_excel(writer, sheet_name="reshaped", index=False)

if __name__ == "__main__":
    sys.exit(main())
