"""第 9 课：把各种特征放在一起对比，并亲手演示数据泄漏。

对比模型（全部用同一段训练/测试时间，除最后两个错误示范）：
1. 平均值基线：永远猜训练集平均值
2. 持续法基线：把当前 pm2.5 直接当成下一小时预测
3. 只用原始时间特征
4. 用周期编码时间特征
5. 周期编码 + 滞后特征
6. 周期编码 + 滞后 + 滑动窗口 + 天气（完整正确版）
7. 错误示范：中心滑动窗口，偷看了未来
8. 错误示范：把答案当特征，R2 约为 1
9. 错误示范：随机切分时间序列

运行：python scripts/09_model_comparison.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from common import (
    TABLES_DIR,
    load_model_data,
    print_step,
    print_title,
    regression_metrics,
)

RESULT_CSV = TABLES_DIR / "09_model_comparison.csv"
ABLATION_CSV = TABLES_DIR / "09_ablation.csv"
PRED_CSV = TABLES_DIR / "09_test_predictions.csv"
COEF_CSV = TABLES_DIR / "09_feature_coefficients.csv"

TIME_RAW = ["month", "day", "hour", "dayofweek", "is_weekend", "dayofyear"]
TIME_CYC = [
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "dayofweek_sin",
    "dayofweek_cos",
    "month_sin",
    "month_cos",
]
LAGS = [
    "pm25_now",
    "pm25_lag1",
    "pm25_lag2",
    "pm25_lag3",
    "pm25_lag24",
    "pm25_lag168",
    "pm25_diff1",
    "pm25_diff24",
]
ROLLS = [
    "pm25_roll24_mean",
    "pm25_roll24_std",
    "pm25_roll24_max",
    "pm25_roll24_min",
    "pm25_roll168_mean",
    "pm25_roll168_std",
]
WEATHER = ["TEMP", "DEWP", "PRES", "Iws", "Is", "Ir", "TEMP_lag1", "TEMP_roll24_mean"]
LEAKY_CENTER = ["pm25_roll24_mean_center_leaky", "pm25_roll168_mean_center_leaky"]
LEAKY_ANSWER = ["pm25_answer_leaky"]


def prepare_data() -> pd.DataFrame:
    df = load_model_data()
    needed = TIME_RAW + TIME_CYC + LAGS + ROLLS + WEATHER + LEAKY_CENTER + LEAKY_ANSWER + ["pm25_next"]
    needed = list(dict.fromkeys(needed))  # 去重，保持顺序
    df = df.dropna(subset=needed)
    # 为了公平对比，错误特征在 dropna 后也一起留下；正式模型只是不选它们而已。
    return df


def evaluate(
    name: str,
    feature_desc: str,
    split_desc: str,
    y_true: pd.Series,
    y_pred: np.ndarray,
    trust: str,
    results: list[dict],
) -> None:
    metrics = regression_metrics(y_true, y_pred)
    print(
        f"{name:<28} MAE={metrics['MAE']:7.3f}  "
        f"RMSE={metrics['RMSE']:7.3f}  R2={metrics['R2']:7.4f}  [{trust}]"
    )
    results.append(
        {
            "实验": name,
            "特征": feature_desc,
            "切分方式": split_desc,
            "MAE": round(metrics["MAE"], 3),
            "RMSE": round(metrics["RMSE"], 3),
            "R2": round(metrics["R2"], 4),
            "是否可信": trust,
        }
    )


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> np.ndarray:
    model = LinearRegression()
    model.fit(train[features], train["pm25_next"])
    return model.predict(test[features])


def main() -> None:
    print_title("第 9 课：特征对照实验 + 数据泄漏演示")

    df = prepare_data()
    split_index = int(len(df) * 0.8)
    train = df.iloc[:split_index]
    test = df.iloc[split_index:]

    print(f"总行数：{len(df)}，训练集 {len(train)}，测试集 {len(test)}")
    print(f"训练时间：{train.index.min()} 到 {train.index.max()}")
    print(f"测试时间：{test.index.min()} 到 {test.index.max()}")

    y_train = train["pm25_next"]
    y_test = test["pm25_next"]
    results: list[dict] = []

    print_step("1. 正规对比（测试期都在训练期之后）")

    # 1. 平均值基线
    mean_pred = np.full(len(test), y_train.mean())
    evaluate("平均值基线", "无", "按时间 8:2", y_test, mean_pred, "可信", results)

    # 2. 持续法：直接把当前 pm2.5 当作下一小时
    persistence_pred = test["pm25_now"].to_numpy()
    evaluate("持续法基线", "当前 pm2.5", "按时间 8:2", y_test, persistence_pred, "可信", results)

    pred_time_raw = fit_predict(train, test, TIME_RAW)
    evaluate("只用原始时间特征", "month/day/hour/weekday...", "按时间 8:2", y_test, pred_time_raw, "可信", results)

    pred_time_cyc = fit_predict(train, test, TIME_CYC)
    evaluate("只用周期编码时间", "hour_sin/cos...", "按时间 8:2", y_test, pred_time_cyc, "可信", results)

    pred_lags = fit_predict(train, test, TIME_CYC + LAGS)
    evaluate("周期编码 + 滞后", "时间 + lag/diff", "按时间 8:2", y_test, pred_lags, "可信", results)

    full_features = TIME_CYC + LAGS + ROLLS + WEATHER
    pred_full = fit_predict(train, test, full_features)
    evaluate("完整正确版", "周期 + 滞后 + 滑动 + 天气", "按时间 8:2", y_test, pred_full, "可信", results)

    print_step("2. 错误示范：为什么会得到“假高分”")

    pred_center_leaky = fit_predict(train, test, TIME_CYC + LAGS + LEAKY_CENTER + WEATHER)
    evaluate("中心滑动窗口（泄漏）", "窗口包含了未来值", "按时间 8:2", y_test, pred_center_leaky, "不可信", results)

    pred_answer_leaky = fit_predict(train, test, TIME_CYC + LAGS + LEAKY_ANSWER + WEATHER)
    evaluate("把答案当特征（作弊）", "pm25_answer_leaky = 答案", "按时间 8:2", y_test, pred_answer_leaky, "不可信", results)

    # 随机切分：时间顺序被打乱，虽然有滞后列都 <= t，但它不代表“预测未来”。
    train_random, test_random = train_test_split(df, test_size=0.2, shuffle=True, random_state=42)
    pred_random = fit_predict(train_random, test_random, full_features)
    evaluate(
        "随机切分（错误做法）",
        "完整正确特征",
        "随机 8:2",
        test_random["pm25_next"],
        pred_random,
        "不可信",
        results,
    )

    print_step("3. 哪些特征组有用？做“拿掉一组”对照（消融实验）")
    ablation_specs = [
        ("完整特征", full_features),
        ("去掉滞后", TIME_CYC + ROLLS + WEATHER),
        ("去掉滑动窗口", TIME_CYC + LAGS + WEATHER),
        ("去掉天气", TIME_CYC + LAGS + ROLLS),
        ("只留时间特征", TIME_CYC),
    ]

    ablation_rows = []
    for name, features in ablation_specs:
        pred = fit_predict(train, test, features)
        metrics = regression_metrics(y_test, pred)
        print(f"  {name:<12} MAE={metrics['MAE']:7.3f}  RMSE={metrics['RMSE']:7.3f}  R2={metrics['R2']:7.4f}")
        ablation_rows.append(
            {
                "实验": name,
                "特征个数": len(features),
                "MAE": round(metrics["MAE"], 3),
                "RMSE": round(metrics["RMSE"], 3),
                "R2": round(metrics["R2"], 4),
            }
        )

    print_step("4. 标准化后的回归系数（粗看谁更重要）")
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(train[full_features])
    x_test_scaled = scaler.transform(test[full_features])
    scaled_model = LinearRegression()
    scaled_model.fit(x_train_scaled, y_train)

    coefficient_rows = []
    for feature, coefficient in zip(full_features, scaled_model.coef_):
        coefficient_rows.append({"特征": feature, "标准化系数": round(float(coefficient), 4)})
    coefficient_df = pd.DataFrame(coefficient_rows).sort_values(
        "标准化系数", key=lambda s: s.abs(), ascending=False
    )
    print(coefficient_df.head(12).to_string(index=False))
    print("\n提醒：特征之间高度相关时，单个系数会被分摊，不能把它当成严格的因果结论。")

    result_df = pd.DataFrame(results)
    result_df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(ablation_rows).to_csv(ABLATION_CSV, index=False, encoding="utf-8-sig")
    coefficient_df.to_csv(COEF_CSV, index=False, encoding="utf-8-sig")

    prediction_df = pd.DataFrame(
        {
            "datetime": test.index,
            "y_true": y_test.to_numpy(),
            "pred_persistence": persistence_pred,
            "pred_time_raw": pred_time_raw,
            "pred_time_cyc": pred_time_cyc,
            "pred_lags": pred_lags,
            "pred_full": pred_full,
            "pred_center_leaky": pred_center_leaky,
        }
    )
    prediction_df.to_csv(PRED_CSV, index=False, encoding="utf-8-sig")

    print(f"\n对比表：{RESULT_CSV}")
    print(f"消融表：{ABLATION_CSV}")
    print(f"预测值：{PRED_CSV}")
    print(f"系数表：{COEF_CSV}")

    print("\n结论怎么写（给你一个模板）：")
    print("从 MAE 看，完整正确版比只用时间特征好了约 X；加入滞后后提升最大，")
    print("说明 PM2.5 的“临近时刻值”信息量很强。中心滑动窗口分数虽然更好，")
    print("但它使用了预测时刻之后的数据，属于数据泄漏，不能作为真实效果。")
    print("\n下一步：python scripts/10_plots.py")


if __name__ == "__main__":
    main()
