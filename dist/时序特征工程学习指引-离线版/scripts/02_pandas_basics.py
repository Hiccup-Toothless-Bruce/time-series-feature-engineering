"""第 2 课：pandas 基础。

pandas 是 Python 处理表格数据的工具。你可以把它想成“用代码操作的 Excel”。
最重要的两个概念：
- Series：一列数据
- DataFrame：一张表格（很多列）

运行：python scripts/02_pandas_basics.py
"""

from __future__ import annotations

import pandas as pd

from common import PROCESSED_DIR, load_raw_data, print_step, print_title


def describe_dataframe() -> pd.DataFrame:
    """手动造一张小表，先认识 DataFrame 长什么样。"""
    print_step("1. 手动造一张表：3 天的天气记录")

    df = pd.DataFrame(
        {
            "date": ["2026-10-01", "2026-10-02", "2026-10-03"],
            "city": ["南京", "南京", "南京"],
            "temperature": [28.0, 31.5, 24.0],
            "rain_mm": [0.0, 12.5, 3.2],
        }
    )

    print(df)
    print("\n形状（行数, 列数）：", df.shape)
    print("列名：", df.columns.tolist())
    print("\n每一列的类型：")
    print(df.dtypes)
    print("\n数值列的统计：")
    print(df.describe())
    return df


def select_and_filter(df: pd.DataFrame) -> None:
    print_step("2. 选列、筛选行、加新列")

    print('只选一列 df["temperature"]：')
    print(df["temperature"])

    print("\n只选两列：")
    print(df[["date", "temperature"]])

    print("\n筛选出下雨超过 5 毫米的行：")
    rainy = df[df["rain_mm"] > 5]
    print(rainy)

    df["is_rainy"] = df["rain_mm"] > 0
    df["temp_f"] = df["temperature"] * 9 / 5 + 32
    print("\n新增两列后：")
    print(df)


def groupby_demo() -> None:
    print_step("3. groupby：把数据分组后再算统计量")

    bigger = pd.DataFrame(
        {
            "city": ["南京", "南京", "北京", "北京", "上海"],
            "temperature": [28.0, 31.5, 22.0, 20.5, 26.0],
        }
    )
    print(bigger)
    print("\n按城市求温度平均值：")
    print(bigger.groupby("city")["temperature"].mean())


def datetime_demo() -> None:
    print_step("4. 时间列：字符串 -> datetime -> 拆出年月日时")

    stamps = pd.Series(["2026-10-08 08:00:00", "2026-10-08 09:00:00", "2026-10-09 00:00:00"])
    dt = pd.to_datetime(stamps)

    print("原来的字符串：")
    print(stamps)
    print("\n变成 datetime 后：")
    print(dt)

    result = pd.DataFrame(
        {
            "datetime": dt,
            "year": dt.dt.year,
            "month": dt.dt.month,
            "day": dt.dt.day,
            "hour": dt.dt.hour,
            "weekday": dt.dt.dayofweek,  # 0=周一, 6=周日
            "is_weekend": dt.dt.dayofweek >= 5,
        }
    )
    print("\n拆出来的时间特征：")
    print(result)


def read_real_csv() -> None:
    print_step("5. 读真正的 CSV：北京 PM2.5 原始数据")

    df = load_raw_data()
    print("形状（行数, 列数）：", df.shape)
    print("\n前 5 行：")
    print(df.head().to_string(index=False))
    print("\n每列缺多少个值：")
    print(df.isna().sum())
    print("\npm2.5 这一列的统计：")
    print(df["pm2.5"].describe())

    demo_path = PROCESSED_DIR / "pandas_demo.csv"
    df.head(100).to_csv(demo_path, index=False, encoding="utf-8-sig")
    print(f"\n前 100 行已保存到：{demo_path}")


def main() -> None:
    print_title("第 2 课：pandas 基础")

    df = describe_dataframe()
    select_and_filter(df)
    groupby_demo()
    datetime_demo()
    read_real_csv()

    print("\n完成！记住 4 个动作：读数据、看数据、选数据、造新列。")
    print("下一步：python scripts/03_sqlite_basics.py")


if __name__ == "__main__":
    main()
