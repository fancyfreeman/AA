import pandas as pd
from aa.report_generators.operators.base_operator import BaseOperator

# 全局变量 升序排名指标关键字
asc_ordered_keywords = ["不良率", "成本率", "同业排名", "排名"]

# 全局变量 百分比指标关键字
percentage_keywords = ["率", "占比", "定价", "比例"]


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
    elif any(keyword in indicator for keyword in percentage_keywords):
        res = f"{value:.2%}"
    elif "客户数" in indicator:
        res = f"{int(value)}"
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
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"查询指标数据出错{str(e)}"

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
                return "查询指标数据出错，记录数为0"

            values = filtered["指标值"].dropna().unique()
            if len(values) != 1:
                return "查询指标数据出错，记录数不为1"

            return f"当期值：{pp(indicator,values[0])}"

        except Exception as e:
            return f"查询指标数据出错{str(e)}"


class RankingOperator(BaseOperator):
    """处理组内排名操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取查询参数
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
            format = config["format"] 
        except KeyError as e:
            return f"查询指标数据出错{str(e)}"

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
                return "查询指标数据出错"

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
                return "查询指标数据出错，分组数据为空"

            # 去除重复机构数据（保留最后一个）
            dedup_data = group_data.drop_duplicates(subset=["机构名称"], keep="last")

            # 检查 indicator 是否包含列表中的关键词
            ascending_sort = any(
                keyword in indicator for keyword in asc_ordered_keywords
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
                return "查询指标数据出错，记录数为0"
            # 生成组内分行排名详情
            rank_details = []
            for idx, row in sorted_df.iterrows():
                rank = row["排名"]
                branch = row["机构名称"]
                value = row["指标值"]
                rank_details.append(f"No{rank}.{branch}（{pp(indicator,value)}）")

            if format == 'A':
                return f"组内排名：第{org_rank[0]}名（组内共{len(sorted_df)}家机构）；组内排名顺序为：{'， '.join(rank_details)}"
            else:
                return (
                    "=====" * (len(sorted_df) + 1 - org_rank[0])
                    + f"（第{org_rank[0]}名）"
                )

        except Exception as e:
            return f"查询指标数据出错 {str(e)}"

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

class TrendOperator(BaseOperator):
    """处理近期趋势操作符"""

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
            return f"查询指标数据出错{str(e)}"

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
                return "查询指标数据出错，数据集为空"

            # 按日期排序后去重（保留每个月份最后一个记录）
            filtered = filtered.sort_values("数据日期")
            dedup_data = filtered.drop_duplicates(subset=["数据日期"], keep="last")

            # 检查是否包含完整三个月数据
            existing_months = dedup_data["数据日期"].unique()
            if not all(m in existing_months for m in month_ends):
                return "查询指标数据出错，数据日期不完整"

            # 按时间顺序提取指标值（T-2、T-1、T）
            trend_data = dedup_data.set_index("数据日期").loc[month_ends]
            values = trend_data["指标值"].tolist()

            # 最终有效性检查
            if len(values) != 3 or any(pd.isnull(values)):
                return "查询指标数据出错，数据日期不完整"

            v1, v2, v3 = values
            # if "排名" in indicator:
            #     indicator_value = f"近3月指标值为：{v1:.0f} {v2:.0f} {v3:.0f}"
            # elif "率" in indicator:
            #     indicator_value = f"近3月指标值为：{v1:.2%} {v2:.2%} {v3:.2%}"
            # else:
            #     indicator_value = f"近3月指标值为：{v1:.1f} {v2:.1f} {v3:.1f}"

            indicator_value = f"近3月指标值为：{pp(indicator,v1)} {pp(indicator,v2)} {pp(indicator,v3)}"

            # 检查 indicator 是否包含列表中的关键词
            if any(keyword in indicator for keyword in asc_ordered_keywords):
                rank = "ASC"
            else:
                rank = "DESC"

            # 判断趋势类型
            if v1 < v2 < v3:
                mean_of_trend = et("up", rank)
                return f"近期趋势：连续2月{mean_of_trend}。{indicator_value}"
            elif v1 > v2 > v3:
                mean_of_trend = et("down", rank)
                return f"近期趋势：连续2月{mean_of_trend}。{indicator_value}"
            elif v1 <= v2 and v2 > v3:
                mean_of_trend = et("down", rank)
                return f"近期趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 >= v2 and v2 < v3:
                mean_of_trend = et("up", rank)
                return f"近期趋势：出现拐点，开始{mean_of_trend}。{indicator_value}"
            elif v1 == v2 and v2 == v3:
                return f"近期趋势：持平。{indicator_value}"
            else:
                return f"近期趋势：波动。{indicator_value}"

        except Exception as e:
            return f"查询指标数据出错{str(e)}"


class CompletionRateOperator(BaseOperator):
    """处理完成率操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        return f"完成率：{config.get('rate', 'XX')}%（示例实现）"


class YearOverYearOperator(BaseOperator):
    """处理指标同比操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取基础参数
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"查询指标数据基础参数出错{str(e)}"

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
                    return f"查询指标数据出错，{period}数据记录数为0"

                values = data["指标值"].dropna().unique()
                if len(values) != 1:
                    return f"查询指标数据出错，{period}数据记录数不为1"

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
            return f"同比情况：同比变动 {tmp_str1}{tmp_str2}，去年同期：{pp(indicator,last_year_value)}"

        except Exception as e:
            return f"查询指标数据出错：{str(e)}"


class MonthOverMonthOperator(BaseOperator):
    """处理指标月环比操作符"""

    @classmethod
    def handle(
        cls, config: dict, all_data_df: pd.DataFrame, all_data_melted_df: pd.DataFrame
    ) -> str:
        try:
            # 获取基础参数
            target_date = pd.to_datetime(config["data_dt"]).normalize()
            org = config["org_name"]
            indicator = config["indicator"]
        except KeyError as e:
            return f"查询指标数据基础参数出错{str(e)}"

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
                    return f"查询指标数据出错，{period}数据记录数为0"

                values = data["指标值"].dropna().unique()
                if len(values) != 1:
                    return f"查询指标数据出错，{period}数据记录数不为1"

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
            return f"环比情况：环比变动 {tmp_str1}{tmp_str2}，上月同期：{pp(indicator,last_month_value)}"

        except Exception as e:
            return f"查询指标数据出错：{str(e)}"
