"""下载教程使用的数据集。

数据集：北京 PM2.5 数据（UCI Machine Learning Repository）
- 时间范围：2010-01-01 到 2014-12-31
- 频率：每小时一条，共 43824 条
- 时区：UTC（正好符合“时间戳统一 UTC”的要求）
- 目标列：pm2.5（PM2.5 浓度，单位微克/立方米）

如果学校网络下载失败，脚本会自动生成一份“结构一模一样的模拟数据”，
保证后面的课程仍然能跑通。模拟数据会在终端明确标注。

运行：python scripts/download_data.py
"""

from __future__ import annotations

import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "beijing_pm25"
TARGET_CSV = RAW_DIR / "PRSA_data_2010.1.1-2014.12.31.csv"
ZIP_URL = "https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip"


def download_from_uci() -> bool:
    """从 UCI 官方地址下载。成功返回 True，失败返回 False。"""
    print(f"正在下载：{ZIP_URL}")
    try:
        with urllib.request.urlopen(ZIP_URL, timeout=90) as response:
            content = response.read()

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                print("压缩包里没有 CSV 文件。")
                return False
            with zf.open(csv_names[0]) as src, open(TARGET_CSV, "wb") as dst:
                shutil.copyfileobj(src, dst)

        print(f"下载成功：{TARGET_CSV}")
        return True
    except Exception as exc:  # noqa: BLE001 - 新手教程，任何网络错误都走备用方案
        print(f"下载失败：{type(exc).__name__}: {exc}")
        return False


def make_fake_data() -> None:
    """生成一份结构相同的模拟数据，仅在真实数据下载失败时使用。"""
    print("\n改用模拟数据（真实数据下载失败时的备用方案）。")

    rng = np.random.default_rng(42)
    times = pd.date_range("2010-01-01", "2014-12-31 23:00", freq="h")
    n = len(times)
    hour = times.hour.to_numpy()
    day_of_year = times.dayofyear.to_numpy()
    weekday = times.dayofweek.to_numpy()

    # 一个简单的“像真的”PM2.5：冬季更高 + 早晚双高峰 + 随机波动
    season = 45 * np.cos(2 * np.pi * (day_of_year - 15) / 365.25)
    daily = 25 * np.sin(2 * np.pi * (hour - 7) / 24) + 18 * np.sin(
        2 * np.pi * (hour - 18) / 12
    )
    weekly = -8 * (weekday >= 5)

    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.82 * noise[i - 1] + rng.normal(0, 9)

    pm25 = np.clip(85 + season + daily + weekly + noise, 2, None)
    pm25[rng.random(n) < 0.045] = np.nan  # 故意制造一些缺失值，方便练习清洗

    temperature = 14 - 15 * np.cos(2 * np.pi * (day_of_year - 15) / 365.25) + rng.normal(0, 3, n)
    dew_point = temperature - rng.uniform(2, 15, n)
    pressure = 1012 + 10 * np.cos(2 * np.pi * day_of_year / 365.25) + rng.normal(0, 4, n)
    wind = np.abs(rng.normal(2, 1.5, n))
    rain = (rng.random(n) < 0.03).astype(int)
    snow = (rng.random(n) < 0.01).astype(int)

    df = pd.DataFrame(
        {
            "No": np.arange(1, n + 1),
            "year": times.year,
            "month": times.month,
            "day": times.day,
            "hour": times.hour,
            "pm2.5": np.round(pm25, 1),
            "DEWP": np.round(dew_point, 0).astype(int),
            "TEMP": np.round(temperature, 1),
            "PRES": np.round(pressure, 1),
            "cbwd": rng.choice(["NW", "NE", "SE", "SW", "cv"], size=n),
            "Iws": np.round(wind, 2),
            "Is": snow,
            "Ir": rain,
        }
    )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TARGET_CSV, index=False, encoding="utf-8-sig")
    print(f"模拟数据已生成：{TARGET_CSV}")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET_CSV.exists():
        print(f"数据已经存在，不重复下载：{TARGET_CSV}")
        return

    if not download_from_uci():
        make_fake_data()

    # 下载后立刻检查一遍，避免拿到空文件还不知道。
    df = pd.read_csv(TARGET_CSV, nrows=5)
    print("\n前 5 行长这样：")
    print(df.to_string(index=False))
    print("\n下一步：python scripts/04_load_clean.py")


if __name__ == "__main__":
    main()
