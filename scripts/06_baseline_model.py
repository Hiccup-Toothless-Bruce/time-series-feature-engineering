"""第 6 课：第一个基线模型（线性回归）。

任务：用“现在这个小时的时间信息”，预测“下一个小时的 PM2.5”。

这一课的重点不是分数高不高，而是把整套流程跑通：
- 目标 y 是什么
- 特征 X 是什么
- 怎么切分训练集/测试集（时序数据必须按时间切）
- MAE、RMSE、R2 怎么看

运行：python scripts/06_baseline_model.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    load_time_features,
    print_step,
    print_title,
    regression_metrics,
)

RESULT_CSV = TABLES_DIR / "06_baseline_results.csv"
PRED_CSV = TABLES_DIR / "06_baseline_predictions.csv"

# 只允许用“预测时刻已经知道/能算出来”的列。
# 例如现在的 month/hour 是可以知道的；pm2.5 下一个小时的值不能拿来当特征。
TIME_FEATURES = ["month", "day", "hour", "dayofweek", "is_weekend", "dayofyear"]


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    print_step("1. 构造目标 y：下一个小时的 pm2.5")

    df = df.copy()
    df["pm25_next"] = df["pm2.5"].shift(-1)

    print("shift(-1) 的意思是“把整列往上提一行”：")
    demo = df[["pm2.5", "pm25_next"]].head(4)
    print(demo.to_string())
    print("\n看第 1 行：现在是 80，下一小时是 75，所以 pm25_next=75。")
    print("最后一行没有“下一个小时”，所以最后一个是 NaN，待会要删掉。")

    # 最后一行没有未来目标，删掉；特征有缺失的也删掉。
    return df.dropna(subset=["pm25_next"] + TIME_FEATURES)


def chronological_split(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    print_step("2. 按时间切分：前 80% 训练，后 20% 测试")

    split_index = int(len(df) * train_ratio)
    train = df.iloc[:split_index].copy()
    test = df.iloc[split_index:].copy()

    print(f"训练集：{len(train)} 行，时间 {train.index.min()} 到 {train.index.max()}")
    print(f"测试集：{len(test)} 行，时间 {test.index.min()} 到 {test.index.max()}")
    print("为什么不能随机切分？因为随机切分会把未来的数据混进训练集（考试漏题）。")
    return train, test


def evaluate(name: str, y_true: pd.Series, y_pred: np.ndarray, results: list[dict]) -> None:
    metrics = regression_metrics(y_true, y_pred)
    print(
        f"{name:<24} MAE={metrics['MAE']:7.3f}  "
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


def main() -> None:
    print_title("第 6 课：线性回归基线模型")

    df = load_time_features()
    df = build_target(df)
    train, test = chronological_split(df)

    x_train = train[TIME_FEATURES]
    x_test = test[TIME_FEATURES]
    y_train = train["pm25_next"]
    y_test = test["pm25_next"]

    results: list[dict] = []
    print_step("3. 两个模型对比：只会猜平均 vs 线性回归")

    # 基线 1：完全不管特征，永远预测训练集的平均值。
    dummy = DummyRegressor(strategy="mean")
    dummy.fit(x_train, y_train)
    dummy_pred = dummy.predict(x_test)
    evaluate("平均值基线", y_test, dummy_pred, results)

    # 基线 2：用时间特征做线性回归。
    model = LinearRegression()
    model.fit(x_train, y_train)
    pred = model.predict(x_test)
    evaluate("线性回归（时间特征）", y_test, pred, results)

    print_step("4. 看看线性回归到底学到了什么")
    for feature, coefficient in sorted(
        zip(TIME_FEATURES, model.coef_), key=lambda pair: abs(pair[1]), reverse=True
    ):
        print(f"  {feature:<12} 系数 = {coefficient: .4f}")
    print("\n系数正负只表示方向；系数大小会受特征单位影响，不能直接当重要性排名。")

    result_df = pd.DataFrame(results)
    result_df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n结果表已保存：{RESULT_CSV}")

    prediction_df = pd.DataFrame(
        {
            "datetime": test.index,
            "y_true": y_test.to_numpy(),
            "pred_dummy": dummy_pred,
            "pred_time_only": pred,
        }
    )
    prediction_df.to_csv(PRED_CSV, index=False, encoding="utf-8-sig")
    print(f"预测值已保存：{PRED_CSV}")

    print("\n怎么读这些指标：")
    print("- MAE：平均每次预测差多少，最好和 pm2.5 本身的平均值一起看。")
    print("- RMSE：和 MAE 类似，但会重罚离谱的大错误。")
    print("- R2：1 最好；0 约等于只会猜平均值；负数比猜平均值还差。")
    print("\n如果 R2 很低，不要沮丧，这说明“只看钟表时间”确实不够，")
    print("下一课加入周期编码，再下一课加入滞后和滑动窗口，看看能不能变好。")
    print("\n下一步：python scripts/07_cyclic_encoding.py")


if __name__ == "__main__":
    main()
