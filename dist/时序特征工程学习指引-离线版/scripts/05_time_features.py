"""第 5 课：从时间戳里拆出模型能用的特征。

这一课对应导师要求 2.3：年、月、日、星期、小时、是否周末。
另外还加上“周期编码”：用 sin/cos 告诉模型“23 点和 0 点是挨着的”。

运行：python scripts/05_time_features.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import PROCESSED_DIR, TABLES_DIR, load_clean_data, print_step, print_title

OUT_CSV = PROCESSED_DIR / "pm25_time_features.csv"
DICT_CSV = TABLES_DIR / "05_feature_dictionary.csv"

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("1. 拆出年、月、日、星期、小时、是否周末")

    df = df.copy()
    index = df.index

    df["year"] = index.year
    df["month"] = index.month
    df["day"] = index.day
    df["hour"] = index.hour
    df["dayofweek"] = index.dayofweek  # 0=周一, 6=周日
    df["weekday_name"] = index.dayofweek.map(lambda x: WEEKDAY_NAMES[x])
    df["is_weekend"] = (index.dayofweek >= 5).astype(int)
    df["dayofyear"] = index.dayofyear
    df["weekofyear"] = index.isocalendar().week.to_numpy()
    df["quarter"] = index.quarter

    print("新增了：year, month, day, hour, dayofweek, weekday_name, is_weekend, dayofyear, weekofyear, quarter")
    print("注意：这份数据的时间戳是 UTC。北京本地时间 = UTC + 8；"
          "如果你想看北京作息，可以再算 (hour + 8) % 24。本教程保持 UTC 统一。")
    print("\n随机看 5 行：")
    columns = ["pm2.5", "year", "month", "day", "hour", "dayofweek", "weekday_name", "is_weekend"]
    print(df[columns].sample(5, random_state=42).sort_index().to_string())
    return df


def add_cyclic_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("2. 周期编码：把小时、星期、月份变成圆上的坐标")

    df = df.copy()

    # 为什么小时用 24、星期用 7、月份用 12？
    # 因为它们在各自的周期结束后会“回到开头”。
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    df["dayofweek_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dayofweek_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)

    df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12)
    df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12)

    print("新增了：hour_sin, hour_cos, dayofweek_sin, dayofweek_cos, month_sin, month_cos")
    print("\n看几个关键时刻，体会 23 点和 0 点在圆上是挨着的：")
    demo = pd.DataFrame(
        {
            "hour": [0, 1, 6, 12, 18, 22, 23],
        }
    )
    demo["hour_sin"] = np.sin(2 * np.pi * demo["hour"] / 24)
    demo["hour_cos"] = np.cos(2 * np.pi * demo["hour"] / 24)
    print(demo.to_string(index=False))
    return df


def save_feature_dictionary() -> None:
    print_step("3. 保存“特征字典”：每个特征怎么构造、什么意思、有什么用")

    rows = [
        ("year", "index.year", "年份", "捕捉长期变化趋势（本例里只有 5 年）"),
        ("month", "index.month", "月份 1-12", "捕捉季节变化"),
        ("day", "index.day", "几号", "通常用处不大，容易造成过拟合"),
        ("hour", "index.hour", "小时 0-23", "捕捉一天内的早晚高峰"),
        ("dayofweek", "index.dayofweek", "0=周一...6=周日", "捕捉工作日/周末差异"),
        ("is_weekend", "dayofweek >= 5", "是否周末 0/1", "简单明了地告诉模型周末效应"),
        ("dayofyear", "index.dayofyear", "1-366", "季节位置，比 month 精度更高"),
        ("weekofyear", "index.isocalendar().week", "一年中的第几周", "周期性任务、报告常用"),
        ("hour_sin", "sin(2*pi*hour/24)", "小时在圆上的横坐标", "让 23 点和 0 点距离变近"),
        ("hour_cos", "cos(2*pi*hour/24)", "小时在圆上的纵坐标", "和 hour_sin 配对使用"),
        ("dayofweek_sin", "sin(2*pi*dayofweek/7)", "星期在圆上的横坐标", "表达“周而复始”"),
        ("dayofweek_cos", "cos(2*pi*dayofweek/7)", "星期在圆上的纵坐标", "和 dayofweek_sin 配对"),
        ("month_sin", "sin(2*pi*(month-1)/12)", "月份在圆上的横坐标", "表达季节循环"),
        ("month_cos", "cos(2*pi*(month-1)/12)", "月份在圆上的纵坐标", "和 month_sin 配对"),
    ]
    dictionary = pd.DataFrame(rows, columns=["特征名", "构造方法", "含义", "可能的作用"])
    dictionary.to_csv(DICT_CSV, index=False, encoding="utf-8-sig")
    print(f"已保存：{DICT_CSV}")
    print(dictionary.to_string(index=False))


def print_group_patterns(df: pd.DataFrame) -> None:
    print_step("4. 用平均值观察周期性：不同小时/星期，PM2.5 是否不一样？")

    by_hour = df.groupby("hour")["pm2.5"].mean()
    by_weekday = df.groupby("weekday_name")["pm2.5"].mean().reindex(WEEKDAY_NAMES)

    print("每个小时的平均 PM2.5（越高说明这个时段污染越重）：")
    for hour_value, mean_value in by_hour.items():
        bar = "#" * int(mean_value / 5)
        print(f"  {hour_value:02d} 点：{mean_value:6.1f}  {bar}")

    print("\n周一至周日的平均 PM2.5：")
    for name, mean_value in by_weekday.items():
        print(f"  {name}：{mean_value:6.1f}")


def main() -> None:
    print_title("第 5 课：时间特征提取")

    df = load_clean_data()
    df = add_calendar_features(df)
    df = add_cyclic_features(df)
    save_feature_dictionary()
    print_group_patterns(df)

    print_step("5. 保存带时间特征的数据")
    df.to_csv(OUT_CSV, encoding="utf-8-sig")
    print(f"已保存：{OUT_CSV}")
    print(f"现在共有 {df.shape[1]} 列特征。")

    print("\n完成！下一步：python scripts/06_baseline_model.py")


if __name__ == "__main__":
    main()
