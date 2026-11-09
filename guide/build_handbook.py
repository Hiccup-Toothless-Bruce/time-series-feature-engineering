"""把 docs/08-知识点与代码速查.md 变成可打印的 PDF。

流程只有三步：

1. 用 markdown 库把 Markdown 渲染成 HTML；
2. 套上专门的"打印样式"（A4 纸张、紧凑排版、代码块自动换行）；
3. 调用本机已有的浏览器（Chrome 或 Edge）做"打印成 PDF"。

运行（在项目根目录）：

    python guide\\build_handbook.py                    # 紧凑版：HTML + PDF
    python guide\\build_handbook.py --no-pdf           # 只生成 HTML
    python guide\\build_handbook.py --page-break-chapters  # 每一章从新页开始

输出：

    outputs\\知识点与代码速查.html
    outputs\\知识点与代码速查.pdf

说明：默认不强制每章分页，纸张利用率更高。如果确实需要把每一章
分开打印或装订，再加 --page-break-chapters。

不需要额外安装任何软件。只要电脑上有 Chrome 或 Edge（Windows
一般都有）就能出 PDF。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import markdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = PROJECT_ROOT / "docs" / "08-知识点与代码速查.md"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
HTML_PATH = OUTPUT_DIR / "知识点与代码速查.html"
PDF_PATH = OUTPUT_DIR / "知识点与代码速查.pdf"

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

# 紧凑打印样式：默认不强制章节换页，靠留白和标题色块区分层级。
# 这样可以把正文塞进前一页的剩余空间，避免每章末尾出现半页空白。
PRINT_CSS_TEMPLATE = """
@page {
  size: A4;
  margin: 12mm 11mm 12mm;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
  font-size: 9.9pt;
  line-height: 1.5;
  color: #1b2733;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* 章节标题：紧凑色块，醒目但不占地方 */
h1 {
  font-size: 14.5pt;
  line-height: 1.3;
  margin: 14pt 0 6pt;
  padding: 4pt 8pt;
  background: #e9f2f0;
  border-left: 4pt solid #0f7b6c;
  color: #0a5f53;
  break-inside: avoid;
  page-break-inside: avoid;
  break-after: avoid;
  page-break-after: avoid;
}

/* 封面标题保持大标题样式 */
h1:first-of-type {
  font-size: 20pt;
  line-height: 1.25;
  margin: 0 0 10pt;
  padding: 0 0 6pt;
  background: transparent;
  border-left: 0;
  border-bottom: 2px solid #0f7b6c;
  break-before: avoid;
  page-break-before: avoid;
}

/*__CHAPTER_BREAK__*/

h2 {
  font-size: 11.3pt;
  line-height: 1.35;
  margin: 10pt 0 4pt;
  padding-bottom: 1.5pt;
  border-bottom: 1px solid #dfe8e6;
  color: #14435c;
  break-after: avoid;
  page-break-after: avoid;
}

h3 {
  font-size: 10.2pt;
  line-height: 1.35;
  margin: 8pt 0 3pt;
  color: #37505f;
  break-after: avoid;
  page-break-after: avoid;
}

p {
  margin: 3pt 0;
  orphans: 2;
  widows: 2;
}

/* 说明文字后面紧跟着列表或代码时，不要把它单独留在页底 */
p:has(+ ul), p:has(+ ol), p:has(+ pre) {
  break-after: avoid;
  page-break-after: avoid;
}

h1 + *, h2 + *, h3 + * {
  break-before: avoid;
  page-break-before: avoid;
}

/* 代码块：浅底 + 左侧色条，长行自动换行，避免被裁掉 */
pre {
  background: #f5f7fa;
  border: 1px solid #d9e0e7;
  border-left: 3px solid #0f7b6c;
  border-radius: 2px;
  padding: 4.5pt 6pt;
  margin: 4.5pt 0;
  font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
  font-size: 8.05pt;
  line-height: 1.42;
  white-space: pre-wrap;
  word-break: break-word;
  tab-size: 2;
  break-inside: avoid;
  page-break-inside: avoid;
}

/* 代码块尽量和紧随其后的说明留在同一页 */
pre + p { break-before: avoid; page-break-before: avoid; }

pre code {
  background: transparent;
  border: 0;
  padding: 0;
  font-size: inherit;
  color: #16324a;
}

code {
  font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
  font-size: 8.8pt;
  background: #eef1f4;
  border: 1px solid #e2e6eb;
  border-radius: 2px;
  padding: 0 1.5pt;
  color: #24435c;
  word-break: break-word;
}

/* 表格：表头跨页重复，行不被拆开 */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 5pt 0;
  font-size: 8.35pt;
  line-height: 1.38;
}

thead { display: table-header-group; }
tr { page-break-inside: avoid; break-inside: avoid; }

th, td {
  border: 1px solid #ccd4dc;
  padding: 2pt 3.5pt;
  text-align: left;
  vertical-align: top;
}

th { background: #eef4f3; color: #0a5f53; font-weight: 700; }

blockquote {
  margin: 6pt 0;
  padding: 5pt 8pt;
  background: #f0f7f5;
  border-left: 3px solid #0f7b6c;
  border-radius: 0 2px 2px 0;
  color: #2d3b45;
  font-size: 9.5pt;
}

blockquote p { margin: 2pt 0; }

ul, ol {
  margin: 2.5pt 0;
  padding-left: 17pt;
}

li { margin: 1pt 0; }
li > ul, li > ol { margin-top: 1pt; margin-bottom: 1pt; }

hr {
  border: 0;
  border-top: 1px dashed #d8e0e6;
  margin: 7pt 0;
}

a { color: #14435c; text-decoration: none; }

/* 封面上的目录 */
.toc {
  margin: 8pt 0 3pt;
  padding: 6pt 8pt;
  border: 1px solid #d9e0e7;
  border-radius: 3px;
  background: #fbfcfd;
  break-inside: avoid;
  page-break-inside: avoid;
}

.toc-title { font-weight: 700; color: #0a5f53; margin-bottom: 3pt; font-size: 9.4pt; }
.toc ul { margin: 0; padding-left: 0; list-style: none; column-count: 2; column-gap: 18pt; }
.toc li { margin: 1pt 0; font-size: 9pt; }
.toc a { color: #24435c; }

.meta-line {
  font-size: 8.6pt;
  color: #6b7885;
  margin: 2pt 0 0;
}

@media print {
  a { color: #24435c; }
  .no-print { display: none; }
}
"""

CHAPTER_BREAK_CSS = """
/* 可选：每一章从新的一页开始（适合分章打印或装订） */
h1 {
  break-before: page;
  page-break-before: always;
}
h1:first-of-type {
  break-before: avoid;
  page-break-before: avoid;
}
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="replace")


def find_browser() -> str | None:
    """找一个能打印 PDF 的浏览器。"""
    for candidate in BROWSER_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return str(path)

    for name in ("chrome", "google-chrome", "chromium", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    return None


def build_css(page_break_chapters: bool) -> str:
    chapter_rule = CHAPTER_BREAK_CSS if page_break_chapters else ""
    return PRINT_CSS_TEMPLATE.replace("/*__CHAPTER_BREAK__*/", chapter_rule)


def render_html(markdown_text: str, page_break_chapters: bool = False) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "toc", "md_in_html"],
        extension_configs={"toc": {"toc_depth": "1-1", "permalink": False}},
    )
    body = md.convert(markdown_text)

    toc_html = ""
    if getattr(md, "toc", ""):
        mode_text = "每章从新的一页开始" if page_break_chapters else "连续排版，节省纸张"
        toc_html = (
            f'<nav class="toc"><div class="toc-title">目录（{mode_text}）</div>'
            + md.toc
            + "</nav>"
        )
        # 把目录插在封面说明（第一个引用块）之后
        marker = "</blockquote>"
        position = body.find(marker)
        if position >= 0:
            position += len(marker)
            body = body[:position] + toc_html + body[position:]
        else:
            body = toc_html + body

    layout_note = (
        "打印建议：A4、缩放 100%（每章另起一页）"
        if page_break_chapters
        else "打印建议：A4、缩放 100%（连续紧凑排版，已尽量减少空白）"
    )
    meta = (
        '<p class="meta-line">项目：time-series-feature-engineering'
        f"　|　生成时间：{datetime.now():%Y-%m-%d %H:%M}"
        f"　|　{layout_note}</p>"
    )
    body = body.replace("</h1>", "</h1>" + meta, 1)

    return HTML_TEMPLATE.format(
        title="时序特征工程 · 知识点与代码速查手册",
        css=build_css(page_break_chapters),
        body=body,
    )


def print_pdf(browser: str, html_path: Path, pdf_path: Path) -> bool:
    """调用浏览器把 HTML 打成 PDF。"""
    if pdf_path.exists():
        pdf_path.unlink()

    with tempfile.TemporaryDirectory(prefix="handbook-print-") as user_data_dir:
        html_url = "file:///" + quote(html_path.as_posix(), safe="/:")
        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--user-data-dir={user_data_dir}",
            f"--print-to-pdf={pdf_path}",
            html_url,
        ]
        try:
            subprocess.run(command, capture_output=True, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return False

    return pdf_path.exists() and pdf_path.stat().st_size > 20_000


def report_pdf(pdf_path: Path) -> None:
    """如果装了 pypdf，就顺便报一下页数，方便确认没有打空。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    try:
        reader = PdfReader(str(pdf_path))
        print(f"PDF 页数：{len(reader.pages)} 页")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="生成《知识点与代码速查手册》的 HTML 和 PDF")
    parser.add_argument("--no-pdf", action="store_true", help="只生成 HTML，不生成 PDF")
    parser.add_argument(
        "--page-break-chapters",
        action="store_true",
        help="每一章从新的一页开始（默认关闭，连续排版更省纸）",
    )
    args = parser.parse_args()

    if not SOURCE_MD.exists():
        print(f"找不到源文件：{SOURCE_MD}")
        raise SystemExit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markdown_text = read_text(SOURCE_MD)
    html = render_html(markdown_text, page_break_chapters=args.page_break_chapters)
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"已生成 HTML：{HTML_PATH}")

    if args.no_pdf:
        print("（按 --no-pdf 要求，跳过 PDF）")
        return

    browser = find_browser()
    if not browser:
        print("没有找到 Chrome 或 Edge，无法自动生成 PDF。")
        print(f"可以打开 {HTML_PATH}，按 Ctrl + P 手动打印成 PDF。")
        return

    print(f"正在用浏览器打印 PDF：{browser}")
    if print_pdf(browser, HTML_PATH, PDF_PATH):
        size_kb = PDF_PATH.stat().st_size / 1024
        print(f"已生成 PDF：{PDF_PATH}（{size_kb:.0f} KB）")
        report_pdf(PDF_PATH)
    else:
        print("PDF 生成失败。可以打开 HTML 后按 Ctrl + P，选择“另存为 PDF”。")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
