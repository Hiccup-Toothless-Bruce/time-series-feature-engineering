"""第 4 课：把原始 CSV 清洗成能建模的数据。

做完这一步，你会得到 data/processed/pm25_clean.csv，它满足：
1. 时间列是真正的 datetime，不是字符串；
2. 时间统一标成 UTC；
3. 按时间从早到晚排好序；
4. 没有重复时间戳；
5. 保持完整的“每小时一行”；短缺失插值，长缺失保留为空。

运行：python scripts/04_load_clean.py
"""

from __future__ import annotations

import pandas as pd

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    load_raw_data,
    print_step,
    print_title,
)

OUT_CSV = PROCESSED_DIR / "pm25_clean.csv"
REPORT_TXT = TABLES_DIR / "04_cleaning_report.txt"


def build_utc_datetime(df: pd.DataFrame) -> pd.DataFrame:
    print_step("1. 把 年/月/日/小时 四列拼成一个 UTC 时间列")

    print("原始数据里的时间是这样分开存的：")
    print(df[["year", "month", "day", "hour"]].head(3).to_string(index=False))

    # pd.to_datetime 可以把多列拼成时间；tz_localize("UTC") 表示“这个时间本来就是 UTC”。
    dt = pd.to_datetime(df[["year", "month", "day", "hour"]])
    df = df.copy()
    df["datetime"] = dt.dt.tz_localize("UTC")

    print("\n拼好以后：")
    print(df[["datetime", "pm2.5", "TEMP"]].head(3).to_string(index=False))
    print(f"\n时间范围：{df['datetime'].min()} 到 {df['datetime'].max()}")
    return df


def sort_and_check(df: pd.DataFrame) -> pd.DataFrame:
    print_step("2. 排序 + 检查重复 + 检查有没有漏掉整点")

    df = df.set_index("datetime").sort_index()
    # asfreq("h") 保证时间轴是“每个整点一行”。如果有漏掉的整点，会补一行 NaN，
    # 这样后面的 shift(24) 才真的表示 24 小时前，而不是“往前数 24 行”。
    df = df.asfreq("h")

    duplicate_count = int(df.index.duplicated().sum())
    print(f"重复的时间戳数量：{duplicate_count}")

    expected = pd.date_range(df.index.min(), df.index.max(), freq="h")
    missing_timestamps = len(expected) - len(df)
    print(f"应该有的小时数：{len(expected)}")
    print(f"实际有的行数：{len(df)}")
    print(f"中间漏掉的时间戳数量：{missing_timestamps}")

    if duplicate_count == 0 and missing_timestamps == 0:
        print("结论：时间轴完整且没有重复，可以做滞后和滑动窗口。")
    else:
        print("注意：时间轴不完整！后面的 lag/rolling 需要先补齐时间轴。")

    return df


def handle_missing_pm25(df: pd.DataFrame) -> pd.DataFrame:
    print_step("3. 处理缺失值（重点是目标列 pm2.5）")

    missing_before = int(df["pm2.5"].isna().sum())
    print(f"pm2.5 缺失数量：{missing_before} / {len(df)} （{missing_before / len(df):.2%}）")

    df = df.copy()
    # 留一个“这个值原本是不是缺失”的标记，之后可以研究缺失是否和污染有关。
    df["pm25_was_missing"] = df["pm2.5"].isna().astype(int)

    # 时间序列常用做法：用前后时刻线性插值。
    # limit=6 表示“最多连续补 6 个小时”，补不了的宁可按缺失处理。
    df["pm2.5"] = df["pm2.5"].interpolate(method="linear", limit=6, limit_direction="both")

    missing_after = int(df["pm2.5"].isna().sum())
    print(f"短缺口插值后还缺：{missing_after}（占 {missing_after / len(df):.2%}）")
    print("处理原则：短缺口（不超过 6 小时）用前后值线性插值；长缺口保留 NaN，不硬猜。")
    print("为什么不直接删掉缺失行？因为删行会让时间轴断开，")
    print("shift/rolling 里的“24 小时”就会变成“往前数 24 行”，发生错位。")
    print("所以这里保留完整小时轴；建模脚本再按实际用到的特征删除无法计算的行。")
    print("注意：插值是一种“猜”，必须在报告里写清楚，不能装作数据本来没有缺失。")
    return df


def main() -> None:
    print_title("第 4 课：加载 → 解析时间 → 排序 → 检查缺失")

    raw = load_raw_data()
    print(f"原始数据形状：{raw.shape}")

    df = build_utc_datetime(raw)
    df = sort_and_check(df)
    df = handle_missing_pm25(df)

    print_step("4. 保存清洗后的数据")
    df.to_csv(OUT_CSV, encoding="utf-8-sig")
    print(f"已保存：{OUT_CSV}")

    report_lines = [
        "北京 PM2.5 数据清洗报告",
        "=" * 40,
        f"原始行数：{len(raw)}",
        f"最终行数（保持完整小时轴）：{len(df)}",
        f"时间范围：{df.index.min()} 到 {df.index.max()}",
        "时间频率：每小时（UTC）",
        f"原始 pm2.5 缺失：{int(raw['pm2.5'].isna().sum())}",
        f"短缺口插值后剩余缺失：{int(df['pm2.5'].isna().sum())}",
        "",
        "pm2.5 统计量（缺失值不参与统计）：",
        df["pm2.5"].describe().to_string(),
        "",
        "处理说明：",
        "1. 把 year/month/day/hour 拼成 UTC datetime；",
        "2. asfreq('h') 补齐时间轴，保证每个整点一行；",
        "3. 对连续缺失不超过 6 小时的缺口做线性插值；",
        "4. 长缺口保留为 NaN，建模时按使用的特征删除无法计算的行；",
        "5. 保留 pm25_was_missing 标记，记录哪些值原本缺失。",
    ]
    REPORT_TXT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"清洗报告：{REPORT_TXT}")

    print("\n完成！下一步：python scripts/05_time_features.py")


if __name__ == "__main__":
    main()
