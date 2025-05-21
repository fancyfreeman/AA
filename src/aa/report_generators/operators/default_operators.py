"""
默认操作符模块

该模块包含了一系列用于生成报告的默认操作符类，包括:
- 当期值操作符
- 排名操作符
- 趋势操作符
- 完成率操作符
- 同比操作符
- 环比操作符

每个操作符都继承自BaseOperator基类，实现了特定的数据处理和格式化逻辑。
"""

import logging
from typing import Union
import pandas as pd
from aa.report_generators.operators.base_operator import BaseOperator

logger = logging.getLogger(__name__)

# 默认值，将在初始化时被替换
ASC_ORDERED_KEYWORDS = [
    "不良率",
    "成本率",
    "同业排名",
    "排名",
    "零售综合考评等级",
    "退货率",
    "成本",
    "库存量（件）",
]
PERCENTAGE_KEYWORDS = ["率", "占比", "定价", "比例"]


# 用于更新关键词列表的函数
def update_keywords(asc_ordered_keywords=None, percentage_keywords=None):
    """
    更新模块中使用的关键词列表

    Args:
        asc_ordered_keywords: 升序排序关键词列表
        percentage_keywords: 百分比关键词列表
    """
    global ASC_ORDERED_KEYWORDS, PERCENTAGE_KEYWORDS
    if (asc_ordered_keywords is not None) and (percentage_keywords is not None):
        ASC_ORDERED_KEYWORDS = asc_ordered_keywords
        PERCENTAGE_KEYWORDS = percentage_keywords
        logger.info(f"已更新ASC_ORDERED_KEYWORDS: {ASC_ORDERED_KEYWORDS}")
        logger.info(f"已更新PERCENTAGE_KEYWORDS: {PERCENTAGE_KEYWORDS}")


def pp(indicator, value) -> str:
    """美化输出值"""
    # 用于格式化输出数值
    if "排名" in indicator and ("同比" in indicator or "环比" in indicator):
        rank_change = int(value)
        if rank_change == 0:
            res = "排名位次不变"
        else:
            res = f"排名位次{"上升" if value <0 else "下降" }{abs(int(value)):d}位"
    elif "排名" in indicator:
        rank_change = int(value)
        res = f"第{rank_change:d}名"
    elif any(keyword in indicator for keyword in ["成本率", "定价"]) and (
        "同比" in indicator or "环比" in indicator
    ):
        bps = int(value * 10000)
        res = f"{bps:+d}Bps"
    elif any(keyword in indicator for keyword in ["占比", "比例"]) and (
        "同比" in indicator or "环比" in indicator
    ):
        percentage = value * 100
        res = f"{percentage:.2f}个百分点"
    elif any(keyword in indicator for keyword in PERCENTAGE_KEYWORDS):
        res = f"{value:.2%}"
    elif "客户数" in indicator:
        res = f"{int(value)}"
    elif "零售综合考评等级" in indicator:
        mapping = {1: "A", 2: "B", 3: "C"}
        res = mapping.get(value)
    else:
        res = f"{value:.1f}"
    return res


class CurrentValueOperator(BaseOperator):
    """处理当期值操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        # 获取查询参数
        try:
            target_date = pd.to_datetime(config["data_dt_rule"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算当期值时：查询指标数据出错{str(e)}"

        # 执行数据查询
        try:
            filtered = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == target_date
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            # 检查查询结果有效性
            if len(filtered) == 0:
                return "计算当期值时：查询指标数据出错，记录数为0，请检查数据是否完整"

            values = filtered["指标值"].dropna().unique()
            if len(values) != 1:
                return "计算当期值时：查询指标数据出错，记录数不为1，请检查数据是否重复"

            sentiment = get_sentiment(
                operator="CurrentValueOperator", indicator=indicator
            )
            return f"{sentiment}当期值：{pp(indicator,values[0])}"

        except Exception as e:
            return f"计算当期值时：查询指标数据出错{str(e)}"

class RankingOperator(BaseOperator):
    """处理组内排名操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取查询参数
            target_date = pd.to_datetime(config["data_dt_rule"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
            format = config["format"]
        except KeyError as e:
            return f"计算组内排名时：查询指标数据出错{str(e)}"

        try:
            # 获取当前机构的机构分组
            current_org_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == target_date
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            if current_org_data.empty:
                return "计算组内排名时：查询指标数据出错，请检查数据是否完整"

            branch_group = current_org_data["机构分组"].iloc[0]

            # 获取同分组所有机构数据
            group_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == target_date
                )
                & (all_data_melted_df["机构分组"] == branch_group)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            if group_data.empty:
                return "计算组内排名时：查询指标数据出错，机构分组数据为空，请检查机构分组参数是否配置"

            # 去除重复机构数据（保留最后一个）
            dedup_data = group_data.drop_duplicates(subset=["机构名称"], keep="last")

            # 检查 indicator 是否包含列表中的关键词
            ascending_sort = any(
                keyword in indicator for keyword in ASC_ORDERED_KEYWORDS
            )

            sorted_df = dedup_data.sort_values(by="指标值", ascending=ascending_sort)

            # 计算排名（处理并列情况）
            sorted_df["排名"] = (
                sorted_df["指标值"]
                .rank(method="min", ascending=ascending_sort)
                .astype(int)
            )

            # 查找当前机构排名
            org_rank = sorted_df.loc[sorted_df["机构名称"] == org, "排名"].values

            if len(org_rank) == 0:
                return "计算组内排名时：查询指标数据出错，记录数为0，请检查数据是否完整"
            # 生成组内分行排名详情
            rank_details = []
            for idx, row in sorted_df.iterrows():
                rank = row["排名"]
                branch = row["机构名称"]
                value = row["指标值"]
                rank_details.append(f"No{rank}.{branch}（{pp(indicator,value)}）")

            if format == "A":
                sentiment = get_sentiment(
                    operator="RankingOperator",
                    indicator=indicator,
                    group_rank_participant_count=len(sorted_df),
                    rank=org_rank[0]
                )
                return f"{sentiment}组内排名：第{org_rank[0]}名（组内共{len(sorted_df)}家机构）；组内排名顺序为：{'， '.join(rank_details)}"
            else:
                return (
                    "=====" * (len(sorted_df) + 1 - org_rank[0])
                    + f"（第{org_rank[0]}名）"
                )

        except Exception as e:
            return f"计算组内排名时：查询指标数据出错 {str(e)}"


class TrendLast3MonthsOperator(BaseOperator):
    """处理近3月趋势操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 解析基础参数
            target_date = pd.to_datetime(config["data_dt_rule"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算近3月趋势时：查询指标数据出错{str(e)}"

        try:
            # 生成需要查询的三个月范围（T-2、T-1、T）
            months = [target_date - pd.DateOffset(months=x) for x in [2, 1, 0]]
            # 对 months 中的每个日期加上 pd.offsets.MonthEnd(0)
            month_ends = [date + pd.offsets.MonthEnd(0) for date in months]

            # 过滤目标数据
            filtered = all_data_melted_df[
                (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
                & (all_data_melted_df["数据日期"].isin(month_ends))
            ]

            # 有效性检查基础数据
            if filtered.empty:
                return "计算近3月趋势时：查询指标数据出错，数据集为空"

            # 按日期排序后去重（保留每个月份最后一个记录）
            filtered = filtered.sort_values("数据日期")
            dedup_data = filtered.drop_duplicates(subset=["数据日期"], keep="last")

            # 检查是否包含完整三个月数据
            existing_months = dedup_data["数据日期"].unique()
            if not all(m in existing_months for m in month_ends):
                return "计算近3月趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个月末的数据"

            # 按时间顺序提取指标值（T-2、T-1、T）
            trend_data = dedup_data.set_index("数据日期").loc[month_ends]
            values = trend_data["指标值"].tolist()

            # 最终有效性检查
            if len(values) != 3 or any(pd.isnull(values)):
                return "计算近3月趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个月末的数据"

            v1, v2, v3 = values

            indicator_value = f"近3月指标值为：{pp(indicator,v1)} {pp(indicator,v2)} {pp(indicator,v3)}"

            # 检查 indicator 是否包含列表中的关键词
            if any(keyword in indicator for keyword in ASC_ORDERED_KEYWORDS):
                rank = "ASC"
            else:
                rank = "DESC"

            # 判断趋势类型
            result = ""
            if v1 < v2 < v3:
                mean_of_trend = et("up", rank)
                result = f"近3月趋势：连续2月{mean_of_trend}。{indicator_value}"
            elif v1 > v2 > v3:
                mean_of_trend = et("down", rank)
                result = f"近3月趋势：连续2月{mean_of_trend}。{indicator_value}"
            elif v1 <= v2 and v2 > v3:
                mean_of_trend = et("down", rank)
                result = f"近3月趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 >= v2 and v2 < v3:
                mean_of_trend = et("up", rank)
                result = f"近3月趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 == v2 and v2 == v3:
                result = f"近3月趋势：持平。{indicator_value}"
            else:
                result = f"近3月趋势：波动。{indicator_value}"

            sentiment = get_sentiment(
                operator="TrendLast3MonthsOperator",
                indicator=indicator,
                result_str=result
            )
            return f"{sentiment}{result}"

        except Exception as e:
            return f"计算近3月趋势时：查询指标数据出错{str(e)}"


class TrendLast3QuartersOperator(BaseOperator):
    """处理近3季度趋势操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 解析基础参数
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算近3季度趋势时：查询指标数据出错{str(e)}"

        try:
            # 生成需要查询的三个季度范围（T-2、T-1、T）
            # 计算当前季度末
            current_quarter_end = target_date + pd.offsets.QuarterEnd(0)

            # 生成三个季度的季末日期
            quarters = [target_date - pd.DateOffset(months=x) for x in [6, 3, 0]]
            quarter_ends = [date + pd.offsets.MonthEnd(0) for date in quarters]

            # 过滤目标数据
            filtered = all_data_melted_df[
                (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
                & (all_data_melted_df["数据日期"].isin(quarter_ends))
            ]

            # 有效性检查基础数据
            if filtered.empty:
                return "计算近3季度趋势时：查询指标数据出错，数据集为空"

            # 按日期排序后去重（保留每个季度最后一个记录）
            filtered = filtered.sort_values("数据日期")
            dedup_data = filtered.drop_duplicates(subset=["数据日期"], keep="last")

            # 检查是否包含完整三个季度数据
            existing_quarters = dedup_data["数据日期"].unique()
            if not all(q in existing_quarters for q in quarter_ends):
                return "计算近3季度趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个季度末的数据"

            # 按时间顺序提取指标值（T-2、T-1、T）
            trend_data = dedup_data.set_index("数据日期").loc[quarter_ends]
            values = trend_data["指标值"].tolist()

            # 最终有效性检查
            if len(values) != 3 or any(pd.isnull(values)):
                return "计算近3季度趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个季度末的数据"

            v1, v2, v3 = values
            indicator_value = f"近3季度指标值为：{pp(indicator,v1)} {pp(indicator,v2)} {pp(indicator,v3)}"

            # 检查 indicator 是否包含列表中的关键词
            if any(keyword in indicator for keyword in ASC_ORDERED_KEYWORDS):
                rank = "ASC"
            else:
                rank = "DESC"

            # 判断趋势类型
            result = ""
            if v1 < v2 < v3:
                mean_of_trend = et("up", rank)
                result = f"近3季度趋势：连续2季度{mean_of_trend}。{indicator_value}"
            elif v1 > v2 > v3:
                mean_of_trend = et("down", rank)
                result = f"近3季度趋势：连续2季度{mean_of_trend}。{indicator_value}"
            elif v1 <= v2 and v2 > v3:
                mean_of_trend = et("down", rank)
                result = (
                    f"近3季度趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
                )
            elif v1 >= v2 and v2 < v3:
                mean_of_trend = et("up", rank)
                result = (
                    f"近3季度趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
                )
            elif v1 == v2 and v2 == v3:
                result = f"近3季度趋势：持平。{indicator_value}"
            else:
                result = f"近3季度趋势：波动。{indicator_value}"

            sentiment = get_sentiment(
                operator="TrendLast3QuartersOperator",
                indicator=indicator,
                result_str=result,
            )
            return f"{sentiment}{result}"

        except Exception as e:
            return f"计算近3季度趋势时：查询指标数据出错{str(e)}"


class TrendLast3YearsOperator(BaseOperator):
    """处理近3年趋势操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 解析基础参数
            # normalize()将时间戳规范化到当天的午夜时间点(00:00:00)
            # 例如: 2024-03-14 13:45:30 -> 2024-03-14 00:00:00
            # 这样可以确保在比较日期时忽略具体时分秒,只关注年月日
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算近3年趋势时：查询指标数据出错{str(e)}"

        # 判断是否为年末
        if target_date.month == 12 and target_date.day == 31:
            current_year_end = target_date
        else:
            # 获取target_date所在年的年末日期
            # target_date是pd.Timestamp类型,为保持一致也使用pd.Timestamp
            current_year_end = pd.Timestamp(target_date.year - 1, 12, 31).normalize()

        try:
            # 生成需要查询的三个年度范围（T-2、T-1、T）
            years = [current_year_end - pd.DateOffset(years=x) for x in [12, 1, 0]]
            # 生成三个年度的年末日期
            year_ends = [date + pd.offsets.YearEnd(0) for date in years]

            # 过滤目标数据
            filtered = all_data_melted_df[
                (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
                & (all_data_melted_df["数据日期"].isin(year_ends))
            ]

            # 有效性检查基础数据
            if filtered.empty:
                return "计算近3年趋势时：查询指标数据出错，数据集为空"

            # 按日期排序后去重（保留每个年度最后一个记录）
            filtered = filtered.sort_values("数据日期")
            dedup_data = filtered.drop_duplicates(subset=["数据日期"], keep="last")

            # 检查是否包含完整三个年度数据
            existing_years = dedup_data["数据日期"].unique()
            if not all(y in existing_years for y in year_ends):
                return "计算近3年趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个年末的数据"

            # 按时间顺序提取指标值（T-2、T-1、T）
            trend_data = dedup_data.set_index("数据日期").loc[year_ends]
            values = trend_data["指标值"].tolist()

            # 最终有效性检查
            if len(values) != 3 or any(pd.isnull(values)):
                return "计算近3年趋势时：查询指标数据出错，数据日期不完整，数据应包含近3个年末的数据"

            v1, v2, v3 = values
            indicator_value = f"近3年指标值为：{pp(indicator,v1)} {pp(indicator,v2)} {pp(indicator,v3)}"

            # 检查 indicator 是否包含列表中的关键词
            if any(keyword in indicator for keyword in ASC_ORDERED_KEYWORDS):
                rank = "ASC"
            else:
                rank = "DESC"

            # 判断趋势类型
            result = ""
            if v1 < v2 < v3:
                mean_of_trend = et("up", rank)
                return f"近3年趋势：连续2年{mean_of_trend}。{indicator_value}"
            elif v1 > v2 > v3:
                mean_of_trend = et("down", rank)
                return f"近3年趋势：连续2年{mean_of_trend}。{indicator_value}"
            elif v1 <= v2 and v2 > v3:
                mean_of_trend = et("down", rank)
                return f"近3年趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 >= v2 and v2 < v3:
                mean_of_trend = et("up", rank)
                return f"近3年趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 == v2 and v2 == v3:
                return f"近3年趋势：持平。{indicator_value}"
            else:
                return f"近3年趋势：波动。{indicator_value}"

            sentiment = get_sentiment(
                operator="TrendLast3YearsOperator",
                indicator=indicator,
                result_str=result,
            )
            return f"{sentiment}{result}"

        except Exception as e:
            return f"计算近3年趋势时：查询指标数据出错{str(e)}"


# class CompletionRateOperator(BaseOperator):
#     """处理完成率操作符"""

#     @classmethod
#     def handle(
#         cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
#     ) -> str:
#         return f"完成率：{config.get('rate', 'XX')}%（示例实现）"


class YearOverYearOperator(BaseOperator):
    """处理指标同比操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取基础参数
            target_date = pd.to_datetime(config["data_dt_rule"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算年同比时：查询指标数据基础参数出错{str(e)}"

        try:
            # 计算去年同期日期
            last_year_date = target_date - pd.DateOffset(years=1)
            last_year_month_end = last_year_date + pd.offsets.MonthEnd(0)

            # 查询当前数据
            current_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == target_date
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            # 查询去年同期数据
            last_year_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == last_year_month_end
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            # 数据有效性检查
            for data, period in zip(
                [current_data, last_year_data], ["当前", "去年同期"]
            ):
                if len(data) == 0:
                    return f"计算年同比时：查询指标数据出错，{period}数据记录数为0，请检查数据是否完整"

                values = data["指标值"].dropna().unique()
                if len(values) != 1:
                    return f"计算年同比时：查询指标数据出错，{period}数据记录数不为1，请检查数据是否重复"

            # 提取数值
            current_value = current_data["指标值"].iloc[0]
            last_year_value = last_year_data["指标值"].iloc[0]

            # 计算增长额和增幅
            growth_amount = current_value - last_year_value
            try:
                growth_rate = (growth_amount / last_year_value) * 100
            except ZeroDivisionError:
                growth_rate = float("inf")

            # return f"同比情况: 同比增长{growth_amount:.1f}，同比增幅{growth_rate:.1f}%。去年同期：{last_year_value:.1f}"
            # tmp_str1 = f"同比排名 {pp(f"{indicator}_同比",-growth_amount)}" if "排名" in indicator else f"同比增长 {pp(f"{indicator}_同比",growth_amount)}"
            tmp_str1 = f"{pp(f"{indicator}_同比",growth_amount)}"
            tmp_str2 = "" if "排名" in indicator else f"，同比增幅 {growth_rate:.1f}%"

            sentiment = get_sentiment(
                operator="YearOverYearOperator",
                indicator=indicator,
                change_value=growth_amount
            )

            return f"{sentiment}年同比情况：同比变动 {tmp_str1}{tmp_str2}，去年同期：{pp(indicator,last_year_value)}"

        except Exception as e:
            return f"计算年同比时：查询指标数据出错：{str(e)}"


class MonthOverMonthOperator(BaseOperator):
    """处理指标月环比操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取基础参数
            target_date = pd.to_datetime(config["data_dt_rule"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"计算月环比时：查询指标数据基础参数出错{str(e)}"

        try:
            # 计算上月同期日期
            last_month_date = target_date - pd.DateOffset(months=1)

            last_month_month_end = last_month_date + pd.offsets.MonthEnd(0)
            # 查询当前数据
            current_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == target_date
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            # 查询上月同期数据
            last_month_data = all_data_melted_df[
                (
                    pd.to_datetime(all_data_melted_df["数据日期"]).dt.normalize()
                    == last_month_month_end
                )
                & (all_data_melted_df["机构名称"] == org)
                & (all_data_melted_df["指标名称"] == indicator)
            ]

            # 数据有效性检查
            for data, period in zip(
                [current_data, last_month_data], ["当前", "上月同期"]
            ):
                if len(data) == 0:
                    return f"计算月环比时：查询指标数据出错，{period}数据记录数为0，请检查数据是否完整"

                values = data["指标值"].dropna().unique()
                if len(values) != 1:
                    return f"计算月环比时：查询指标数据出错，{period}数据记录数不为1，请检查数据是否重复"

            # 提取数值
            current_value = current_data["指标值"].iloc[0]
            last_month_value = last_month_data["指标值"].iloc[0]

            # 计算增长额和增幅
            growth_amount = current_value - last_month_value
            try:
                growth_rate = (growth_amount / last_month_value) * 100
            except ZeroDivisionError:
                growth_rate = float("inf")

            # tmp_str = "" if "排名" in indicator else f"，环比增幅 {growth_rate:.1f}%"
            # return f"环比情况: 环比增长 {pp(f"{indicator}_环比",growth_amount)}{tmp_str}。上月同期：{pp(indicator,last_month_value)}"

            tmp_str1 = f"{pp(f"{indicator}_环比",growth_amount)}"
            tmp_str2 = "" if "排名" in indicator else f"，环比增幅 {growth_rate:.1f}%"

            sentiment = get_sentiment(
                operator="MonthOverMonthOperator",
                indicator=indicator,
                change_value=growth_amount,
            )
            return f"{sentiment}月环比情况：环比变动 {tmp_str1}{tmp_str2}，上月同期：{pp(indicator,last_month_value)}"

        except Exception as e:
            return f"计算月环比时：查询指标数据出错：{str(e)}"


def et(origianl_trend: str, rank: str) -> str:
    """解释趋势含义"""
    # up 原始数据上升 down 原始数据下降
    # DESC 降序排序 越大越好 ASC 升序排序 越小越好 如 排名
    if origianl_trend == "up" and rank == "DESC":
        return "向好"
    elif origianl_trend == "down" and rank == "DESC":
        return "转差"
    elif origianl_trend == "up" and rank == "ASC":
        return "转差"
    elif origianl_trend == "down" and rank == "ASC":
        return "向好"


def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def get_sentiment(
    operator: str,
    indicator: str,
    result_str: str = None,
    change_value: float = None,
    group_rank_participant_count: int = None,
    rank: int = None,
) -> str:
    """
    判断指标变动的情绪

    Args:
        operator: 算子名称
        result_str: 算子监测的结果字符串
        indicator: 指标名称，如果为None则从result_str中提取

    Returns:
        str: 'Positive' 表示积极情绪，'Negative' 表示消极情绪，'Neutral' 表示中性情绪
    """
    import re

    positive = "🔴"
    negative = "🟢"
    neutral  = "➖"
    # 如果未提供indicator，尝试从result_str中提取
    if indicator is None:
        # 尝试从结果字符串中提取指标名称
        indicator_match = re.search(r"指标名称[：:](\S+)", result_str)
        if indicator_match:
            indicator = indicator_match.group(1)
        else:
            # 如果无法提取指标名称，使用空字符串
            indicator = ""

    # 判断指标是否为负向指标（在ASC_ORDERED_KEYWORDS中的指标为负向指标）
    is_negative_indicator = any(
        keyword in indicator for keyword in ASC_ORDERED_KEYWORDS
    )

    # 根据算子类型处理不同情况
    # 当期值算子
    if operator == "CurrentValueOperator":
        # 当期值算子，都返回中性
        return neutral
    # 趋势类算子
    elif operator in [
        "TrendLast3MonthsOperator",
        "TrendLast3QuartersOperator",
        "TrendLast3YearsOperator",
    ]:
        # 根据趋势描述判断情绪
        if "向好" in result_str:
            return positive
        elif "转差" in result_str:
            return negative
        elif "持平" in result_str or "波动" in result_str:
            return neutral
    # 同环比算子
    elif operator in ["YearOverYearOperator", "MonthOverMonthOperator"]:
        if is_negative_indicator and change_value > 0:
            return positive
        elif is_negative_indicator and change_value < 0:
            return negative
        elif not is_negative_indicator and change_value > 0:
            return positive
        elif not is_negative_indicator and change_value < 0:
            return negative
        elif change_value == 0:
            return neutral
        else:
            return neutral
    # 处理组内排名算子
    elif operator in ["RankingOperator"]:
        pct = rank / group_rank_participant_count
        if pct < 1 / 3:
            return positive
        elif pct > 2 / 3:
            return positive
        else:
            return neutral
    # 其他算子情况
    else:
        return neutral
    # # 同比和环比算子
    # elif operator in ["YearOverYearOperator", "MonthOverMonthOperator"]:
    #     change_value = None

    #     # 使用正则表达式匹配文本中的排名位次变化信息
    #     # 匹配格式为"排名位次上升X位"或"排名位次下降X位"
    #     rank_change_match = re.search(r"排名位次(上升|下降)(\d+)位", result_str)
    #     if rank_change_match:
    #         # 获取变化方向(上升/下降)
    #         # group(1)表示获取正则表达式中第一个捕获组的内容
    #         # 例如在正则表达式"(上升|下降)"中,括号内的内容就是第一个捕获组
    #         # 如果匹配到"上升",则group(1)返回"上升";如果匹配到"下降",则返回"下降"
    #         direction = rank_change_match.group(1)
    #         # 获取变化的数值并转为浮点数
    #         value = float(rank_change_match.group(2))
    #         # 如果是上升,数值取负;如果是下降,数值保持不变
    #         # 这样统一了排名变化的表示方式:负值表示排名提升,正值表示排名下降
    #         change_value = -value

    # # 尝试匹配Bps值
    # elif "Bps" in result_str:
    #     bps_match = re.search(r"([+-]?\d+)Bps", result_str)
    #     if bps_match:
    #         change_value = float(bps_match.group(1)) / 10000  # 转换回小数形式

    # # 尝试匹配百分点
    # elif "个百分点" in result_str:
    #     percent_match = re.search(r"([+-]?\d+\.?\d*)个百分点", result_str)
    #     if percent_match:
    #         change_value = float(percent_match.group(1)) / 100  # 转换回小数形式

    # # 尝试匹配一般数值（带符号的数字）
    # elif not change_value:
    #     number_match = re.search(r"变动\s+([+-]?\d+\.?\d*)", result_str)
    #     if number_match:
    #         change_value = float(number_match.group(1))
    #     else:
    #         # 如果上述模式都不匹配，尝试匹配任何数字
    #         general_number_match = re.search(r"([+-]?\d+\.?\d*)", result_str)
    #         if general_number_match:
    #             change_value = float(general_number_match.group(1))
    #         else:
    #             # 如果无法提取数值，返回中性情绪
    #             return neutral

    # # 判断变动值的正负
    # is_positive_change = change_value > 0

    # # 正向指标，变动为正，为正面；变动为负，为负面
    # # 负向指标，变动为正，为负面；变动为负，为正面
    # if is_negative_indicator:
    #     return positive if not is_positive_change else "Negative"
    # else:
    #     return positive if is_positive_change else "Negative"

    # # 排名算子
    # elif operator == "RankingOperator":
    #     # 排名算子，需要提取排名信息
    #     rank_match = re.search(r"第(\d+)名", result_str)
    #     if rank_match:
    #         rank_value = int(rank_match.group(1))
    #         total_match = re.search(r"组内共(\d+)家机构", result_str)
    #         if total_match:
    #             total = int(total_match.group(1))
    #             # 排名在前三分之一为正面，后三分之一为负面
    #             if rank_value <= total / 3:
    #                 return positive
    #             elif rank_value > total * 2 / 3:
    #                 return negative
    #             else:
    #                 return neutral
    #         else:
    #             # 无法获取总数，简单判断
    #             return (
    #                 "Positive"
    #                 if rank_value <= 3
    #                 else ("Neutral" if rank_value <= 10 else "Negative")
    #             )
    #     return neutral

    # # 默认情况，尝试提取数值
    # else:
    #     # 尝试匹配任何数字
    #     number_match = re.search(r"([+-]?\d+\.?\d*)", result_str)
    #     if number_match:
    #         change_value = float(number_match.group(1))
    #         is_positive_change = change_value > 0

    #         if is_negative_indicator:
    #             return positive if not is_positive_change else "Negative"
    #         else:
    #             return positive if is_positive_change else "Negative"

    #     return neutral
