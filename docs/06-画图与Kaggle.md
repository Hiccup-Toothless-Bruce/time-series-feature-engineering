# 06 画图与 Kaggle：用眼睛理解特征，用比赛练手

对应脚本：`scripts/10_plots.py`。
对应导师要求：3.3 画图观察特征、3.4 用 Kaggle 入门赛练手。

---

## 第一部分：怎么读你生成的 6 张图

图片都在 `outputs/figures/`。

### 图 1：原始序列与趋势（`01_原始序列与趋势.png`）

上半张是 5 年的日平均 PM2.5，下半张是放大后的两周小时数据。

要看三件事：

- 有没有长期趋势（整体上升/下降）；
- 有没有季节规律（冬天通常更高）；
- 小时级数据是不是上下波动明显。

### 图 2：滑动平均与差分（`02_滑动平均与差分.png`）

- 灰色线：每天的原始值，抖动很大；
- 橙色线：7 天滑动平均，把短期噪声抹平，趋势更清楚；
- 绿色线：差分（今天 − 昨天），正数表示升高，负数表示降低；
- 差分图上的大尖刺就是异常变化点。

### 图 3：周期性观察（`03_周期性观察.png`）

三张柱状图分别是按小时、按星期、按月份的平均 PM2.5。

怎么判断有没有周期：**柱子高低是否明显不同**。
如果所有柱子一样高，说明这个时间维度没有信息；如果高低差很多，说明它可能有用。

注意：这张图用的是 UTC 小时。UTC 08:00 是北京时间 16:00。
如果你觉得峰值时间和直觉对不上，先想一想时区。

### 图 4：预测对比（`04_预测对比.png`）

- 黑线：真实值；
- 橙线：只用周期时间特征的预测，几乎是平的；
- 蓝线：完整特征（滞后 + 滑动 + 天气）的预测，紧跟黑线。

这张图最直观地说明了：**滞后特征让模型从"猜平均"变成了"跟着走"。**

### 图 5：周期编码圆（`05_周期编码圆.png`）

23 个点分布在圆上，每个点是一个小时。0 点和 23 点在圆上紧挨着。
这就是 sin/cos 编码想要表达的："小时是一个循环，不是一条直线。"

### 图 6：相关性热力图（`06_相关性热力图.png`）

红色是正相关，蓝色是负相关。数值越接近 ±1 关系越强。

第一行/第一列是 `pm25_next`（目标），可以看看哪些特征和它关系最近。
但要记住：**相关不代表因果，也不能只凭相关性选特征。**

---

## 第二部分：matplotlib 最小必要知识

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(dates, values, label="PM2.5")
ax.set_title("标题")
ax.set_xlabel("日期")
ax.set_ylabel("数值")
ax.legend()
ax.grid(alpha=0.3)
fig.savefig("outputs/figures/my_plot.png")
plt.close(fig)
```

- `fig`：整张画布；
- `ax`：具体的坐标轴；
- `plot`：画折线；
- `bar`：画柱状图；
- `scatter`：画散点；
- `label` + `legend`：图例；
- `savefig`：保存成图片。

中文显示需要设置字体（本项目已经在 `scripts/common.py` 里统一设置）：

```python
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
```

---

## 第三部分：Kaggle 入门赛实战

### 1. 注册

打开 <https://www.kaggle.com>，用邮箱注册。免费。

### 2. 找时间序列相关的 Playground 比赛

路径：

```text
Competitions → 筛选 Playground → 搜索 time series / forecasting / sales
```

也可以直接搜索这些关键词：

- `Store Sales Time Series Forecasting`
- `Bike Sharing Demand`
- `Tabular Playground Series`（每一期主题不同，找时间序列相关的）
- `Web Traffic Time Series Forecasting`
- `M5 Forecasting`（经典，但可能已经结束/不可提交）

注意：Kaggle 比赛会更新，具体名称和是否开放提交以网站为准。
你要找的是：**有明确时间列、有训练集和测试集、评价指标清楚**的比赛。

### 3. 看懂一个比赛页面

| 页面 | 你要看什么 |
| --- | --- |
| Overview | 任务是什么、规则、时间线 |
| Data | 有哪些文件、每列什么意思、训练/测试怎么分 |
| Evaluation | 用什么指标（MAE、RMSE、SMAPE…） |
| Code | 别人的公开 notebook |
| Discussion | 常见坑、数据问题 |

### 4. 先做一个最笨的提交

不要一上来就冲高分。先做：

1. 读 `sample_submission.csv`，看提交格式；
2. 用训练集的平均值，或"最后一个已知值"作为预测；
3. 生成提交文件，上传一次；
4. 记住这个分数，它是你的基线。

### 5. 读 3 篇公开 notebook 的方法

不要从头到尾读代码，直接搜关键词：

```text
feature engineering
lag
rolling
shift
cyclical
sin
cos
date
weekday
holiday
```

每读到一种特征，就问自己：

1. 他怎么构造的？
2. 为什么他认为这个特征有用？
3. 我能不能在自己的数据上复现？
4. 复现后指标变化多少？

把答案写进 `notes/学习笔记模板.md`。

### 6. 复现一个特征的完整流程

1. 在自己的数据上写构造代码；
2. 确认没有用到未来数据；
3. 保持模型和切分方式不变，只加这一个特征；
4. 记录加之前/之后的 MAE；
5. 写下结论：有用、没用、还是不确定。

### 7. 关于排名

导师的要求是"不追求排名，着重看别人的特征工程思路"。
所以：

- 排名 3000 名不丢人；
- 能说清楚"我复现了 lag 特征，MAE 从 X 降到 Y"才是真本事；
- 抄代码不理解，面试/答辩一问就露馅。

### 8. 常见的 Kaggle 时间序列特征清单

| 类别 | 特征 |
| --- | --- |
| 日历 | year、month、day、weekday、weekofyear、is_weekend、is_holiday |
| 周期 | hour_sin/cos、weekday_sin/cos、month_sin/cos |
| 滞后 | lag1、lag2、lag7、lag14、lag28、lag365 |
| 滑动 | rolling mean/std/min/max（7、14、28 天） |
| 差分 | diff1、diff7、pct_change |
| 其他变量 | 天气、促销、油价、节假日 |
| 静态信息 | 店铺 id、商品 id、城市（类别特征） |

注意：具体用哪些，取决于你的数据频率和业务含义。小时数据看 24/168，日数据看 7/30/365。

### 9. Kaggle 检查点

- [ ] 我注册了 Kaggle；
- [ ] 我找到了一个时间序列相关的 Playground 比赛；
- [ ] 我看懂了数据文件和提交格式；
- [ ] 我做出了一次基线提交；
- [ ] 我读了至少 3 篇公开 notebook；
- [ ] 我复现了至少 1 个特征并记录了指标变化；
- [ ] 我没有直接复制别人的代码当自己的作业。

---

## 第四部分：把 Kaggle 学到的东西搬回本项目

如果你在 Kaggle 学到了新特征，可以回来改 `scripts/08_lag_rolling_features.py`：

1. 加一个新特征；
2. 重新运行 `09_model_comparison.py`；
3. 看消融实验有没有变化；
4. 把结论写进笔记。

这就是一个完整的"学习 → 复现 → 验证 → 记录"闭环。
导师想看到的正是这个，而不是一个漂亮的分数。

---

下一课：`07-交作业清单与报告模板.md`。
