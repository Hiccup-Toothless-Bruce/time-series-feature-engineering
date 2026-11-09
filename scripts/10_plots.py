"""第 10 课：画图观察特征。

图比数字更容易让人看懂：
- 原始序列：整体趋势和季节变化
- 7 天滑动平均：把短期噪声抹平，看清趋势
- 差分序列：今天比昨天变化了多少，异常点更刺眼
- 小时/星期/月份平均：周期长什么样
- 周期编码圆：23 点和 0 点为什么变近了
- 预测对比：加了特征以后，预测线有没有更贴近真实线

运行：python scripts/10_plots.py
图片保存在 outputs/figures/
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import (
    FIGURES_DIR,
    TABLES_DIR,
    load_clean_data,
    load_model_data,
    load_time_features,
    print_step,
    print_title,
    setup_matplotlib_chinese,
)

plt = setup_matplotlib_chinese()

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def plot_original_series() -> None:
    print_step("1. 原始序列：整体看 5 年，再放大看 2 周")

    df = load_clean_data()
    daily = df["pm2.5"].resample("D").mean()
    zoom = df.loc["2014-06-01":"2014-06-14", "pm2.5"]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(daily.index, daily.values, color="#2c7fb8", linewidth=1)
    axes[0].set_title("PM2.5 日平均值（2010-2014）")
    axes[0].set_ylabel("PM2.5")
    axes[0].grid(alpha=0.3)

    axes[1].plot(zoom.index, zoom.values, color="#d95f02", linewidth=1)
    axes[1].set_title("放大看：2014 年 6 月前两周的每小时 PM2.5")
    axes[1].set_ylabel("PM2.5")
    axes[1].set_xlabel("UTC 时间")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    path = FIGURES_DIR / "01_原始序列与趋势.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"已保存：{path}")

    print("怎么读图：")
    print("- 上图：能看出季节变化（冬天通常更高）和长期趋势。")
    print("- 下图：能看出一天内的高低起伏，这就是“日周期”。")


def plot_rolling_and_diff() -> None:
    print_step("2. 原始序列 vs 7 天滑动平均 vs 差分")

    df = load_clean_data()
    daily = df["pm2.5"].resample("D").mean()
    rolling7 = daily.rolling(7).mean()
    diff1 = daily.diff(1)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(daily.index, daily.values, color="#aaaaaa", linewidth=1, label="每日原始值")
    axes[0].plot(rolling7.index, rolling7.values, color="#e6550d", linewidth=2.5, label="7 天滑动平均")
    axes[0].set_title("原始序列 vs 7 天滑动平均")
    axes[0].set_ylabel("PM2.5")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(diff1.index, diff1.values, color="#31a354", linewidth=1)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("差分序列：今天 - 昨天（变化量）")
    axes[1].set_ylabel("变化量")
    axes[1].set_xlabel("日期（UTC）")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    path = FIGURES_DIR / "02_滑动平均与差分.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"已保存：{path}")
    print("怎么读图：滑动平均像“降噪滤镜”；差分把“变化大不大”单独拎出来，突刺就是异常点。")


def plot_periodicity() -> None:
    print_step("3. 周期长什么样：按小时 / 星期 / 月份求平均")

    df = load_time_features()
    by_hour = df.groupby("hour")["pm2.5"].mean()
    by_weekday = df.groupby("dayofweek")["pm2.5"].mean().reindex(range(7))
    by_month = df.groupby("month")["pm2.5"].mean().reindex(range(1, 13))

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    axes[0].bar(by_hour.index, by_hour.values, color="#2c7fb8")
    axes[0].set_title("一天内的周期（按小时平均）")
    axes[0].set_xlabel("小时（UTC）")
    axes[0].set_ylabel("平均 PM2.5")
    axes[0].set_xticks(range(0, 24, 3))
    axes[0].grid(alpha=0.3, axis="y")

    axes[1].bar(range(7), by_weekday.values, color="#31a354")
    axes[1].set_title("一周内的周期（按星期平均）")
    axes[1].set_xticks(range(7), WEEKDAY_NAMES)
    axes[1].grid(alpha=0.3, axis="y")

    axes[2].bar(by_month.index, by_month.values, color="#e6550d")
    axes[2].set_title("一年内的周期（按月份平均）")
    axes[2].set_xlabel("月份")
    axes[2].set_xticks(range(1, 13))
    axes[2].grid(alpha=0.3, axis="y")

    fig.tight_layout()
    path = FIGURES_DIR / "03_周期性观察.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"已保存：{path}")
    print("怎么读图：柱子不是一条直线，说明小时/星期/月份确实包含预测信息。")


def plot_prediction_comparison() -> None:
    print_step("4. 预测对比：只看时间 vs 加上滞后滑动特征 vs 真实值")

    path = TABLES_DIR / "09_test_predictions.csv"
    if not path.exists():
        print(f"找不到 {path}，请先运行 09_model_comparison.py。")
        return

    pred = pd.read_csv(path)
    pred["datetime"] = pd.to_datetime(pred["datetime"], utc=True)
    pred = pred.set_index("datetime")

    # 测试期有大约 8500 小时，全部画会看不清，只取前 14 天。
    start = pred.index.min()
    end = start + pd.Timedelta(days=14)
    part = pred.loc[start:end]

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.plot(part.index, part["y_true"], color="black", linewidth=2, label="真实值")
    ax.plot(part.index, part["pred_time_cyc"], color="#e6550d", linewidth=1.5, alpha=0.9, label="只用周期时间特征")
    ax.plot(part.index, part["pred_full"], color="#2c7fb8", linewidth=1.5, alpha=0.9, label="完整正确特征")
    ax.set_title("测试期前 14 天：预测值 vs 真实值")
    ax.set_ylabel("PM2.5")
    ax.set_xlabel("UTC 时间")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()

    save_path = FIGURES_DIR / "04_预测对比.png"
    fig.savefig(save_path)
    plt.close(fig)
    print(f"已保存：{save_path}")
    print("怎么读图：蓝色线如果比橙色线更贴近黑线，说明滞后/滑动特征真的有用。")


def plot_cyclic_circle() -> None:
    print_step("5. 周期编码圆：23 点和 0 点在圆上其实是邻居")

    hours = np.arange(24)
    sin_values = np.sin(2 * np.pi * hours / 24)
    cos_values = np.cos(2 * np.pi * hours / 24)

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.scatter(sin_values, cos_values, c=hours, cmap="viridis", s=90, zorder=3)

    for hour, x, y in zip(hours, sin_values, cos_values):
        if hour % 2 == 0:
            ax.annotate(str(hour), (x, y), textcoords="offset points", xytext=(6, 6), fontsize=9)

    circle = plt.Circle((0, 0), 1, fill=False, color="gray", linewidth=1)
    ax.add_patch(circle)
    ax.set_aspect("equal")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_xlabel("hour_sin")
    ax.set_ylabel("hour_cos")
    ax.set_title("小时周期编码：23 点和 0 点是邻居")
    ax.grid(alpha=0.3)

    path = FIGURES_DIR / "05_周期编码圆.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"已保存：{path}")


def plot_correlation_heatmap() -> None:
    print_step("6. 相关性热力图：哪些特征和下一小时 PM2.5 关系更近")

    df = load_model_data()
    selected = [
        "pm25_next",
        "pm25_now",
        "pm25_lag24",
        "pm25_roll24_mean",
        "pm25_roll168_mean",
        "hour_sin",
        "hour_cos",
        "TEMP",
        "PRES",
    ]
    corr = df[selected].dropna().corr()

    fig, ax = plt.subplots(figsize=(9, 7.5))
    image = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(selected)), selected, rotation=45, ha="right")
    ax.set_yticks(range(len(selected)), selected)

    for i in range(len(selected)):
        for j in range(len(selected)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=8)

    fig.colorbar(image, ax=ax, shrink=0.8)
    ax.set_title("特征相关性热力图（红=正相关，蓝=负相关）")
    fig.tight_layout()

    path = FIGURES_DIR / "06_相关性热力图.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"已保存：{path}")
    print("怎么读图：相关性高不代表因果，也不能只看它选特征，但可以作为第一眼参考。")


def main() -> None:
    print_title("第 10 课：画图观察特征")

    plot_original_series()
    plot_rolling_and_diff()
    plot_periodicity()
    plot_prediction_comparison()
    plot_cyclic_circle()
    plot_correlation_heatmap()

    print(f"\n全部图片都在：{FIGURES_DIR}")
    print("建议把 6 张图贴进你的 Markdown 笔记，每张图下面写 2-3 句话：")
    print("看到了什么现象 -> 这个现象说明哪个特征可能有用 -> 实验里它到底有没有用。")


if __name__ == "__main__":
    main()
