"""第 8 课：滞后（lag）和滑动窗口（rolling）特征。

先约定预测场景（非常重要）：
    站在时间 t，用截至 t 已经知道的信息，预测 t+1 时刻的 pm2.5。

所以：
- t 时刻的 pm2.5、天气，都是“已经知道”的，可以用。
- t+1 及以后的值，绝对不能作为特征，否则就是作弊（数据泄漏）。

本脚本会生成：
1. 正确特征：lag、diff、trailing rolling；
2. 故意错误特征：中心滑动窗口（会看到未来）、把答案当特征；
   它们只用于第 9 课的错误示范，不能放进正式模型。

运行：python scripts/08_lag_rolling_features.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    load_clean_data,
    print_step,
    print_title,
)

OUT_CSV = PROCESSED_DIR / "pm25_model_data.csv"
ALIGN_CSV = TABLES_DIR / "08_time_alignment.csv"

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("1. 先把第 5 课的时间特征加上")

    df = df.copy()
    index = df.index
    df["year"] = index.year
    df["month"] = index.month
    df["day"] = index.day
    df["hour"] = index.hour
    df["dayofweek"] = index.dayofweek
    df["weekday_name"] = index.dayofweek.map(lambda x: WEEKDAY_NAMES[x])
    df["is_weekend"] = (index.dayofweek >= 5).astype(int)
    df["dayofyear"] = index.dayofyear

    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dayofweek_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dayofweek_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12)
    df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12)

    print("时间特征已加上。")
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("2. 滞后特征 lag：把过去的值挪到当前行")

    df = df.copy()

    # 当前值：站在 t 时刻，pm2.5 已经测到了，当然可以用。
    df["pm25_now"] = df["pm2.5"]

    # shift(1) 表示“上一小时的值”，shift(24) 表示“昨天同一小时”。
    df["pm25_lag1"] = df["pm2.5"].shift(1)
    df["pm25_lag2"] = df["pm2.5"].shift(2)
    df["pm25_lag3"] = df["pm2.5"].shift(3)
    df["pm25_lag24"] = df["pm2.5"].shift(24)
    df["pm25_lag168"] = df["pm2.5"].shift(168)  # 24*7，上周同一小时

    # diff 是“变化量”：比昨天同一小时高了多少？
    df["pm25_diff1"] = df["pm2.5"].diff(1)
    df["pm25_diff24"] = df["pm2.5"].diff(24)

    print("新增：pm25_now, pm25_lag1/2/3/24/168, pm25_diff1, pm25_diff24")
    print("解释：lag24 能帮模型看到“昨天这个时候的污染水平”，lag168 看“上周同一时刻”。")
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("3. 滑动窗口特征 rolling：最近的均值、波动、最大值")

    df = df.copy()

    # 注意：窗口在 t 时刻结束（trailing window），里面的值都 <= t，预测 t+1 时是安全的。
    # 数据里有少量长缺口，所以 min_periods 不要求 24/168 个值全部存在：
    # 24 小时窗口至少要有 18 个值，168 小时窗口至少要有 120 个值。
    # 既不会因为个别缺失就把整行丢掉，也不会只靠一两个值硬算平均。
    window24 = df["pm2.5"].rolling(window=24, min_periods=18)
    window168 = df["pm2.5"].rolling(window=168, min_periods=120)

    df["pm25_roll24_mean"] = window24.mean()
    df["pm25_roll24_std"] = window24.std()
    df["pm25_roll24_max"] = window24.max()
    df["pm25_roll24_min"] = window24.min()

    df["pm25_roll168_mean"] = window168.mean()
    df["pm25_roll168_std"] = window168.std()

    print("新增：roll24 的 mean/std/max/min，roll168 的 mean/std。")
    print("min_periods=18 表示：24 小时窗口里至少有 18 个有效值才算；不够就填 NaN。")

    # 另外给天气变量也做几个滞后/滑动特征，体会同一套方法可以用在其他列上。
    df["TEMP_lag1"] = df["TEMP"].shift(1)
    df["TEMP_roll24_mean"] = df["TEMP"].rolling(24, min_periods=18).mean()
    print("另外加了 TEMP_lag1、TEMP_roll24_mean 作为其他变量的例子。")
    return df


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    print_step("4. 定义预测目标：下一个小时的 pm2.5")

    df = df.copy()
    df["pm25_next"] = df["pm2.5"].shift(-1)

    print("pm25_next = pm2.5.shift(-1)，也就是把未来一行的值移到当前行。")
    print("这一列是“答案”，只能当 y，不能当特征 X。")
    return df


def add_leaky_demo_features(df: pd.DataFrame) -> pd.DataFrame:
    print_step("5. 故意制造两个“错误示范”特征，供下一课打脸用")

    df = df.copy()

    # 错误 1：center=True 表示窗口中心在当前时刻，会看到 t+1、t+2... 的未来值。
    df["pm25_roll24_mean_center_leaky"] = df["pm2.5"].rolling(
        window=24, center=True, min_periods=24
    ).mean()
    df["pm25_roll168_mean_center_leaky"] = df["pm2.5"].rolling(
        window=168, center=True, min_periods=168
    ).mean()

    # 错误 2：直接把答案挪过来当特征，这是最离谱的作弊方式。
    df["pm25_answer_leaky"] = df["pm25_next"]

    print("已创建 _leaky 结尾的错误特征。")
    print("名字里带 leaky 的列禁止进入正式模型，它们只用来演示“分数为什么会假高”。")
    return df


def show_alignment(df: pd.DataFrame) -> None:
    print_step("6. 看一眼时间对齐：每一行到底用了哪些时刻的数据")

    columns = [
        "pm2.5",
        "pm25_lag1",
        "pm25_lag24",
        "pm25_roll24_mean",
        "pm25_next",
    ]
    demo = df[columns].iloc[200:206]
    print(demo.to_string())
    print("\n读表方法：")
    print("- 以某一行为当前时刻 t；")
    print("- pm25_lag1 是 t-1 的值；")
    print("- pm25_roll24_mean 是 t-23 到 t 这 24 个值的平均；")
    print("- pm25_next 是 t+1 的值，也就是我们要预测的答案。")

    demo.to_csv(ALIGN_CSV, encoding="utf-8-sig")
    print(f"\n对齐示例已保存：{ALIGN_CSV}")


def main() -> None:
    print_title("第 8 课：滞后特征 + 滑动窗口特征")

    df = load_clean_data()
    df = add_time_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df)
    df = add_target(df)
    df = add_leaky_demo_features(df)
    show_alignment(df)

    print_step("7. 保存完整建模数据")
    df.to_csv(OUT_CSV, encoding="utf-8-sig")
    print(f"已保存：{OUT_CSV}")
    print(f"总列数：{df.shape[1]}")

    print("\n完成！下一步：python scripts/09_model_comparison.py")


if __name__ == "__main__":
    main()
