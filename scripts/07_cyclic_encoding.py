"""第 7 课：正弦/余弦周期编码，到底有没有用？

对比两种写法：
A. 直接把 hour=0..23 当成数字喂给线性回归；
B. 把 hour 拆成 hour_sin、hour_cos 两个数再喂给线性回归。

运行：python scripts/07_cyclic_encoding.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from common import (
    TABLES_DIR,
    load_time_features,
    print_step,
    print_title,
    regression_metrics,
)

RESULT_CSV = TABLES_DIR / "07_cyclic_results.csv"
PRED_CSV = TABLES_DIR / "07_cyclic_predictions.csv"

RAW_FEATURES = ["month", "day", "hour", "dayofweek", "is_weekend", "dayofyear"]
CYCLIC_FEATURES = [
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "dayofweek_sin",
    "dayofweek_cos",
    "month_sin",
    "month_cos",
]


def explain_problem() -> None:
    print_step("1. 先说清楚：为什么直接把 23 和 0 当数字很别扭？")

    demo = pd.DataFrame({"hour": [0, 1, 6, 12, 18, 22, 23]})
    demo["hour_sin"] = np.sin(2 * np.pi * demo["hour"] / 24)
    demo["hour_cos"] = np.cos(2 * np.pi * demo["hour"] / 24)
    print(demo.to_string(index=False))
    print("\n对模型来说，如果只给一个 hour 数字：")
    print("  23 和 0 相差 23，看起来隔得很远；")
    print("  但现实中 23:00 和 00:00 只差 1 小时。")
    print("用 sin/cos 把时间放到圆上后，两者坐标就非常接近。")


def make_target(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pm25_next"] = df["pm2.5"].shift(-1)
    return df.dropna(subset=["pm25_next"])


def fit_and_evaluate(
    name: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    results: list[dict],
) -> np.ndarray:
    model = LinearRegression()
    model.fit(train[features], train["pm25_next"])
    pred = model.predict(test[features])
    metrics = regression_metrics(test["pm25_next"], pred)
    print(
        f"{name:<20} MAE={metrics['MAE']:7.3f}  "
        f"RMSE={metrics['RMSE']:7.3f}  R2={metrics['R2']:7.4f}"
    )
    results.append(
        {
            "模型": name,
            "MAE": round(metrics["MAE"], 3),
            "RMSE": round(metrics["RMSE"], 3),
            "R2": round(metrics["R2"], 4),
        }
    )
    return pred


def main() -> None:
    print_title("第 7 课：周期编码对照实验")

    explain_problem()

    df = make_target(load_time_features())
    split_index = int(len(df) * 0.8)
    train = df.iloc[:split_index]
    test = df.iloc[split_index:]

    print_step("2. 同一个任务、同一段时间切分，只改特征写法")
    print(f"训练集 {len(train)} 行，测试集 {len(test)} 行。")

    results: list[dict] = []

    pred_raw = fit_and_evaluate("原始数字时间", train, test, RAW_FEATURES, results)
    pred_cyclic = fit_and_evaluate("周期编码时间", train, test, CYCLIC_FEATURES, results)

    result_df = pd.DataFrame(results)
    result_df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n结果表已保存：{RESULT_CSV}")

    prediction_df = pd.DataFrame(
        {
            "datetime": test.index,
            "y_true": test["pm25_next"].to_numpy(),
            "pred_raw": pred_raw,
            "pred_cyclic": pred_cyclic,
        }
    )
    prediction_df.to_csv(PRED_CSV, index=False, encoding="utf-8-sig")
    print(f"预测值已保存：{PRED_CSV}")

    print("\n怎么解读：")
    print("- 如果周期编码后的 MAE/RMSE 更小、R2 更大，说明它确实有帮助。")
    print("- 如果差别很小，也不代表周期编码没用，可能只是这个数据/模型没利用好它。")
    print("- 不要把结论写成“sin/cos 一定更好”，要写成“在这个数据、这个模型、这段测试期上，结果如何”。")
    print("\n下一步：python scripts/08_lag_rolling_features.py")


if __name__ == "__main__":
    main()
