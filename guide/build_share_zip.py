"""生成“解压后双击就能看”的离线分享压缩包。

用法（在项目根目录）：

    python guide\\build_share_zip.py
    python guide\\build_share_zip.py --no-rebuild
    python guide\\build_share_zip.py --no-zip

输出：

    dist\\时序特征工程学习指引-离线版\\index.html
    dist\\时序特征工程学习指引-离线版.zip

压缩包里包含：
- 网页本体（教程、脚本、表格数据已内嵌在 HTML 里）；
- 图片、知识点速查 PDF、源码、笔记模板；
- 一个内置的文件清单，所以“项目文件”页在离线状态下也能浏览。

限制：
- 不包含 data/ 里的原始数据和处理后数据，压缩包更小，适合分享阅读；
- “选择其他文件夹”功能仍然依赖浏览器权限，Chrome / Edge 支持。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUIDE_DIR = PROJECT_ROOT / "guide"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DIST_DIR = PROJECT_ROOT / "dist"

PACKAGE_NAME = "时序特征工程学习指引-离线版"
PACKAGE_DIR = DIST_DIR / PACKAGE_NAME
ZIP_PATH = DIST_DIR / f"{PACKAGE_NAME}.zip"

GUIDE_INDEX = GUIDE_DIR / "index.html"
DATA_RE = re.compile(
    r'(<script id="guide-data" type="application/json">)(.*?)(</script>)',
    re.S,
)

INCLUDE_ROOTS = ("docs", "notes", "scripts", "guide", "outputs")
INCLUDE_ROOT_FILES = ("README.md", "requirements.txt", "run_all.ps1")
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist"}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"}
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".js",
    ".css",
    ".html",
    ".ps1",
    ".yml",
    ".yaml",
    ".toml",
    ".sql",
    ".gitignore",
}
EMBED_TEXT_LIMIT = 200 * 1024


def read_text(path: Path) -> str:
    """读文本，优先 UTF-8，失败再试 GBK。"""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def run_builder(script: Path) -> None:
    print(f"正在重新生成：{script.relative_to(PROJECT_ROOT)}")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(script)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"生成失败：{script}")


def iter_source_files() -> list[Path]:
    """列出要放进压缩包的文件，跳过虚拟环境和缓存。"""
    files: list[Path] = []

    for name in INCLUDE_ROOT_FILES:
        path = PROJECT_ROOT / name
        if path.is_file():
            files.append(path)

    for root_name in INCLUDE_ROOTS:
        root = PROJECT_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(PROJECT_ROOT)
            if set(relative.parts) & SKIP_PARTS:
                continue
            # 离线包的根目录已经有一份 index.html，不再重复收录原始页面。
            if relative.as_posix() == "guide/index.html":
                continue
            files.append(path)

    unique = {path.relative_to(PROJECT_ROOT).as_posix(): path for path in files}
    return [unique[key] for key in sorted(unique)]


def url_path(path: str) -> str:
    """把文件路径转成浏览器可以打开的相对 URL。"""
    return "/".join(quote(part) for part in path.split("/"))


def kind_of(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix == ".csv":
        return "csv"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    return "binary"


def build_file_records(paths: list[Path]) -> dict[str, dict]:
    """给每个文件建立离线清单，顺便把不太大的文本内嵌进页面。"""
    records: dict[str, dict] = {}

    for path in paths:
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        stat = path.stat()
        suffix = path.suffix.lower()
        record = {
            "path": relative,
            "name": path.name,
            "size": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "ext": suffix,
            "kind": kind_of(path),
            "href": url_path(relative),
        }
        if suffix in TEXT_EXTENSIONS and stat.st_size <= EMBED_TEXT_LIMIT:
            try:
                record["text"] = read_text(path)
            except OSError:
                pass
        records[relative] = record

    return records


def file_node(record: dict) -> dict:
    return {
        "type": "file",
        "name": record["name"],
        "path": record["path"],
        "size": record["size"],
        "mtime": record["mtime"],
        "ext": record["ext"],
        "kind": record["kind"],
    }


def build_tree(records: dict[str, dict]) -> list[dict]:
    """把扁平文件清单变成侧边栏使用的树结构。"""
    root: dict = {"dirs": {}, "files": []}

    for record in records.values():
        parts = record["path"].split("/")
        node = root
        for part in parts[:-1]:
            node = node["dirs"].setdefault(part, {"dirs": {}, "files": []})
        node["files"].append(record)

    def convert(node: dict, prefix: str = "") -> list[dict]:
        result: list[dict] = []

        for name in sorted(node["dirs"]):
            child = node["dirs"][name]
            path = f"{prefix}/{name}" if prefix else name
            result.append(
                {
                    "type": "dir",
                    "name": name,
                    "path": path,
                    "children": convert(child, path),
                }
            )

        for record in sorted(node["files"], key=lambda item: item["name"].lower()):
            result.append(file_node(record))

        return result

    return convert(root)


def load_guide_data(index_html: str) -> tuple[dict, re.Match[str]]:
    match = DATA_RE.search(index_html)
    if not match:
        raise SystemExit("没有在 guide/index.html 里找到 guide-data 数据块。")
    try:
        data = json.loads(match.group(2))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"guide-data 不是合法 JSON：{exc}") from exc
    return data, match


def packaged_route(route: str, records: dict[str, dict]) -> bool:
    """搜索索引里指向未打包文件的条目要删掉，避免点开变成死链。"""
    if not route.startswith("#file-"):
        return True
    path = unquote(route[len("#file-") :])
    return path in records


def make_offline_html(index_html: str, data: dict, records: dict[str, dict]) -> str:
    data["projectRoot"] = "离线分享版（解压后双击 index.html）"
    data["offline"] = {
        "rootName": PACKAGE_NAME,
        "rootPath": "离线压缩包（打包时快照）",
        "fileCount": len(records),
        "files": records,
        "tree": build_tree(records),
        "builtAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # 图片和 PDF 在压缩包根目录，路径从 ../outputs/ 改成 outputs/。
    for figure in data.get("figures", []):
        record = records.get(figure.get("file", ""))
        if record:
            figure["href"] = record["href"]
            figure["exists"] = True

    data["search"] = [
        entry for entry in data.get("search", [])
        if packaged_route(entry.get("route", ""), records)
    ]

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("../outputs/", "outputs/")
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    rendered = DATA_RE.sub(
        lambda match: match.group(1) + payload + match.group(3),
        index_html,
        count=1,
    )
    rendered = rendered.replace(
        "<title>时序特征工程 · 学习指引</title>",
        "<title>时序特征工程 · 学习指引（离线版）</title>",
        1,
    )
    rendered = rendered.replace('href="style.css"', 'href="guide/style.css"', 1)
    rendered = rendered.replace('src="vendor/lucide.min.js"', 'src="guide/vendor/lucide.min.js"', 1)
    rendered = rendered.replace('src="app.js"', 'src="guide/app.js"', 1)
    return rendered


def reset_package_dir() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    resolved = PACKAGE_DIR.resolve()
    if resolved.parent != DIST_DIR.resolve() or resolved.name != PACKAGE_NAME:
        raise SystemExit("拒绝清理意外的目录。")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def copy_package_files(records: dict[str, dict]) -> None:
    for relative in records:
        source = PROJECT_ROOT / relative
        target = PACKAGE_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_readme() -> None:
    text = f"""时序特征工程 · 学习指引（离线分享版）

怎么打开
1. 先把压缩包完整解压到任意文件夹。
2. 双击里面的 index.html，用 Chrome 或 Edge 打开。
3. 左边的目录、搜索、代码复制、图表、表格、速查 PDF 都可以离线使用。

说明
- 教程、脚本、表格数据和文件清单已经打包进网页；
- 图片和 PDF 放在 outputs/ 文件夹，不要单独把 index.html 拖出来；
- “项目文件”页展示的是打包时的文件快照；
- 如果要读取自己电脑上的其他文件夹，可以点“选择其他文件夹”（Chrome / Edge 支持）。

打包时间：{datetime.now():%Y-%m-%d %H:%M}
"""
    write_text(PACKAGE_DIR / "打开前先看我.txt", text)


def create_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(DIST_DIR).as_posix()
                archive.write(path, arcname)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成可以分享的离线学习指引压缩包")
    parser.add_argument("--no-rebuild", action="store_true", help="不重新生成教程和 PDF，直接打包")
    parser.add_argument("--no-zip", action="store_true", help="只生成文件夹，不生成 zip")
    args = parser.parse_args()

    if not args.no_rebuild:
        run_builder(GUIDE_DIR / "build_guide.py")
        run_builder(GUIDE_DIR / "build_handbook.py")

    if not GUIDE_INDEX.exists():
        raise SystemExit("找不到 guide/index.html，请先运行 python guide\\build_guide.py")

    index_html = GUIDE_INDEX.read_text(encoding="utf-8-sig")
    data, _ = load_guide_data(index_html)

    paths = iter_source_files()
    records = build_file_records(paths)

    reset_package_dir()
    copy_package_files(records)

    # 根目录首页：资源路径改成 guide/...，数据路径改成 outputs/...
    share_html = make_offline_html(index_html, data, records)
    (PACKAGE_DIR / "index.html").write_text(share_html, encoding="utf-8")
    write_readme()

    folder_size = sum(path.stat().st_size for path in PACKAGE_DIR.rglob("*") if path.is_file())

    print()
    print(f"离线文件夹：{PACKAGE_DIR}")
    print(f"文件数量：{len(records) + 1} 个，文件夹大小约 {folder_size / 1024 / 1024:.1f} MB")

    if args.no_zip:
        print("按 --no-zip 要求，没有生成压缩包。")
        return

    create_zip()
    zip_size = ZIP_PATH.stat().st_size / 1024 / 1024

    with zipfile.ZipFile(ZIP_PATH) as archive:
        broken = archive.testzip()
        if broken:
            raise SystemExit(f"压缩包校验失败：{broken}")

    print(f"分享压缩包：{ZIP_PATH}（{zip_size:.1f} MB）")
    print("发给别人后，对方解压并双击 index.html 就能看。")


if __name__ == "__main__":
    main()
