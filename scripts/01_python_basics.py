"""第 1 课：Python 零基础速通。

这一课只讲后面做特征工程一定会用到的 6 样东西：
1. 变量和列表 list
2. 字典 dict
3. 队列 deque
4. 函数 def
5. 文件读写
6. 循环和条件

运行：python scripts/01_python_basics.py
"""

from __future__ import annotations

from collections import deque

from common import TABLES_DIR, print_step, print_title


# ---------------------------------------------------------------------------
# 1. 列表 list：一排有顺序的数据
# ---------------------------------------------------------------------------
def lesson_list() -> None:
    print_step("1. 列表 list：就像一排储物柜，每个格子有编号")

    # 注意：Python 的编号从 0 开始，不是从 1 开始。
    temperatures = [11.0, 12.5, 10.8, 9.6, 13.2]
    print("原始列表：", temperatures)
    print("第 1 个元素 temperatures[0] =", temperatures[0])
    print("最后 1 个元素 temperatures[-1] =", temperatures[-1])
    print("前 3 个元素 temperatures[:3] =", temperatures[:3])

    temperatures.append(14.0)
    print("append(14.0) 之后：", temperatures)
    print("最大值 =", max(temperatures), "  平均值 =", sum(temperatures) / len(temperatures))


# ---------------------------------------------------------------------------
# 2. 字典 dict：用名字找值，就像通讯录
# ---------------------------------------------------------------------------
def lesson_dict() -> None:
    print_step("2. 字典 dict：用名字（键）找值")

    row = {
        "city": "南京",
        "date": "2026-10-08",
        "temperature": 22.5,
        "is_weekend": False,
    }
    print("一整条记录：", row)
    print('row["temperature"] =', row["temperature"])

    row["weather"] = "多云"  # 新增一个键
    row["temperature"] = 23.1  # 修改已有的键
    print("修改后：", row)

    for key, value in row.items():
        print(f"  {key} -> {value}")


# ---------------------------------------------------------------------------
# 3. 队列 deque：只保留最近 N 个值，天然适合“滑动窗口”
# ---------------------------------------------------------------------------
def lesson_queue() -> None:
    print_step("3. 队列 deque：进门排队，先来先走；只留最近 3 个数")

    window = deque(maxlen=3)
    hourly_pm25 = [80, 75, 90, 120, 110, 95]

    for hour, value in enumerate(hourly_pm25):
        window.append(value)
        average = sum(window) / len(window)
        print(f"第 {hour} 小时 PM2.5={value:>3}，窗口={list(window)}，窗口均值={average:.1f}")

    print("\n这就是“滑动窗口”：每一步丢掉最老的数，加入最新的数，再算统计量。")


# ---------------------------------------------------------------------------
# 4. 函数 def：把一段代码打包，起个名字反复用
# ---------------------------------------------------------------------------
def c_to_f(celsius: float) -> float:
    """把摄氏度换成华氏度。"""
    return celsius * 9 / 5 + 32


def lesson_function() -> None:
    print_step("4. 函数 def：输入 -> 处理 -> 输出")

    for celsius in [0, 10, 25, 37]:
        print(f"{celsius:>3} 摄氏度 = {c_to_f(celsius):>5.1f} 华氏度")


# ---------------------------------------------------------------------------
# 5. 文件读写：把结果存下来，下次还能用
# ---------------------------------------------------------------------------
def lesson_file() -> None:
    print_step("5. 文件读写：写出去，再读回来")

    note_path = TABLES_DIR / "python_notes.txt"
    note_path.write_text(
        "我今天学会了列表、字典、队列、函数和文件读写。\n",
        encoding="utf-8",
    )
    print(f"已写入：{note_path}")
    print("读回来：", note_path.read_text(encoding="utf-8").strip())

    # 追加一行（\n 表示换行）
    with note_path.open("a", encoding="utf-8") as f:
        f.write("下一步：用 pandas 读真正的 CSV 数据。\n")
    print("追加后文件内容：")
    print(note_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 6. 循环 + 条件：自动给每条记录打标签
# ---------------------------------------------------------------------------
def lesson_loop_and_if() -> None:
    print_step("6. 循环 + 条件：给每个 PM2.5 数值分级")

    hourly_pm25 = [35, 76, 120, 210, 45, 90]
    for value in hourly_pm25:
        if value <= 50:
            level = "优"
        elif value <= 100:
            level = "良"
        elif value <= 150:
            level = "轻度污染"
        else:
            level = "中重度污染"
        print(f"PM2.5={value:>3} -> {level}")


# ---------------------------------------------------------------------------
# 小练习：先自己想，再看运行结果对照
# ---------------------------------------------------------------------------
def exercises() -> None:
    print_step("小练习（先暂停，自己写一写再看答案）")

    print("题目 1：把 [3, 1, 4, 1, 5] 排序后取最大值。")
    numbers = [3, 1, 4, 1, 5]
    numbers.sort()
    print("答案 1：排序后 =", numbers, "，最大值 =", numbers[-1])

    print("\n题目 2：统计一句话里每个单词出现的次数。")
    sentence = "time time series window time"
    counts: dict[str, int] = {}
    for word in sentence.split():
        counts[word] = counts.get(word, 0) + 1
    print("答案 2：", counts)

    print("\n题目 3：用 deque 算最近 3 个数的平均值。")
    window = deque(maxlen=3)
    for value in [10, 20, 30, 40]:
        window.append(value)
    print("答案 3：最后一个窗口 =", list(window), "，均值 =", sum(window) / len(window))


def main() -> None:
    print_title("第 1 课：Python 零基础速通")
    print("这一课不需要背，先看代码 -> 运行 -> 改数字再运行。")

    lesson_list()
    lesson_dict()
    lesson_queue()
    lesson_function()
    lesson_file()
    lesson_loop_and_if()
    exercises()

    print("\n完成！你刚刚已经用到了后面做滑动窗口的核心思路。")
    print("下一步：python scripts/02_pandas_basics.py")


if __name__ == "__main__":
    main()
