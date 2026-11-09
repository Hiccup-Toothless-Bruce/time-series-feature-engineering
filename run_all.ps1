# 一键运行全部课程脚本（Windows PowerShell）
# 用法：在项目根目录打开 PowerShell，输入  .\run_all.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "找不到虚拟环境 .venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "请先按 README.md 的“第 0 步”创建并安装依赖。" -ForegroundColor Yellow
    exit 1
}

$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$scripts = @(
    "download_data.py",
    "01_python_basics.py",
    "02_pandas_basics.py",
    "03_sqlite_basics.py",
    "04_load_clean.py",
    "05_time_features.py",
    "06_baseline_model.py",
    "07_cyclic_encoding.py",
    "08_lag_rolling_features.py",
    "09_model_comparison.py",
    "10_plots.py"
)

foreach ($name in $scripts) {
    Write-Host "`n========== 正在运行 $name ==========" -ForegroundColor Cyan
    & $Python (Join-Path $ProjectRoot "scripts\$name")
}

Write-Host "`n========== 正在生成网页学习指引 ==========" -ForegroundColor Cyan
& $Python (Join-Path $ProjectRoot "guide\build_guide.py")

Write-Host "`n========== 正在生成可打印的 PDF 手册 ==========" -ForegroundColor Cyan
& $Python (Join-Path $ProjectRoot "guide\build_handbook.py")

Write-Host "`n全部脚本运行完成！请看 outputs 文件夹里的图片和表格。" -ForegroundColor Green
Write-Host "网页指引已生成：guide\index.html" -ForegroundColor Green
Write-Host "推荐打开方式：powershell -File .\guide\start-server.ps1" -ForegroundColor Green
