#!/usr/bin/env python3
"""全球鸡蛋购买力排名：按「中位数月工资 ÷ 每斤鸡蛋价格」排序。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from io import StringIO

import pandas as pd
import requests

# 鸡蛋价格：12 枚 M 号鸡蛋/打，美元（GlobalProductPrices，2026 年 1 月）
EGG_PRICES_USD_PER_DOZEN: dict[str, float] = {
    "Switzerland": 7.89,
    "Australia": 7.00,
    "New Zealand": 6.88,
    "Norway": 6.87,
    "Uruguay": 6.28,
    "Czechia": 5.12,
    "Belgium": 4.92,
    "Sweden": 4.88,
    "Denmark": 4.82,
    "Austria": 4.81,
    "UK": 4.76,
    "Hong Kong": 4.71,
    "Ireland": 4.70,
    "USA": 4.62,
    "Italy": 4.57,
    "Germany": 4.53,
    "Greece": 4.49,
    "Israel": 4.44,
    "Ghana": 4.43,
    "France": 4.19,
    "Slovakia": 4.12,
    "Lithuania": 4.12,
    "Latvia": 3.98,
    "Chile": 3.98,
    "Romania": 3.97,
    "Poland": 3.87,
    "Hungary": 3.83,
    "Finland": 3.75,
    "Spain": 3.73,
    "Puerto Rico": 3.58,
    "Portugal": 3.55,
    "Morocco": 3.51,
    "Netherlands": 3.39,
    "Croatia": 3.38,
    "South Africa": 3.24,
    "Mexico": 3.17,
    "South Korea": 3.04,
    "Colombia": 2.97,
    "Japan": 2.90,
    "Slovenia": 2.88,
    "Canada": 2.77,
    "UA Emirates": 2.72,
    "Ivory Coast": 2.69,
    "Nigeria": 2.68,
    "Singapore": 2.65,
    "Peru": 2.58,
    "Jordan": 2.54,
    "Serbia": 2.52,
    "Thailand": 2.52,
    "Malaysia": 2.49,
    "Turkey": 2.40,
    "Brazil": 2.37,
    "Saudi Arabia": 2.34,
    "Tanzania": 2.34,
    "Ecuador": 2.33,
    "China": 2.30,
    "Russia": 2.29,
    "Cameroon": 2.27,
    "Philippines": 2.26,
    "Kuwait": 2.21,
    "Vietnam": 2.10,
    "Ukraine": 2.06,
    "Paraguay": 2.06,
    "Domin. Rep.": 2.05,
    "Tunisia": 2.02,
    "Costa Rica": 1.94,
    "India": 1.91,
    "Uganda": 1.90,
    "Guatemala": 1.89,
    "Kenya": 1.88,
    "Zambia": 1.86,
    "Bolivia": 1.81,
    "Azerbaijan": 1.80,
    "Indonesia": 1.75,
    "Kazakhstan": 1.71,
    "Egypt": 1.68,
    "Sri Lanka": 1.62,
    "Bangladesh": 1.55,
    "Pakistan": 1.40,
}

# 国家/地区中文名
COUNTRY_NAMES_ZH: dict[str, str] = {
    "Switzerland": "瑞士",
    "Australia": "澳大利亚",
    "New Zealand": "新西兰",
    "Norway": "挪威",
    "Uruguay": "乌拉圭",
    "Czechia": "捷克",
    "Belgium": "比利时",
    "Sweden": "瑞典",
    "Denmark": "丹麦",
    "Austria": "奥地利",
    "UK": "英国",
    "Hong Kong": "中国香港",
    "Ireland": "爱尔兰",
    "USA": "美国",
    "Italy": "意大利",
    "Germany": "德国",
    "Greece": "希腊",
    "Israel": "以色列",
    "Ghana": "加纳",
    "France": "法国",
    "Slovakia": "斯洛伐克",
    "Lithuania": "立陶宛",
    "Latvia": "拉脱维亚",
    "Chile": "智利",
    "Romania": "罗马尼亚",
    "Poland": "波兰",
    "Hungary": "匈牙利",
    "Finland": "芬兰",
    "Spain": "西班牙",
    "Puerto Rico": "波多黎各",
    "Portugal": "葡萄牙",
    "Morocco": "摩洛哥",
    "Netherlands": "荷兰",
    "Croatia": "克罗地亚",
    "South Africa": "南非",
    "Mexico": "墨西哥",
    "South Korea": "韩国",
    "Colombia": "哥伦比亚",
    "Japan": "日本",
    "Slovenia": "斯洛文尼亚",
    "Canada": "加拿大",
    "UA Emirates": "阿联酋",
    "Ivory Coast": "科特迪瓦",
    "Nigeria": "尼日利亚",
    "Singapore": "新加坡",
    "Peru": "秘鲁",
    "Jordan": "约旦",
    "Serbia": "塞尔维亚",
    "Thailand": "泰国",
    "Malaysia": "马来西亚",
    "Turkey": "土耳其",
    "Brazil": "巴西",
    "Saudi Arabia": "沙特阿拉伯",
    "Tanzania": "坦桑尼亚",
    "Ecuador": "厄瓜多尔",
    "China": "中国",
    "Russia": "俄罗斯",
    "Cameroon": "喀麦隆",
    "Philippines": "菲律宾",
    "Kuwait": "科威特",
    "Vietnam": "越南",
    "Ukraine": "乌克兰",
    "Paraguay": "巴拉圭",
    "Domin. Rep.": "多米尼加",
    "Tunisia": "突尼斯",
    "Costa Rica": "哥斯达黎加",
    "India": "印度",
    "Uganda": "乌干达",
    "Guatemala": "危地马拉",
    "Kenya": "肯尼亚",
    "Zambia": "赞比亚",
    "Bolivia": "玻利维亚",
    "Azerbaijan": "阿塞拜疆",
    "Indonesia": "印度尼西亚",
    "Kazakhstan": "哈萨克斯坦",
    "Egypt": "埃及",
    "Sri Lanka": "斯里兰卡",
    "Bangladesh": "孟加拉国",
    "Pakistan": "巴基斯坦",
}

# 鸡蛋价格国家名 → 最低工资/工资表国家名
COUNTRY_ALIASES: dict[str, str] = {
    "USA": "United States",
    "UK": "United Kingdom",
    "Czechia": "Czech Republic",
    "UA Emirates": "United Arab Emirates",
    "Domin. Rep.": "Dominican Republic",
    "Ivory Coast": "Côte d'Ivoire",
    "Hong Kong": "Hong Kong SAR, China",
}

# 平均工资表反向映射（Wikipedia 国家名 → 鸡蛋表键名）
AVG_WAGE_REVERSE: dict[str, str] = {
    "United States": "USA",
    "United Kingdom": "UK",
    "Czech Republic": "Czechia",
    "Hong Kong SAR, China": "Hong Kong",
}

# 中位数月工资，美元（各国统计局/CEIC 中位数收入，近年数据）
MEDIAN_MONTHLY_USD: dict[str, float] = {
    "Switzerland": 6955,
    "Australia": 3896,
    "New Zealand": 4050,
    "Norway": 5974,
    "Uruguay": 2509,
    "Czechia": 2506,
    "Belgium": 4409,
    "Sweden": 5707,
    "Denmark": 7344,
    "Austria": 3429,
    "UK": 4047,
    "Hong Kong": 2531,
    "Ireland": 4710,
    "USA": 5133,
    "Italy": 4277,
    "Germany": 6174,
    "Greece": 1821,
    "Israel": 4611,
    "Ghana": 242,
    "France": 3300,
    "Slovakia": 2024,
    "Lithuania": 2940,
    "Latvia": 2289,
    "Romania": 2246,
    "Poland": 2611,
    "Hungary": 2305,
    "Finland": 4948,
    "Spain": 2801,
    "Portugal": 1438,
    "Netherlands": 2994,
    "Croatia": 2377,
    "South Africa": 1660,
    "Mexico": 1142,
    "South Korea": 3350,
    "Japan": 1999,
    "Slovenia": 3081,
    "Canada": 3922,
    "Singapore": 4970,
    "Peru": 650,
    "Jordan": 777,
    "Serbia": 1613,
    "Thailand": 442,
    "Malaysia": 898,
    "Brazil": 658,
    "Saudi Arabia": 1012,
    "Ecuador": 444,
    "China": 1438,
    "Russia": 1352,
    "Vietnam": 399,
    "Ukraine": 693,
    "Paraguay": 527,
    "Kenya": 540,
    "Zambia": 211,
    "Bolivia": 728,
    "Azerbaijan": 677,
    "Indonesia": 187,
    "Kazakhstan": 782,
    "Egypt": 140,
    "Pakistan": 140,
    "Colombia": 259,
    "UA Emirates": 2028,
    "Chile": 900,
    "Puerto Rico": 1600,
    "Morocco": 320,
    "Ivory Coast": 150,
    "Nigeria": 150,
    "Tanzania": 120,
    "Cameroon": 140,
    "Philippines": 300,
    "Kuwait": 2000,
    "Domin. Rep.": 400,
    "Tunisia": 280,
    "Costa Rica": 700,
    "India": 250,
    "Uganda": 70,
    "Guatemala": 450,
    "Sri Lanka": 180,
    "Bangladesh": 120,
    "Turkey": 850,
}

# 平均工资补充（月 gross，美元），Wikipedia 未收录的国家
SUPPLEMENTAL_AVG_MONTHLY_USD: dict[str, float] = {
    "Chile": 1200,
    "Puerto Rico": 2000,
    "Morocco": 400,
    "Ivory Coast": 200,
    "Nigeria": 200,
    "Tanzania": 150,
    "Cameroon": 180,
    "Philippines": 380,
    "Kuwait": 2500,
    "Domin. Rep.": 500,
    "Tunisia": 350,
    "Costa Rica": 900,
    "India": 350,
    "Uganda": 90,
    "Guatemala": 550,
    "Sri Lanka": 220,
    "Bangladesh": 150,
}

# 无法定全国统一最低工资时的补充数据（小时工资，美元）
SUPPLEMENTAL_HOURLY_WAGES: dict[str, tuple[float, str]] = {
    "Switzerland": (22.64, "汝拉州 CHF 20.6/小时"),
    "Norway": (22.19, "建筑无经验工人 NOK 239.61/小时"),
    "Sweden": (14.50, "行业集体谈判估算"),
    "Denmark": (16.00, "私营部门集体协议均价"),
    "Austria": (8.21, "法定下限 €1200/月"),
    "Italy": (8.00, "行业集体协议估算"),
    "Finland": (11.50, "行业集体协议估算"),
    "Singapore": (4.97, "清洁工 SGD 1200/月"),
    "Egypt": (0.80, "私营部门 LE 7000/月"),
    "Puerto Rico": (10.50, "美国联邦最低工资"),
    "Kenya": (0.93, "内罗毕普通劳工 KES 18047/月"),
    "Kazakhstan": (1.15, "全国最低工资 KZT 85000/月"),
}

# 缺少官方中位数时，用平均工资估算的中位数比例
MEDIAN_TO_MEAN_RATIO = 0.82

# M 号鸡蛋约 53g；1 斤 = 500g
EGG_WEIGHT_G = 53
DOZEN_COUNT = 12
JIN_GRAMS = 500

WIKI_MIN_WAGE_URL = "https://en.wikipedia.org/wiki/List_of_minimum_wages_by_country"
WIKI_AVG_WAGE_URL = "https://en.wikipedia.org/wiki/List_of_countries_by_average_wage"


@dataclass
class AffordabilityRow:
    rank: int
    country: str
    median_monthly_usd: float
    avg_monthly_usd: float
    min_hourly_usd: float | None
    egg_dozen_usd: float
    egg_per_jin_usd: float
    median_per_jin_ratio: float
    min_hourly_per_jin_ratio: float | None
    median_jin_per_month: float
    min_jin_per_hour: float | None
    wage_notes: str


def format_country_name(country: str) -> str:
    zh = COUNTRY_NAMES_ZH.get(country)
    if zh:
        return f"{zh} {country}"
    return country


def dozen_to_jin_price(dozen_usd: float) -> float:
    grams_per_dozen = DOZEN_COUNT * EGG_WEIGHT_G
    return dozen_usd / (grams_per_dozen / JIN_GRAMS)


def fetch_wikipedia_min_wages() -> dict[str, float]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; EggAffordability/1.0)"}
    response = requests.get(WIKI_MIN_WAGE_URL, headers=headers, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    wages = tables[2].copy()
    wages.columns = [
        "country",
        "notes",
        "annual_nominal",
        "annual_ppp",
        "workweek",
        "hourly_nominal",
        "hourly_ppp",
        "gdp_pct",
        "effective_date",
    ]
    wages = wages[wages["country"] != "Country"]
    wages["hourly_nominal"] = pd.to_numeric(wages["hourly_nominal"], errors="coerce")
    return dict(zip(wages["country"], wages["hourly_nominal"]))


def fetch_wikipedia_avg_wages() -> dict[str, float]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; EggAffordability/1.0)"}
    response = requests.get(WIKI_AVG_WAGE_URL, headers=headers, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    avg = tables[1].copy()
    avg.columns = ["country", "monthly_usd", "year"]
    avg["country"] = (
        avg["country"].str.replace("\u202f", "", regex=False).str.replace("*", "", regex=False).str.strip()
    )
    avg["monthly_usd"] = pd.to_numeric(avg["monthly_usd"], errors="coerce")
    result: dict[str, float] = {}
    for country, monthly in zip(avg["country"], avg["monthly_usd"]):
        if pd.isna(monthly):
            continue
        key = AVG_WAGE_REVERSE.get(country, country)
        result[key] = float(monthly)
    return result


def resolve_hourly_min_wage(
    egg_country: str, wage_dict: dict[str, float]
) -> tuple[float | None, str]:
    wage_country = COUNTRY_ALIASES.get(egg_country, egg_country)

    hourly = wage_dict.get(wage_country)
    if hourly is not None and not pd.isna(hourly) and hourly > 0:
        return float(hourly), "Wikipedia 法定最低工资"

    if wage_country in SUPPLEMENTAL_HOURLY_WAGES:
        value, note = SUPPLEMENTAL_HOURLY_WAGES[wage_country]
        return value, f"补充：{note}"

    if egg_country in SUPPLEMENTAL_HOURLY_WAGES:
        value, note = SUPPLEMENTAL_HOURLY_WAGES[egg_country]
        return value, f"补充：{note}"

    if wage_country == "United Arab Emirates":
        return None, "无法定最低工资"

    return None, "缺少最低工资数据"


def resolve_wages(
    country: str, avg_dict: dict[str, float]
) -> tuple[float, float, str]:
    median = MEDIAN_MONTHLY_USD.get(country)
    average = avg_dict.get(country) or SUPPLEMENTAL_AVG_MONTHLY_USD.get(country)
    notes: list[str] = []

    if median is not None and average is not None:
        if country in SUPPLEMENTAL_AVG_MONTHLY_USD:
            notes.append("中位数：CEIC/各国统计局/ILO")
            notes.append("平均：ILO/各国统计局补充")
        else:
            notes.append("中位数：CEIC/各国统计局")
            notes.append("平均：Wikipedia UNECE")
    elif median is not None:
        average = median / MEDIAN_TO_MEAN_RATIO
        notes.append("中位数：CEIC/各国统计局/ILO")
        notes.append("平均：由中位数估算")
    elif average is not None:
        median = average * MEDIAN_TO_MEAN_RATIO
        notes.append("平均：Wikipedia UNECE/补充")
        notes.append("中位数：由平均估算")
    else:
        raise ValueError("缺少工资数据")

    return round(median, 2), round(average, 2), "；".join(notes)


def build_ranking() -> tuple[list[AffordabilityRow], list[str]]:
    min_wage_dict = fetch_wikipedia_min_wages()
    avg_dict = fetch_wikipedia_avg_wages()
    rows: list[AffordabilityRow] = []
    excluded: list[str] = []

    for country, dozen_usd in EGG_PRICES_USD_PER_DOZEN.items():
        try:
            median_monthly, avg_monthly, wage_notes = resolve_wages(country, avg_dict)
        except ValueError:
            excluded.append(f"{format_country_name(country)}（缺少中位数/平均工资）")
            continue

        min_hourly, min_note = resolve_hourly_min_wage(country, min_wage_dict)
        jin_price = dozen_to_jin_price(dozen_usd)
        median_ratio = median_monthly / jin_price
        min_ratio = min_hourly / jin_price if min_hourly is not None else None

        full_notes = wage_notes
        if min_hourly is None:
            full_notes += f"；最低工资：{min_note}"
        else:
            full_notes += "；最低工资：Wikipedia/补充"

        rows.append(
            AffordabilityRow(
                rank=0,
                country=country,
                median_monthly_usd=median_monthly,
                avg_monthly_usd=avg_monthly,
                min_hourly_usd=min_hourly,
                egg_dozen_usd=dozen_usd,
                egg_per_jin_usd=round(jin_price, 3),
                median_per_jin_ratio=round(median_ratio, 1),
                min_hourly_per_jin_ratio=round(min_ratio, 2) if min_ratio else None,
                median_jin_per_month=round(median_ratio, 1),
                min_jin_per_hour=round(min_ratio, 2) if min_ratio else None,
                wage_notes=full_notes,
            )
        )

    rows.sort(key=lambda r: r.median_per_jin_ratio, reverse=True)
    for i, row in enumerate(rows, start=1):
        row.rank = i
    return rows, excluded


def format_table(rows: list[AffordabilityRow]) -> str:
    lines = [
        "| 排名 | 国家/地区 | 中位数工资(月USD) | 平均工资(月USD) | 最低工资(时USD) | "
        "鸡蛋/打(USD) | 鸡蛋/斤(USD) | 中位数÷斤价 | 最低时薪÷斤价 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        min_hourly = f"{row.min_hourly_usd:.2f}" if row.min_hourly_usd is not None else "—"
        min_ratio = (
            f"{row.min_hourly_per_jin_ratio:.2f}" if row.min_hourly_per_jin_ratio is not None else "—"
        )
        lines.append(
            f"| {row.rank} | {format_country_name(row.country)} | "
            f"{row.median_monthly_usd:.0f} | {row.avg_monthly_usd:.0f} | {min_hourly} | "
            f"{row.egg_dozen_usd:.2f} | {row.egg_per_jin_usd:.3f} | "
            f"{row.median_per_jin_ratio:.1f} | {min_ratio} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="全球鸡蛋购买力排名")
    parser.add_argument(
        "-o", "--output", default="egg_affordability_ranking.md", help="输出 Markdown 文件"
    )
    args = parser.parse_args()

    rows, excluded = build_ranking()

    header = """# 全球鸡蛋购买力排名

按 **中位数月工资 ÷ 每斤鸡蛋价格** 降序排列。数值越高，表示中位数工资能买到的鸡蛋越多。

## 计算方法

- **鸡蛋价格**：12 枚 M 号鸡蛋（约 53g/枚）零售价，美元/打（[GlobalProductPrices](https://www.globalproductprices.com/rankings/egg_prices/)，2026 年 1 月）
- **每斤价格**：1 斤 = 500g，由打价换算
- **平均工资**：月 gross 平均工资，美元（[Wikipedia UNECE](https://en.wikipedia.org/wiki/List_of_countries_by_average_wage)）
- **中位数工资**：月 gross 中位数工资，美元（各国统计局 / CEIC 中位数收入）
- **最低工资**：法定时薪，美元（[Wikipedia](https://en.wikipedia.org/wiki/List_of_minimum_wages_by_country)）
- **中位数÷斤价** = 中位数月工资可购买的鸡蛋斤数（每月）
- **最低时薪÷斤价** = 最低时薪可购买的鸡蛋斤数（每小时）；无法定最低工资标为 —

"""
    excluded_note = ""
    if excluded:
        excluded_note = "\n## 未纳入排名\n\n" + "\n".join(f"- {item}" for item in excluded) + "\n"

    content = header + format_table(rows) + excluded_note
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    print(content)
    if excluded:
        print("\n未纳入:", ", ".join(excluded))


if __name__ == "__main__":
    main()
