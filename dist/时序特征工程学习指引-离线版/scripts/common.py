"""公共工具函数。

为什么要有一个 common.py？
- 每个脚本都要找数据文件、算指标、设置中文字体，如果每份代码都复制一遍，
  改起来很容易漏。放到一个公共文件里，新手也能一眼看懂。

运行方式：这个文件不用单独运行，别的脚本会自动 import 它。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. 项目里所有重要文件夹和文件的位置
# ---------------------------------------------------------------------------
# Path(__file__) 是“当前这个 py 文件”的路径；parents[1] 就是项目根目录。
# 这样不管你在哪个文件夹里敲命令，路径都不会错。
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_CSV = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "beijing_pm25"
    / "PRSA_data_2010.1.1-2014.12.31.csv"
)
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"

# exist_ok=True 表示“文件夹已存在也不要报错”；parents=True 表示“缺上级文件夹就一起建”。
for folder in (PROCESSED_DIR, FIGURES_DIR, TABLES_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 2. 打印小工具，让终端输出更易读
# ---------------------------------------------------------------------------
def print_title(title: str) -> None:
    """打印一个醒目的标题。"""
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def print_step(step: str) -> None:
    """打印一小步的说明。"""
    print(f"\n--- {step} ---")


# ---------------------------------------------------------------------------
# 3. 读数据
# ---------------------------------------------------------------------------
def load_raw_data() -> pd.DataFrame:
    """读取最原始的 CSV，不做任何清洗。"""
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"找不到原始数据：{RAW_CSV}\n"
            "请先运行：python scripts/download_data.py"
        )
    return pd.read_csv(RAW_CSV)


def _read_csv_with_utc_index(path: Path) -> pd.DataFrame:
    """读带 datetime 列的 CSV，并把 datetime 设为 UTC 时间索引。"""
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}\n请先运行生成它的上一个脚本。")
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.set_index("datetime").sort_index()


def load_clean_data() -> pd.DataFrame:
    """读取 04_load_clean.py 生成的干净数据。"""
    return _read_csv_with_utc_index(PROCESSED_DIR / "pm25_clean.csv")


def load_time_features() -> pd.DataFrame:
    """读取 05_time_features.py 生成的时间特征数据。"""
    return _read_csv_with_utc_index(PROCESSED_DIR / "pm25_time_features.csv")


def load_model_data() -> pd.DataFrame:
    """读取 08_lag_rolling_features.py 生成的完整建模数据。"""
    return _read_csv_with_utc_index(PROCESSED_DIR / "pm25_model_data.csv")


# ---------------------------------------------------------------------------
# 4. 回归模型评估指标
# ---------------------------------------------------------------------------
def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """返回 MAE、RMSE、R2 三个指标。

    指标越小越好：MAE、RMSE；越大越好：R2（1 最好，0 约等于“只会猜平均”）。
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    return {"MAE": mae, "RMSE": rmse, "R2": r2}


# ---------------------------------------------------------------------------
# 5. 画图设置
# ---------------------------------------------------------------------------
def setup_matplotlib_chinese():
    """设置 matplotlib：不弹窗、能显示中文、负号正常。

    返回 plt，调用方写法：plt = setup_matplotlib_chinese()
    注意：必须在 import matplotlib.pyplot 之前调用 use("Agg")。
    """
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    # Windows 自带“微软雅黑”，画中文图不会变成方框。
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.bbox"] = "tight"
    return plt
