#!/usr/bin/env python3
"""全球鸡蛋购买力排名：按「每小时最低工资 ÷ 每斤鸡蛋价格」排序。"""

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

# 鸡蛋价格国家名 → 最低工资表国家名
COUNTRY_ALIASES: dict[str, str] = {
    "USA": "United States",
    "UK": "United Kingdom",
    "Czechia": "Czech Republic",
    "UA Emirates": "United Arab Emirates",
    "Domin. Rep.": "Dominican Republic",
    "Ivory Coast": "Côte d'Ivoire",
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

# M 号鸡蛋约 53g；1 斤 = 500g
EGG_WEIGHT_G = 53
DOZEN_COUNT = 12
JIN_GRAMS = 500

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_minimum_wages_by_country"


@dataclass
class AffordabilityRow:
    rank: int
    country: str
    hourly_wage_usd: float
    egg_dozen_usd: float
    egg_per_jin_usd: float
    wage_per_jin_ratio: float
    jin_per_hour: float
    wage_source: str


def dozen_to_jin_price(dozen_usd: float) -> float:
    grams_per_dozen = DOZEN_COUNT * EGG_WEIGHT_G
    return dozen_usd / (grams_per_dozen / JIN_GRAMS)


def fetch_wikipedia_wages() -> dict[str, float]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; EggAffordability/1.0)"}
    response = requests.get(WIKI_URL, headers=headers, timeout=30)
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


def resolve_hourly_wage(
    egg_country: str, wage_dict: dict[str, float]
) -> tuple[float | None, str]:
    wage_country = COUNTRY_ALIASES.get(egg_country, egg_country)

    hourly = wage_dict.get(wage_country)
    if hourly is not None and not pd.isna(hourly) and hourly > 0:
        return float(hourly), "Wikipedia 法定最低工资"

    if wage_country in SUPPLEMENTAL_HOURLY_WAGES:
        value, note = SUPPLEMENTAL_HOURLY_WAGES[wage_country]
        return value, f"补充数据：{note}"

    if egg_country in SUPPLEMENTAL_HOURLY_WAGES:
        value, note = SUPPLEMENTAL_HOURLY_WAGES[egg_country]
        return value, f"补充数据：{note}"

    # UAE 等无法定最低工资的国家
    if wage_country == "United Arab Emirates":
        return None, "无法定最低工资"

    return None, "缺少工资数据"


def build_ranking() -> tuple[list[AffordabilityRow], list[str]]:
    wage_dict = fetch_wikipedia_wages()
    rows: list[AffordabilityRow] = []
    excluded: list[str] = []

    for country, dozen_usd in EGG_PRICES_USD_PER_DOZEN.items():
        hourly, source = resolve_hourly_wage(country, wage_dict)
        if hourly is None:
            excluded.append(f"{country}（{source}）")
            continue

        jin_price = dozen_to_jin_price(dozen_usd)
        ratio = hourly / jin_price
        rows.append(
            AffordabilityRow(
                rank=0,
                country=country,
                hourly_wage_usd=hourly,
                egg_dozen_usd=dozen_usd,
                egg_per_jin_usd=round(jin_price, 3),
                wage_per_jin_ratio=round(ratio, 2),
                jin_per_hour=round(ratio, 2),
                wage_source=source,
            )
        )

    rows.sort(key=lambda r: r.wage_per_jin_ratio, reverse=True)
    for i, row in enumerate(rows, start=1):
        row.rank = i
    return rows, excluded


def format_table(rows: list[AffordabilityRow]) -> str:
    lines = [
        "| 排名 | 国家/地区 | 时薪(USD) | 鸡蛋/打(USD) | 鸡蛋/斤(USD) | 时薪÷斤价 | 每小时可买(斤) |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.rank} | {row.country} | {row.hourly_wage_usd:.2f} | "
            f"{row.egg_dozen_usd:.2f} | {row.egg_per_jin_usd:.3f} | "
            f"{row.wage_per_jin_ratio:.2f} | {row.jin_per_hour:.2f} |"
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

按 **每小时最低工资 ÷ 每斤鸡蛋价格** 降序排列。数值越高，表示最低工资能买到的鸡蛋越多。

## 计算方法

- 鸡蛋价格：12 枚 M 号鸡蛋（约 53g/枚）的零售价，美元/打（[GlobalProductPrices](https://www.globalproductprices.com/rankings/egg_prices/)，2026 年 1 月）
- 每斤价格：1 斤 = 500g，由打价换算
- 最低工资：以 [Wikipedia](https://en.wikipedia.org/wiki/List_of_minimum_wages_by_country) 法定时薪为主；北欧等无全国统一最低工资的国家使用行业下限估算
- **时薪÷斤价** = 每小时最低工资可购买的鸡蛋斤数

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
