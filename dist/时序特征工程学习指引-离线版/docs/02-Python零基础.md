# 02 Python 零基础：只学够用的 20%

你不需要先学完一整本 Python 书。做时序特征工程，先掌握下面这些就够了。

对应脚本：`scripts/01_python_basics.py`。

---

## 1. 变量：给数据起名字

```python
temperature = 22.5
city = "南京"
is_weekend = False
```

- `temperature` 是名字；
- `22.5`、`"南京"`、`False` 是值；
- `=` 是"把右边的值放进左边的名字"，不是数学里的等于。

---

## 2. 列表 list：一排有顺序的数据

```python
temperatures = [11.0, 12.5, 10.8, 9.6, 13.2]

print(temperatures[0])    # 11.0，Python 从 0 开始编号
print(temperatures[-1])   # 13.2，-1 表示最后一个
print(temperatures[:3])   # 前 3 个

temperatures.append(14.0) # 在末尾追加
print(max(temperatures))
print(sum(temperatures) / len(temperatures))
```

什么时候用：存一列数字。

---

## 3. 字典 dict：用名字找值

```python
row = {
    "city": "南京",
    "date": "2026-10-08",
    "temperature": 22.5,
    "is_weekend": False,
}

print(row["temperature"])  # 22.5
row["weather"] = "多云"     # 新增键
row["temperature"] = 23.1  # 修改值
```

什么时候用：存"一条记录"，每个字段有名字。

---

## 4. 队列 deque：滑动窗口的思想原型

```python
from collections import deque

window = deque(maxlen=3)

for value in [80, 75, 90, 120, 110]:
    window.append(value)
    print(list(window), sum(window) / len(window))
```

输出：

```text
[80] 80.0
[80, 75] 77.5
[80, 75, 90] 81.66666666666667
[75, 90, 120] 95.0
[90, 120, 110] 106.66666666666667
```

`maxlen=3` 表示窗口只能装 3 个：新的进来，最老的自动出去。

这就是 `rolling(3).mean()` 的直觉：**只看最近 3 个，算平均**。

---

## 5. 函数 def：把代码打包

```python
def c_to_f(celsius):
    return celsius * 9 / 5 + 32

print(c_to_f(25))   # 77.0
```

- `def` 是定义函数；
- 括号里是输入；
- `return` 是输出。

以后你会看到很多函数，例如：

```python
def regression_metrics(y_true, y_pred):
    ...
    return {"MAE": ..., "RMSE": ..., "R2": ...}
```

不要怕，先看"输入是什么、输出是什么"。

---

## 6. 循环和条件：批量处理

```python
for value in [35, 76, 120, 210]:
    if value <= 50:
        level = "优"
    elif value <= 100:
        level = "良"
    elif value <= 150:
        level = "轻度污染"
    else:
        level = "中重度污染"
    print(value, level)
```

Python 用**缩进**表示"谁属于谁"。缩进乱了，程序就报错。

---

## 7. 文件读写：把结果存下来

```python
from pathlib import Path

path = Path("outputs/tables/my_note.txt")
path.write_text("我今天学会了列表和字典。\n", encoding="utf-8")

content = path.read_text(encoding="utf-8")
print(content)
```

时间序列数据通常也是这样：读一个 CSV 进来，处理完再写一个 CSV 出去。

---

## 8. 怎么读报错信息

Python 报错看起来吓人，其实结构固定：

```text
Traceback (most recent call last):
  File "scripts/02_pandas_basics.py", line 122, in <module>
    main()
  File "scripts/02_pandas_basics.py", line 121, in main
    groupby_demo(df)
TypeError: groupby_demo() takes 0 positional arguments but 1 was given
```

看三件事：

1. **最后一行**：错误类型和原因（这里是参数多给了一个）；
2. **文件名和行号**：`scripts/02_pandas_basics.py, line 122`；
3. **箭头附近**：出错的那行代码。

新手最常见的 4 个错误：

| 报错 | 大概原因 | 怎么办 |
| --- | --- | --- |
| `IndentationError` | 缩进不对 | 检查空格，别混用 Tab 和空格 |
| `NameError` | 用了没定义的变量 | 检查变量名拼写 |
| `ModuleNotFoundError` | 没装库或没激活虚拟环境 | 激活 `.venv`，`pip install -r requirements.txt` |
| `FileNotFoundError` | 文件路径不对 | 确认先运行了生成数据的上一个脚本 |

---

## 9. 动手练习

在 `scripts/01_python_basics.py` 里改这几处，每改一次就运行一次：

1. 把 `hourly_pm25` 的最后一个数改成 200，看平均值怎么变；
2. 把 `deque(maxlen=3)` 改成 `maxlen=5`，看窗口怎么变；
3. 在 `exercises()` 里加一个数字 `7`，看最大值和排序结果；
4. 把文件里写的那句话改成你自己的名字。

---

## 10. 检查点

- [ ] 我能解释 list 和 dict 的区别；
- [ ] 我能说出 deque(maxlen=3) 在干什么；
- [ ] 我能定义并调用一个函数；
- [ ] 我知道报错要看最后一行、文件名、行号；
- [ ] 我改过代码里的数字并成功重新运行。

下一课：`03-pandas与SQLite.md`。
