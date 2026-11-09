"""本地学习服务器：网页 + 读取项目文件夹。

用法（在项目根目录打开 PowerShell）：

    python guide\\server.py                  # 默认端口 8765
    python guide\\server.py --port 8899      # 端口被占用时换一个

它做了三件事：

1. 把整个项目目录当普通静态网站提供出去（所以 guide/index.html、图片、表格都能打开）；
2. 多提供两个接口，让网页能"读取文件夹"：
       GET /api/tree                 → 项目文件树（JSON）
       GET /api/file?path=docs/x.md  → 某个文本文件的内容（JSON）
3. 打开 http://127.0.0.1:8765/ 会自动跳到网页指引。

注意：接口只允许读取本项目文件夹里的内容，不能读电脑上的其他目录。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUIDE_URL = "/guide/index.html"

MAX_TEXT_BYTES = 512 * 1024   # 单个文本文件最多返回 512 KB
MAX_DEPTH = 5                 # 文件树最多展开 5 层
MAX_FILES = 2000              # 文件树最多列出 2000 个文件

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".idea", ".vscode", ".pytest_cache", ".ipynb_checkpoints",
    ".mypy_cache", ".ruff_cache",
}

TEXT_EXT = {
    ".py", ".md", ".txt", ".json", ".ps1", ".bat", ".sh", ".js", ".mjs",
    ".css", ".html", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".sql",
    ".tex", ".csv", ".gitignore", ".editorconfig",
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"}


def kind_of(path: Path) -> str:
    """给网页判断该用哪种预览方式。"""
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext == ".csv":
        return "csv"
    if ext in TEXT_EXT:
        return "text"
    return "binary"


def relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def safe_path(value: str) -> Path:
    """把网页传来的相对路径转成项目内的绝对路径，阻挡越界访问。"""
    candidate = (PROJECT_ROOT / unquote(value)).resolve()
    candidate.relative_to(PROJECT_ROOT)   # 越界会抛 ValueError
    return candidate


def read_text_file(path: Path) -> tuple[str, str]:
    """按 UTF-8 读，失败再试 GBK，避免中文乱码。"""
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace"), "utf-8(替换非法字符)"


def describe_file(path: Path) -> dict:
    stat = path.stat()
    return {
        "type": "file",
        "name": path.name,
        "path": relative(path),
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "ext": path.suffix.lower(),
        "kind": kind_of(path),
    }


def build_tree(directory: Path, depth: int = 0, counter: list[int] | None = None) -> list[dict]:
    """递归列出文件树；跳过虚拟环境、缓存等无关目录。"""
    if counter is None:
        counter = [0]

    entries: list[dict] = []
    try:
        children = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    except OSError:
        return entries

    for child in children:
        if child.name.startswith(".") or child.name in SKIP_DIRS:
            continue

        if child.is_dir():
            if depth >= MAX_DEPTH:
                continue
            entries.append(
                {
                    "type": "dir",
                    "name": child.name,
                    "path": relative(child),
                    "children": build_tree(child, depth + 1, counter),
                }
            )
        elif child.is_file():
            counter[0] += 1
            if counter[0] > MAX_FILES:
                continue
            entries.append(describe_file(child))

    return entries


class GuideHandler(SimpleHTTPRequestHandler):
    """静态文件 + 两个只读接口。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def end_headers(self):
        # 关掉缓存：改完文件刷新网页就能看到最新内容
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", GUIDE_URL)
            self.end_headers()
            return

        if parsed.path == "/api/tree":
            self.send_json(
                {
                    "root": str(PROJECT_ROOT),
                    "name": PROJECT_ROOT.name,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "entries": build_tree(PROJECT_ROOT),
                }
            )
            return

        if parsed.path == "/api/file":
            self.handle_file(parse_qs(parsed.query))
            return

        super().do_GET()

    def handle_file(self, query: dict) -> None:
        wanted = (query.get("path") or [""])[0]
        if not wanted:
            self.send_json({"error": "缺少 path 参数。"}, status=400)
            return

        try:
            target = safe_path(wanted)
        except ValueError:
            self.send_json({"error": "这个路径不在项目文件夹里。"}, status=400)
            return

        if not target.exists():
            self.send_json({"error": f"找不到文件：{wanted}"}, status=404)
            return
        if target.is_dir():
            self.send_json({"error": f"{wanted} 是一个文件夹，不是文件。"}, status=400)
            return

        size = target.stat().st_size
        if size > MAX_TEXT_BYTES:
            self.send_json(
                {
                    "error": f"文件太大了（{size / 1024:.0f} KB），网页只显示 512 KB 以内的文本。"
                             "可以点右上角“新标签打开”看原文件。",
                    "path": wanted,
                    "size": size,
                },
                status=413,
            )
            return

        try:
            text, encoding = read_text_file(target)
        except OSError as error:
            self.send_json({"error": f"读取失败：{error}"}, status=500)
            return

        self.send_json(
            {
                "path": relative(target),
                "size": size,
                "encoding": encoding,
                "ext": target.suffix.lower(),
                "text": text,
            }
        )

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        try:
            message = fmt % args
        except Exception:
            message = fmt
        if "/api/" in message:
            return
        sys.stdout.write(f"[{datetime.now():%H:%M:%S}] {message}\n")
        sys.stdout.flush()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="启动“时序特征工程”学习指引本地服务器")
    parser.add_argument("--port", type=int, default=8765, help="端口号，默认 8765")
    parser.add_argument("--bind", default="127.0.0.1", help="监听地址，默认只允许本机")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.bind, args.port), GuideHandler)
    print(f"项目目录：{PROJECT_ROOT}")
    print(f"网页地址：http://{args.bind}:{args.port}{GUIDE_URL}")
    print("按 Ctrl + C 停止服务器。")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
