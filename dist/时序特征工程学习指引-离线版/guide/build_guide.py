"""生成一个静态学习指引网页：guide/index.html

特点：
- 不需要联网（除了页面里的图片路径，也都是本地文件）；
- 左边是导航，右边直接读教程、看代码、看实验结果；
- 支持搜索、复制命令、勾选学习进度；
- 打开方式：guide/index.html，或用 guide/start-server.ps1 启动本地网页服务。

运行：python guide/build_guide.py
"""

from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

import markdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUIDE_DIR = PROJECT_ROOT / "guide"
OUTPUT_HTML = GUIDE_DIR / "index.html"

# ---------------------------------------------------------------------------
# 1. 页面里要展示的教程
# ---------------------------------------------------------------------------
DOCS: list[dict[str, str]] = [
    {
        "id": "overview",
        "title": "项目总览",
        "group": "开始",
        "icon": "home",
        "file": "README.md",
        "summary": "项目做什么、怎么运行、7 天学习计划。",
    },
    {
        "id": "req",
        "title": "导师要求翻译",
        "group": "开始",
        "icon": "list-checks",
        "file": "docs/00-先读我-导师要求翻译.md",
        "summary": "把导师的每条要求翻译成'我要做什么'。",
    },
    {
        "id": "env",
        "title": "环境与工具",
        "group": "教程",
        "icon": "settings",
        "file": "docs/01-环境与工具.md",
        "summary": "Python、venv、Git、GitHub、Markdown 最小必要操作。",
    },
    {
        "id": "python",
        "title": "Python 零基础",
        "group": "教程",
        "icon": "braces",
        "file": "docs/02-Python零基础.md",
        "summary": "list、dict、deque、函数、文件读写和报错阅读。",
    },
    {
        "id": "pandas-sqlite",
        "title": "pandas 与 SQLite",
        "group": "教程",
        "icon": "table-2",
        "file": "docs/03-pandas与SQLite.md",
        "summary": "读 CSV、筛选、groupby、时间处理、SQL 增删改查。",
    },
    {
        "id": "feature-core",
        "title": "时序特征工程核心",
        "group": "教程",
        "icon": "calendar-clock",
        "file": "docs/04-时序特征工程核心.md",
        "summary": "UTC、日历特征、sin/cos、lag、rolling、数据泄漏。",
    },
    {
        "id": "modeling",
        "title": "建模与实验",
        "group": "教程",
        "icon": "line-chart",
        "file": "docs/05-建模与实验.md",
        "summary": "线性回归、按时间切分、MAE/RMSE/R²、结果解读。",
    },
    {
        "id": "plots-kaggle",
        "title": "画图与 Kaggle",
        "group": "教程",
        "icon": "image",
        "file": "docs/06-画图与Kaggle.md",
        "summary": "6 张图怎么读，以及 Kaggle 入门赛的练法。",
    },
    {
        "id": "handbook",
        "title": "知识点速查手册",
        "group": "教程",
        "icon": "book-marked",
        "file": "docs/08-知识点与代码速查.md",
        "summary": "所有知识点 + 代码 + 一句话作用，可打印；PDF 在 outputs 文件夹。",
    },
    {
        "id": "homework",
        "title": "交作业清单与报告模板",
        "group": "教程",
        "icon": "clipboard-check",
        "file": "docs/07-交作业清单与报告模板.md",
        "summary": "交付清单、一页报告模板、五分钟汇报提纲。",
    },
    {
        "id": "errors",
        "title": "报错急救",
        "group": "教程",
        "icon": "life-buoy",
        "file": "docs/99-报错急救.md",
        "summary": "最常见报错的原因和解决办法。",
    },
    {
        "id": "note-feature",
        "title": "学习笔记模板",
        "group": "笔记",
        "icon": "notebook-pen",
        "file": "notes/学习笔记模板.md",
        "summary": "每个特征一张表：构造、含义、实验证据、结论。",
    },
    {
        "id": "note-experiment",
        "title": "实验记录模板",
        "group": "笔记",
        "icon": "flask-conical",
        "file": "notes/实验记录模板.md",
        "summary": "模型对比表、消融实验表、结论模板。",
    },
]

# ---------------------------------------------------------------------------
# 2. 页面里要展示的脚本
# ---------------------------------------------------------------------------
SCRIPTS: list[dict[str, str]] = [
    {
        "id": "download",
        "title": "下载数据集",
        "group": "准备",
        "file": "scripts/download_data.py",
        "cmd": "python scripts\\download_data.py",
        "summary": "下载 UCI 北京 PM2.5 数据；网络失败时自动生成结构相同的模拟数据。",
    },
    {
        "id": "python-basics",
        "title": "01 Python 基础",
        "group": "基础",
        "file": "scripts/01_python_basics.py",
        "cmd": "python scripts\\01_python_basics.py",
        "summary": "列表、字典、deque 队列、函数、文件读写、循环和条件。",
    },
    {
        "id": "pandas-basics",
        "title": "02 pandas 基础",
        "group": "基础",
        "file": "scripts/02_pandas_basics.py",
        "cmd": "python scripts\\02_pandas_basics.py",
        "summary": "DataFrame、选列、筛行、groupby、datetime、读真实 CSV。",
    },
    {
        "id": "sqlite-basics",
        "title": "03 SQLite 基础",
        "group": "基础",
        "file": "scripts/03_sqlite_basics.py",
        "cmd": "python scripts\\03_sqlite_basics.py",
        "summary": "建表、增删改查、主键、索引，全部用 Python 自带的 sqlite3。",
    },
    {
        "id": "load-clean",
        "title": "04 加载与清洗",
        "group": "数据处理",
        "file": "scripts/04_load_clean.py",
        "cmd": "python scripts\\04_load_clean.py",
        "summary": "拼 UTC 时间、排序、检查重复和缺失、保持完整小时时间轴。",
    },
    {
        "id": "time-features",
        "title": "05 时间特征提取",
        "group": "特征工程",
        "file": "scripts/05_time_features.py",
        "cmd": "python scripts\\05_time_features.py",
        "summary": "年、月、日、星期、小时、是否周末，以及 sin/cos 周期编码。",
    },
    {
        "id": "baseline",
        "title": "06 基线模型",
        "group": "建模实验",
        "file": "scripts/06_baseline_model.py",
        "cmd": "python scripts\\06_baseline_model.py",
        "summary": "平均值基线 vs 线性回归；按时间前 80% 训练、后 20% 测试。",
    },
    {
        "id": "cyclic",
        "title": "07 周期编码对照",
        "group": "建模实验",
        "file": "scripts/07_cyclic_encoding.py",
        "cmd": "python scripts\\07_cyclic_encoding.py",
        "summary": "只改特征写法：原始小时/星期 vs sin/cos 周期编码。",
    },
    {
        "id": "lag-rolling",
        "title": "08 滞后与滑动窗口",
        "group": "特征工程",
        "file": "scripts/08_lag_rolling_features.py",
        "cmd": "python scripts\\08_lag_rolling_features.py",
        "summary": "shift 造 lag，rolling 造均值/波动/极值，并故意造出 _leaky 错误特征。",
    },
    {
        "id": "compare",
        "title": "09 模型对比与泄漏演示",
        "group": "建模实验",
        "file": "scripts/09_model_comparison.py",
        "cmd": "python scripts\\09_model_comparison.py",
        "summary": "多组特征对照、消融实验、中心滑窗泄漏、把答案当特征。",
    },
    {
        "id": "plots",
        "title": "10 画图观察特征",
        "group": "可视化",
        "file": "scripts/10_plots.py",
        "cmd": "python scripts\\10_plots.py",
        "summary": "原始序列、滑动平均、差分、周期性、预测对比、周期编码圆、相关性热力图。",
    },
    {
        "id": "common",
        "title": "公共工具 common.py",
        "group": "公共",
        "file": "scripts/common.py",
        "cmd": "（不用单独运行，被其他脚本 import）",
        "summary": "路径、读数据、MAE/RMSE/R²、中文画图设置。",
    },
]

# ---------------------------------------------------------------------------
# 3. 图片和表格
# ---------------------------------------------------------------------------
FIGURES = [
    {
        "file": "outputs/figures/01_原始序列与趋势.png",
        "title": "原始序列与趋势",
        "caption": "上图是 5 年日平均，下图是两周小时数据。先看趋势和日周期。",
    },
    {
        "file": "outputs/figures/02_滑动平均与差分.png",
        "title": "滑动平均与差分",
        "caption": "7 天滑动平均像降噪滤镜；差分把变化量和异常点单独拎出来。",
    },
    {
        "file": "outputs/figures/03_周期性观察.png",
        "title": "周期性观察",
        "caption": "按小时、星期、月份求平均。柱子高低明显，说明时间包含预测信号。",
    },
    {
        "file": "outputs/figures/04_预测对比.png",
        "title": "预测对比",
        "caption": "黑线真实值，橙线只用时间特征（几乎是平的），蓝线完整特征（紧跟真实值）。",
    },
    {
        "file": "outputs/figures/05_周期编码圆.png",
        "title": "周期编码圆",
        "caption": "23 点和 0 点在圆上相邻，这就是 sin/cos 编码想表达的事情。",
    },
    {
        "file": "outputs/figures/06_相关性热力图.png",
        "title": "相关性热力图",
        "caption": "和下一小时 PM2.5 的线性相关。相关不等于因果，只能作为第一眼参考。",
    },
]

TABLES = [
    {
        "id": "comparison",
        "title": "模型对比：哪些特征有用",
        "file": "outputs/tables/09_model_comparison.csv",
        "description": "同一段时间切分，只改特征。注意区分'可信'和'不可信'的结论。",
        "max_rows": 50,
    },
    {
        "id": "ablation",
        "title": "消融实验：拿掉一组会怎样",
        "file": "outputs/tables/09_ablation.csv",
        "description": "从完整特征里拿掉一组，看 MAE/R² 变差多少。",
        "max_rows": 50,
    },
    {
        "id": "coefficients",
        "title": "标准化回归系数",
        "file": "outputs/tables/09_feature_coefficients.csv",
        "description": "粗略看哪些特征和预测关系更大；特征相关时不能当因果。",
        "max_rows": 50,
    },
    {
        "id": "feature-dict",
        "title": "特征字典",
        "file": "outputs/tables/05_feature_dictionary.csv",
        "description": "每个时间特征的构造方法、含义和可能作用。",
        "max_rows": 50,
    },
    {
        "id": "alignment",
        "title": "时间对齐示例",
        "file": "outputs/tables/08_time_alignment.csv",
        "description": "看清 lag1、lag24、roll24_mean、pm25_next 分别对应哪些时刻。",
        "max_rows": 20,
    },
    {
        "id": "baseline-results",
        "title": "基线模型结果",
        "file": "outputs/tables/06_baseline_results.csv",
        "description": "平均值基线 vs 只用时间特征的线性回归。",
        "max_rows": 20,
    },
    {
        "id": "cyclic-results",
        "title": "周期编码结果",
        "file": "outputs/tables/07_cyclic_results.csv",
        "description": "原始数字时间 vs sin/cos 周期编码。",
        "max_rows": 20,
    },
    {
        "id": "predictions",
        "title": "预测结果预览（前 20 行）",
        "file": "outputs/tables/09_test_predictions.csv",
        "description": "测试期的真实值、持续法、只用时间、完整特征、泄漏版的预测对比。",
        "max_rows": 20,
    },
]

CONCEPTS = [
    {
        "icon": "globe",
        "title": "UTC",
        "text": "世界统一时间，避免时区混乱。北京时间 = UTC + 8。",
        "route": "#doc-feature-core",
    },
    {
        "icon": "refresh-cw",
        "title": "周期编码",
        "text": "用 sin/cos 把小时、星期放到圆上，让 23 点和 0 点变成邻居。",
        "route": "#doc-feature-core",
    },
    {
        "icon": "history",
        "title": "滞后 lag",
        "text": "shift(1) 是上一小时，shift(24) 是昨天同一小时。",
        "route": "#doc-feature-core",
    },
    {
        "icon": "move-horizontal",
        "title": "滑动窗口 rolling",
        "text": "最近 24/168 小时的均值、波动、最大值、最小值。",
        "route": "#doc-feature-core",
    },
    {
        "icon": "shield-alert",
        "title": "数据泄漏",
        "text": "用了 t+1 或更晚的信息，测试分数会假高。",
        "route": "#doc-feature-core",
    },
    {
        "icon": "target",
        "title": "基线",
        "text": "平均值和持续法。复杂模型必须先打赢它们。",
        "route": "#doc-modeling",
    },
]

ROADMAP = [
    {
        "day": "第 1 天",
        "title": "环境、Git、Markdown",
        "desc": "跑通一键脚本，建 GitHub 仓库，学会写笔记。",
        "route": "#doc-env",
        "key": "day1",
    },
    {
        "day": "第 2 天",
        "title": "Python 基础",
        "desc": "跑 01–03，改几个数字再运行，理解 list/dict/deque。",
        "route": "#script-python-basics",
        "key": "day2",
    },
    {
        "day": "第 3 天",
        "title": "pandas 与 SQLite",
        "desc": "会读 CSV、筛选、分组、时间处理，会写四条 SQL。",
        "route": "#doc-pandas-sqlite",
        "key": "day3",
    },
    {
        "day": "第 4 天",
        "title": "清洗与时间特征",
        "desc": "跑 04、05，理解 UTC、缺失值、is_weekend、sin/cos。",
        "route": "#script-time-features",
        "key": "day4",
    },
    {
        "day": "第 5 天",
        "title": "基线模型与周期编码",
        "desc": "跑 06、07，理解 MAE/RMSE/R²，把结果抄进实验记录。",
        "route": "#doc-modeling",
        "key": "day5",
    },
    {
        "day": "第 6 天",
        "title": "滞后、滑动窗口、防泄漏",
        "desc": "跑 08、09，重点看中心滑窗和'把答案当特征'的错误示范。",
        "route": "#script-compare",
        "key": "day6",
    },
    {
        "day": "第 7 天",
        "title": "画图、Kaggle、总结",
        "desc": "跑 10，读 3 篇 Kaggle notebook，写一页实验总结。",
        "route": "#doc-plots-kaggle",
        "key": "day7",
    },
]

REQUIREMENTS = [
    ("1.1 Git 和 GitHub", "上传代码到仓库", "#doc-env"),
    ("1.2 Markdown", "写特征笔记和实验记录", "#doc-note-feature"),
    ("1.3 Python", "列表、字典、文件、pandas、SQLite", "#script-python-basics"),
    ("2.1 数据集", "带时间戳的 CSV", "#script-download"),
    ("2.2 基础处理", "解析时间、排序、检查缺失", "#script-load-clean"),
    ("2.3 时间特征", "年、月、日、星期、小时、是否周末", "#script-time-features"),
    ("2.4 基线模型", "线性回归基线", "#script-baseline"),
    ("2.5 周期编码", "小时/星期 sin/cos 对照", "#script-cyclic"),
    ("3.1 滞后和滑窗", "shift 和 rolling，防止未来数据", "#script-lag-rolling"),
    ("3.2 对比效果", "记录哪些特征有用", "#table-comparison"),
    ("3.3 画图观察", "原始、滑均、差分序列", "#figures"),
    ("3.4 Kaggle", "看别人的特征工程思路", "#doc-plots-kaggle"),
]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def read_text(path: Path) -> str:
    """读文本，优先 UTF-8，失败再试 GBK。"""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="replace")


def strip_tags(value: str) -> str:
    """粗略去掉 HTML 标签，用于搜索索引。"""
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def iter_project_files(limit: int = 400) -> list[dict[str, str]]:
    """列出项目里的文件，给搜索框做索引（跳过虚拟环境和缓存目录）。"""
    skip = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode", "dist"}
    result: list[dict[str, str]] = []
    for path in sorted(PROJECT_ROOT.rglob("*")):
        if len(result) >= limit:
            break
        if not path.is_file():
            continue
        parts = set(path.relative_to(PROJECT_ROOT).parts)
        if parts & skip:
            continue
        result.append(
            {
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "name": path.name,
            }
        )
    return result


def render_table(path: Path, max_rows: int = 100) -> str:
    """把 CSV 渲染成 HTML 表格。"""
    if not path.exists():
        return '<p class="muted">还没有这个文件，请先运行对应脚本。</p>'

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        return '<p class="muted">表格是空的。</p>'

    header, body = rows[0], rows[1 : max_rows + 1]
    parts = ['<div class="table-wrap"><table class="data-table">', "<thead><tr>"]
    for name in header:
        parts.append(f"<th>{html.escape(name)}</th>")
    parts.append("</tr></thead><tbody>")

    for row in body:
        parts.append("<tr>")
        for index, cell in enumerate(row):
            column = header[index] if index < len(header) else ""
            classes = []
            if re.fullmatch(r"-?\d+(\.\d+)?", cell.strip()):
                classes.append("num")
            if column == "是否可信":
                classes.append("trust" if cell.strip() == "可信" else "untrust")
            class_attr = f' class="{" ".join(classes)}"' if classes else ""
            parts.append(f"<td{class_attr}>{html.escape(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")

    if len(rows) - 1 > len(body):
        parts.append(
            f'<p class="muted">只显示前 {len(body)} 行，共 {len(rows) - 1} 行。'
            f'完整文件：<code>{html.escape(str(path.relative_to(PROJECT_ROOT)))}</code></p>'
        )
    return "\n".join(parts)


def resolve_link(url: str, doc_by_file: dict[str, str], doc_by_name: dict[str, str], script_by_file: dict[str, str]) -> str:
    """把 Markdown 里的相对链接改写成网页内部路由。"""
    if url.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return url

    clean = unquote(url).replace("\\", "/").lstrip("./")
    name = clean.split("/")[-1]

    if clean == "README.md":
        return "#doc-overview"
    if clean in doc_by_file:
        return f"#doc-{doc_by_file[clean]}"
    if name in doc_by_name:
        return f"#doc-{doc_by_name[name]}"
    if clean in script_by_file:
        return f"#script-{script_by_file[clean]}"
    if clean.startswith("notes/"):
        return "#doc-note-feature"
    if clean.startswith("outputs/"):
        return f"../{clean}"
    if clean.startswith("data/"):
        return f"../{clean}"
    return url


def rewrite_links(raw_html: str, doc_by_file: dict[str, str], doc_by_name: dict[str, str], script_by_file: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        attr, url = match.group(1), match.group(2)
        return f'{attr}="{resolve_link(url, doc_by_file, doc_by_name, script_by_file)}"'

    return re.sub(r'(href|src)="([^"]+)"', repl, raw_html)


def build_docs(doc_by_file: dict[str, str], doc_by_name: dict[str, str], script_by_file: dict[str, str]) -> list[dict[str, str]]:
    result = []
    for item in DOCS:
        path = PROJECT_ROOT / item["file"]
        if not path.exists():
            text = f"# {item['title']}\n\n文件还没有生成：`{item['file']}`"
        else:
            text = read_text(path)

        rendered = markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        )
        rendered = rewrite_links(rendered, doc_by_file, doc_by_name, script_by_file)
        result.append(
            {
                **item,
                "html": rendered,
                "plain": strip_tags(rendered),
            }
        )
    return result


def build_scripts() -> list[dict[str, str]]:
    result = []
    for item in SCRIPTS:
        path = PROJECT_ROOT / item["file"]
        code = read_text(path) if path.exists() else f"# 文件不存在：{item['file']}"
        result.append({**item, "code": code})
    return result


# ---------------------------------------------------------------------------
# 4. 生成 HTML
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>时序特征工程 · 学习指引</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="app">
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <span class="brand-icon"><i data-lucide="activity"></i></span>
        <div>
          <strong>时序特征工程</strong>
          <span>北京 PM2.5 实战</span>
        </div>
      </div>

      <div class="search-box">
        <i data-lucide="search"></i>
        <input id="searchInput" type="search" placeholder="搜索教程、特征、脚本" autocomplete="off">
        <kbd>/</kbd>
      </div>

      <nav class="nav" id="nav"></nav>

      <div class="sidebar-foot">
        <button class="ghost-btn" id="copyPathBtn" type="button">
          <i data-lucide="folder"></i>
          <span>复制项目路径</span>
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="icon-btn menu-btn" id="menuBtn" type="button" aria-label="打开菜单">
          <i data-lucide="menu"></i>
        </button>
        <div class="crumb" id="crumb">项目总览</div>
        <div class="top-actions">
          <button class="primary-btn" id="runBtn" type="button">
            <i data-lucide="play"></i>
            <span>复制运行命令</span>
          </button>
        </div>
      </header>

      <main class="content" id="view"></main>
    </div>
  </div>

  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <div class="dialog-backdrop hidden" id="dialogBackdrop">
    <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialogTitle">
      <div class="dialog-head">
        <h2 id="dialogTitle">代码</h2>
        <button class="icon-btn" id="dialogClose" type="button" aria-label="关闭">
          <i data-lucide="x"></i>
        </button>
      </div>
      <div class="dialog-body" id="dialogBody"></div>
    </div>
  </div>

  <script id="guide-data" type="application/json">__GUIDE_DATA__</script>
  <script src="vendor/lucide.min.js"></script>
  <script src="app.js"></script>
</body>
</html>
"""


def main() -> None:
    doc_by_file = {item["file"]: item["id"] for item in DOCS}
    doc_by_name = {item["file"].split("/")[-1]: item["id"] for item in DOCS}
    script_by_file = {item["file"]: item["id"] for item in SCRIPTS}

    docs = build_docs(doc_by_file, doc_by_name, script_by_file)
    scripts = build_scripts()

    tables = {}
    for item in TABLES:
        path = PROJECT_ROOT / item["file"]
        tables[item["id"]] = {
            **item,
            "html": render_table(path, item.get("max_rows", 100)),
            "exists": path.exists(),
        }

    cleaning_report_path = PROJECT_ROOT / "outputs" / "tables" / "04_cleaning_report.txt"
    cleaning_report = (
        f'<pre class="report-pre">{html.escape(read_text(cleaning_report_path))}</pre>'
        if cleaning_report_path.exists()
        else '<p class="muted">还没有清洗报告，请先运行 04_load_clean.py。</p>'
    )

    copied_figures = []
    for item in FIGURES:
        path = PROJECT_ROOT / item["file"]
        copied_figures.append(
            {
                **item,
                "href": f"../{item['file']}",
                "exists": path.exists(),
            }
        )

    search_index = []
    for item in docs:
        search_index.append(
            {
                "title": item["title"],
                "type": item["group"],
                "route": f"#doc-{item['id']}",
                "text": item["plain"][:4000],
            }
        )
    for item in scripts:
        search_index.append(
            {
                "title": item["title"],
                "type": "脚本",
                "route": f"#script-{item['id']}",
                "text": f"{item['summary']} {item['cmd']} {item['code'][:2500]}",
            }
        )
    for item in copied_figures:
        search_index.append(
            {
                "title": item["title"],
                "type": "图",
                "route": "#figures",
                "text": item["caption"],
            }
        )

    search_index.append(
        {
            "title": "项目文件（读取文件夹）",
            "type": "工具",
            "route": "#files",
            "text": "浏览项目文件夹里的文件，教程、代码、笔记、表格、图片都能直接打开；可重新读取刷新。",
        }
    )
    for file_item in iter_project_files():
        search_index.append(
            {
                "title": file_item["path"],
                "type": "文件",
                "route": "#file-" + quote(file_item["path"], safe=""),
                "text": file_item["path"] + " " + file_item["name"],
            }
        )

    data = {
        "projectRoot": str(PROJECT_ROOT),
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "docs": docs,
        "scripts": scripts,
        "tables": tables,
        "figures": copied_figures,
        "cleaningReport": cleaning_report,
        "concepts": CONCEPTS,
        "roadmap": ROADMAP,
        "requirements": [
            {"requirement": row[0], "task": row[1], "route": row[2]} for row in REQUIREMENTS
        ],
        "search": search_index,
    }

    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    rendered = HTML_TEMPLATE.replace("__GUIDE_DATA__", payload)

    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(rendered, encoding="utf-8")
    print(f"已生成：{OUTPUT_HTML}")
    print(f"教程 {len(docs)} 篇，脚本 {len(scripts)} 个，表格 {len(tables)} 张，图片 {len(copied_figures)} 张。")
    print("打开方式一：双击 guide/index.html")
    print("打开方式二：powershell -File guide/start-server.ps1，然后访问 http://127.0.0.1:8765/guide/index.html")


if __name__ == "__main__":
    main()
