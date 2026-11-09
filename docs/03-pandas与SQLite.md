# 03 pandas 与 SQLite：数据处理的两把常用工具

对应脚本：

- `scripts/02_pandas_basics.py`
- `scripts/03_sqlite_basics.py`

---

## 第一部分：pandas

pandas 是 Python 里最常用的表格处理工具。你可以把它想成"用代码操作的 Excel"。

### 1. 两个核心概念

| 概念 | 是什么 | 类比 |
| --- | --- | --- |
| `Series` | 一列数据 | Excel 里的一列 |
| `DataFrame` | 一张表，很多列 | 一整个 Excel 工作表 |

### 2. 读 CSV

```python
import pandas as pd

df = pd.read_csv("data/raw/beijing_pm25/PRSA_data_2010.1.1-2014.12.31.csv")
```

- `df` 是变量名，随便起，但大家习惯叫 `df`（DataFrame 的缩写）；
- 路径可以用相对于项目根目录的路径；
- 读进来之后，先用眼睛看，别急着建模。

### 3. 看数据的 5 个动作

```python
df.head()          # 前 5 行
df.shape           # (行数, 列数)
df.columns         # 列名
df.dtypes          # 每一列的类型
df.describe()      # 数值列的统计量
df.isna().sum()    # 每一列缺多少个值
```

**新手最容易犯的错**：拿到数据直接扔进模型。正确顺序是：先看，再洗，再用。

### 4. 选列和筛选行

```python
df["pm2.5"]                       # 选一列（Series）
df[["pm2.5", "TEMP"]]             # 选两列（DataFrame）
df[df["pm2.5"] > 100]             # 只保留 pm2.5 大于 100 的行
df[(df["pm2.5"] > 100) & (df["TEMP"] < 0)]  # 两个条件
```

注意：多个条件要用 `&`（并且）、`|`（或者），每个条件要加括号。

### 5. 造新列

```python
df["is_weekend"] = df["dayofweek"] >= 5
df["temp_f"] = df["TEMP"] * 9 / 5 + 32
```

特征工程本质上就是不断造新列。

### 6. 分组统计 groupby

```python
df.groupby("hour")["pm2.5"].mean()       # 每个小时的平均 PM2.5
df.groupby("dayofweek")["pm2.5"].mean()  # 每个星期的平均 PM2.5
```

这是观察周期性的最快方法：如果每个小时的平均值不一样，说明小时可能有预测价值。

### 7. 时间处理：字符串 → datetime → 拆特征

```python
df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
df["datetime"] = df["datetime"].dt.tz_localize("UTC")

df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month
df["day"] = df["datetime"].dt.day
df["hour"] = df["datetime"].dt.hour
df["dayofweek"] = df["datetime"].dt.dayofweek   # 0=周一
```

- `datetime` 是真正的时间类型，可以排序、相减、取年/月/日；
- `tz_localize("UTC")` 表示"这个时间本来就是 UTC"；
- 如果原始时间是北京时间 `Asia/Shanghai`，要先用 `tz_localize("Asia/Shanghai")`，再用 `tz_convert("UTC")`。

### 8. 时间索引和重采样

```python
df = df.set_index("datetime").sort_index()

daily = df["pm2.5"].resample("D").mean()   # 每天平均
weekly = df["pm2.5"].resample("W").mean()  # 每周平均
```

- `resample("D")`：按天分组；
- `resample("W")`：按周分组；
- 这是画趋势图之前常用的操作。

### 9. shift 和 rolling（先看一眼，下一课细讲）

```python
df["pm25_lag1"] = df["pm2.5"].shift(1)                 # 上一小时
df["pm25_roll24_mean"] = df["pm2.5"].rolling(24).mean() # 最近 24 小时平均
```

用之前一定先问自己：**这一行看到的数，在预测的时候真的拿得到吗？**

### 10. pandas 动手练习

在 `scripts/02_pandas_basics.py` 里改：

1. 把筛选条件从 `rain_mm > 5` 改成 `rain_mm > 1`，看结果变化；
2. 把 `groupby("city")` 改成按别的列分组；
3. 把 `df.head(100)` 改成 `df.head(500)`；
4. 在真正的数据上，自己算一遍 `df["cbwd"].value_counts()`，看风向有几种。

---

## 第二部分：SQLite

SQLite 是 Python 自带的轻量数据库，零配置。你不需要装 MySQL。

对应脚本：`scripts/03_sqlite_basics.py`。

### 1. 为什么需要数据库

CSV 适合"读进来一次性分析"；数据库适合"很多次增删改查"。

比如你要做一个天气记录系统，每天新增记录、修改、删除、查询，用数据库更合适。

### 2. 连接数据库

```python
import sqlite3

conn = sqlite3.connect("data/processed/practice.db")
```

`connect` 时如果文件不存在，会自动创建。

### 3. 建表 + 主键

```python
conn.execute("""
CREATE TABLE IF NOT EXISTS weather_notes (
    id      INTEGER PRIMARY KEY,   -- 主键：唯一身份证，不能重复
    city    TEXT    NOT NULL,
    date    TEXT    NOT NULL,
    temp    REAL,
    note    TEXT
)
""")
conn.commit()
```

**主键**：每一行的唯一编号。如果你插入两条 `id=1`，数据库会直接报错。这是好事，它帮你防止重复数据。

### 4. 增：INSERT

```python
conn.execute(
    "INSERT INTO weather_notes (id, city, date, temp, note) VALUES (?, ?, ?, ?, ?)",
    (1, "Nanjing", "2026-10-01", 28.0, "sunny"),
)
conn.commit()
```

`?` 是占位符，不要用字符串拼接，既安全又不容易出错。

### 5. 查：SELECT

```python
rows = conn.execute("SELECT * FROM weather_notes WHERE city = ?", ("Nanjing",)).fetchall()
for row in rows:
    print(row)
```

常见查询：

```sql
SELECT * FROM weather_notes ORDER BY date;
SELECT city, COUNT(*) FROM weather_notes GROUP BY city;
SELECT AVG(temp) FROM weather_notes WHERE city = 'Nanjing';
```

### 6. 改：UPDATE

```python
conn.execute("UPDATE weather_notes SET temp = ? WHERE id = ?", (29.5, 1))
conn.commit()
```

**一定要写 WHERE**。不写的话，整张表都会被改掉。

### 7. 删：DELETE

```python
conn.execute("DELETE FROM weather_notes WHERE id = ?", (4,))
conn.commit()
```

同样，**一定要写 WHERE**。

### 8. 索引

```python
conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_notes (city)")
conn.commit()
```

索引像书的目录：按 `city` 查询会更快，但会占一点空间，写入也会稍慢。
不是越多越好，常用查询列才建。

### 9. SQLite 和 pandas 怎么配合

```python
df.to_sql("pm25", conn, if_exists="replace", index=False)  # DataFrame 存进数据库
df2 = pd.read_sql("SELECT * FROM pm25 WHERE pm2.5 > 100", conn)  # 查出来变 DataFrame
```

先把数据放进数据库，再用 SQL 查询、用 pandas 分析，是实际工作中很常见的组合。

### 10. SQLite 动手练习

在 `scripts/03_sqlite_basics.py` 里：

1. 增加一条你自己的记录；
2. 查询 `temp` 大于 25 的行；
3. 把某个城市的名字改掉；
4. 删掉一条记录；
5. 给 `date` 列也建一个索引。

---

## 检查点

- [ ] 我能读一个 CSV 并打印 `shape`、列名、缺失值；
- [ ] 我能筛选行、选列、造新列；
- [ ] 我能用 `groupby` 求每小时平均；
- [ ] 我能把时间字符串转成 datetime；
- [ ] 我能说出主键和索引的作用；
- [ ] 我能写出 INSERT、SELECT、UPDATE、DELETE 四条 SQL。

下一课进入重点：`04-时序特征工程核心.md`。
