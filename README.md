# 大一新生也能跑通的时序特征工程（北京 PM2.5 实战）

> 这不是论文导读，而是一个"照着敲就出结果"的完整项目。
> 导师的要求可以浓缩成一句话：**把时序数据的"时间列"拆成模型能用的特征，并用实验证明这些特征到底有没有用。**

---

## 0. 先明白：你不需要一下子全懂

你现在的状态很正常：看到"特征工程、周期性、滞后、滑动窗口"这些词，每个字都认识，连起来不知道在说什么。

这份教程的设计是：

1. **先让代码跑出结果**（哪怕是照着敲），建立信心；
2. 再解释"为什么这样写"；
3. 最后让你改一两个地方，做出自己的小实验；
4. 把结果写进笔记，交给导师。

记住一句话：**时序数据 = 带时间戳、按时间排好序的记录。**

---

## 网页版学习指引（推荐先看这个）

不用在文件夹里到处找文件。项目自带一个网页，把**教程、代码、图表、实验表格**放在同一页：

- 左边是目录，点一下就能看，不用记路径；
- 每个脚本页直接显示完整代码和“怎么运行”，一键复制命令；
- 顶部有搜索框（按 `/` 快速定位），比如搜“滑动窗口”“MAE”；
- “学习路线”页可以勾选 7 天进度，“导师要求对照”页把每条要求对应到具体内容。
- “项目文件”页直接读取项目文件夹：左边选文件、右边看代码或图片，改完文件点“重新读取”就能看到最新的。

打开方式（二选一）：

```powershell
# 方式一：直接双击 guide\index.html（最简单，离线可看）

# 方式二（推荐）：启一个本地网页服务，图片和表格加载最稳
powershell -ExecutionPolicy Bypass -File .\guide\start-server.ps1
# 浏览器会自动打开 http://127.0.0.1:8765/guide/index.html
# 如果提示端口被占用：powershell -ExecutionPolicy Bypass -File .\guide\start-server.ps1 -Port 8899
```

两种打开方式的能力不一样：

| 打开方式 | 能看教程/图片/表格 | 能读取项目文件夹 |
| --- | --- | --- |
| 双击 `guide\index.html` | 能 | 不能（浏览器安全限制） |
| 运行 `start-server.ps1` | 能 | 能 |

启动服务后会**自动用你电脑上的默认浏览器（Chrome / Edge 等）打开**页面；也可以自己把地址粘到浏览器里：

```text
http://127.0.0.1:8765/guide/index.html
```

嫌上面命令太长，也可以直接运行：

```powershell
python guide\server.py
```

在“项目文件”页里还有一个“选择其他文件夹”按钮，可以在 Chrome / Edge 里临时读取你电脑上任意一个文件夹（不写入、不上传）。

服务只允许本机访问（127.0.0.1），并且只能读到本项目文件夹里的内容。

网页是本地生成的，不联网也能看。改动教程文档或脚本后，重新生成一次即可：

```powershell
python guide\build_guide.py
```

---

## 知识点与代码速查手册（可打印）

项目里的知识点和代码全部集中在一份手册里：每段代码下面都有“作用”说明，按章节排好，打印出来可以直接放在手边查。

- Markdown 版：`docs/08-知识点与代码速查.md`
- PDF 版（推荐打印）：`outputs/知识点与代码速查.pdf`
- 网页版：打开学习指引，点左边「知识点速查手册」

重新生成（不需要额外装软件，用本机的 Chrome / Edge 打印）：

```powershell
python guide\build_handbook.py            # 同时生成 HTML 和 PDF
python guide\build_handbook.py --no-pdf   # 只生成 HTML
```

打印建议：A4 纸、缩放 100%。PDF 一共二十多页，每章从新的一页开始，可以用双面打印。

默认是紧凑排版，约 14 页；章节之间不强制换页，打印更省纸。如果确实需要每章另起一页，可以加参数：

```powershell
python guide\build_handbook.py --page-break-chapters
```

---

---

## 分享给同学：一键打包离线网页

如果想把教程网页发给同学，不需要对方安装 Python，也不需要启动本地服务。运行下面的命令，会生成一个可以直接分享的 zip：

```powershell
# 先激活项目虚拟环境，再执行
python guide\build_share_zip.py
```

生成结果在 `dist/时序特征工程学习指引-离线版.zip`（约 3 MB）。对方解压后双击里面的 `index.html`，就能离线看教程、代码、图表、表格和速查 PDF。

- `--no-rebuild`：不重新生成教程和 PDF，直接打包当前版本；
- `--no-zip`：只生成文件夹，不生成压缩包。

离线包不包含 `data/` 里的原始数据和处理后数据，所以体积比较小，适合分享阅读。

## 1. 导师要求 → 本项目对应位置（最重要的一张表）

| 导师要求 | 你要做的事 | 在本项目里看哪里 | 你会得到什么 |
| --- | --- | --- | --- |
| 1.1 Git 和 GitHub | 把代码传到 GitHub | `docs/01-环境与工具.md` 的 Git 部分 | 一个能打开的代码仓库 |
| 1.2 Markdown | 用 Markdown 写笔记 | `notes/学习笔记模板.md` | 特征笔记 + 实验记录 |
| 1.3 Python | 数组、列表、字典、文件、pandas、SQLite | `scripts/01`、`02`、`03` | 能看懂基础代码 |
| 2.1 找数据集 | 带时间戳的 CSV | `scripts/download_data.py` | 北京 PM2.5 数据（UTC 每小时） |
| 2.2 基础处理 | 解析时间、排序、检查缺失 | `scripts/04_load_clean.py` | `pm25_clean.csv` |
| 2.3 拆时间特征 | 年、月、日、星期、小时、是否周末 | `scripts/05_time_features.py` | 时间特征 + 特征字典 |
| 2.4 基线模型 | 用线性回归跑通 | `scripts/06_baseline_model.py` | 第一组 MAE/RMSE/R² |
| 2.5 周期编码 | 小时/星期做 sin/cos | `scripts/07_cyclic_encoding.py` | 前后对比结果 |
| 3.1 滞后和滑动 | `shift()` 和 `rolling()` | `scripts/08_lag_rolling_features.py` | 滞后/滑窗特征 |
| 3.1 防未来数据 | 理解数据泄漏 | `scripts/09_model_comparison.py` | 正确 vs 错误对照 |
| 3.2 对比效果 | 记录哪些特征有用 | `scripts/09` + `notes/实验记录模板.md` | 消融实验表 |
| 3.3 画图观察 | 原始/滑均/差分序列 | `scripts/10_plots.py` | 6 张中文图 |
| 3.4 Kaggle 练手 | 看别人的特征工程思路 | `docs/06-画图与Kaggle.md` | 复现计划 |

---

## 2. 第 0 步：把项目跑起来（Windows，约 5 分钟）

### 2.1 打开 PowerShell，进入项目文件夹

在文件夹窗口的地址栏输入 `powershell` 并回车，或者在 VS Code 里按 `Ctrl + 反引号` 打开终端。

确认你在这个文件夹：

```powershell
Get-Location
```

应该看到以 `time-series-feature-engineering` 结尾的路径。

### 2.2 创建虚拟环境

虚拟环境就是"只属于这个项目的工具箱"，不会污染电脑里的其他 Python 项目。

```powershell
python -m venv .venv
```

### 2.3 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

成功后，命令行前面会出现 `(.venv)`。

如果报"禁止运行脚本"，先执行下面这行，再重新激活：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 2.4 安装依赖

```powershell
pip install -r requirements.txt
```

### 2.5 一键跑完全部课程

```powershell
.\run_all.ps1
```

看到"全部脚本运行完成"就成功了。图片在 `outputs/figures/`，表格在 `outputs/tables/`，
网页指引也会自动重新生成到 `guide/index.html`。

> 不想一键跑，也可以按顺序一条条运行：
> ```powershell
> python scripts\download_data.py
> python scripts\01_python_basics.py
> python scripts\02_pandas_basics.py
> python scripts\03_sqlite_basics.py
> python scripts\04_load_clean.py
> python scripts\05_time_features.py
> python scripts\06_baseline_model.py
> python scripts\07_cyclic_encoding.py
> python scripts\08_lag_rolling_features.py
> python scripts\09_model_comparison.py
> python scripts\10_plots.py
> ```

---

## 3. 目录说明

```text
time-series-feature-engineering/
├─ README.md                     ← 你正在看的文件
├─ requirements.txt              ← 需要安装的 Python 库
├─ run_all.ps1                   ← 一键运行全部脚本
├─ docs/                         ← 分步教学文档
│  ├─ 00-先读我-导师要求翻译.md
│  ├─ 01-环境与工具.md
│  ├─ 02-Python零基础.md
│  ├─ 03-pandas与SQLite.md
│  ├─ 04-时序特征工程核心.md
│  ├─ 05-建模与实验.md
│  ├─ 06-画图与Kaggle.md
│  ├─ 07-交作业清单与报告模板.md
│  ├─ 08-知识点与代码速查.md
│  └─ 99-报错急救.md
├─ scripts/                      ← 按顺序运行的代码
├─ notes/                        ← 你要填的笔记模板
├─ guide/                        ← 网页版学习指引（index.html + 启动脚本）
├─ data/
│  ├─ raw/                       ← 原始数据（download_data.py 下载）
│  └─ processed/                 ← 清洗、特征工程后的数据
└─ outputs/
   ├─ 知识点与代码速查.pdf        ← 可打印的知识点手册
   ├─ figures/                   ← 6 张图
   └─ tables/                    ← 实验表格、预测结果、清洗报告
```

---

## 4. 建议的 7 天学习计划（每天 1–2 小时）

| 天数 | 学什么 | 做什么 | 当天检查点 |
| --- | --- | --- | --- |
| 第 1 天 | Git、Markdown、环境 | 跑通 `run_all.ps1`，建 GitHub 仓库 | 能在 GitHub 看到代码 |
| 第 2 天 | Python 基础 | 跑 `01`–`03`，改几个数字再跑 | 能解释 list/dict/deque |
| 第 3 天 | pandas 基础 | 跑 `02`，在笔记里写 5 个常用操作 | 能自己读一个 CSV |
| 第 4 天 | 数据清洗 + 时间特征 | 跑 `04`、`05`，看特征字典 | 能解释 UTC 和 is_weekend |
| 第 5 天 | 基线 + 周期编码 | 跑 `06`、`07`，把结果抄进实验记录 | 能解释 MAE/R² |
| 第 6 天 | 滞后、滑窗、防泄漏 | 跑 `08`、`09`，重点看错误示范 | 能说出 3 种数据泄漏 |
| 第 7 天 | 画图 + Kaggle + 总结 | 跑 `10`，挑 1 个 Kaggle 比赛看 3 篇 notebook | 交出一页实验总结 |

---

## 5. 这个项目里已经为你准备好的"成品"

- 真实数据：UCI 北京 PM2.5，43824 小时，UTC 时区；
- 完整代码：从 Python 基础到特征对照实验；
- 中文注释：每一段代码都在解释"为什么"；
- 6 张中文图：原始序列、滑均/差分、周期性、预测对比、周期编码圆、相关性热力图；
- 实验表格：模型对比、消融实验、特征系数；
- 笔记模板：按特征逐条填写，最后能直接交给导师。

---

## 6. 学习时不要做的事

- 不要一上来就推公式。先看输出，再理解公式。
- 不要复制完就跑、不看终端输出。输出里每句话都是给你看的。
- 不要用随机切分时间序列。时序数据必须按时间切。
- 不要只看 R²。还要看 MAE、RMSE 和预测曲线。
- 不要把 `_leaky` 结尾的特征放进正式模型。
- 不要因为周期编码没有大幅提升就认为它没用——要看实验条件。

---

## 7. 最终要交给导师的材料

1. GitHub 仓库链接；
2. 本项目的 README（说明怎么运行）；
3. 填好的 `notes/学习笔记模板.md`；
4. 填好的 `notes/实验记录模板.md`；
5. `outputs/figures/` 里的 6 张图；
6. 一页总结：做了什么、哪个特征有用、哪个没用、为什么、下一步做什么。

报告怎么写，看 `docs/07-交作业清单与报告模板.md`。

---

## 8. 常用命令速查

```powershell
# 进入项目
cd E:\develop\codex\github\time-series-feature-engineering

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 运行某个脚本
python scripts\05_time_features.py

# 一键运行
.\run_all.ps1

# 查看当前状态
git status

# 保存一次修改
git add .
git commit -m "完成时间特征提取"

# 第一次连接 GitHub（把网址换成你自己的）
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

---

## 9. 遇到报错怎么办

先不要删代码、不要重装 Python。

1. 把终端里**最后 10 行**完整看一遍；
2. 找到 `Error` 或 `Traceback` 那一行；
3. 打开 `docs/99-报错急救.md` 对照；
4. 还是不会，把"你运行了什么命令 + 完整报错 + 已经试过什么"发给同学或导师。

---

> 下一步：打开 `docs/00-先读我-导师要求翻译.md`，先把导师的话翻译成人话。
