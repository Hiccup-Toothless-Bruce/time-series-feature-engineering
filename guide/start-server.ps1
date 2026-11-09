# 启动“学习指引”本地网页服务器（Windows PowerShell）
#
# 用法：在项目根目录打开 PowerShell，输入
#   powershell -ExecutionPolicy Bypass -File .\guide\start-server.ps1
#
# 然后在浏览器里打开：
#   http://127.0.0.1:8765/guide/index.html
#
# 为什么需要服务器：
# 1. 网页里的图片和表格在 outputs 文件夹，直接用 file:// 打开时部分浏览器会拦截；
# 2. 网页里的“项目文件”要读取文件夹，浏览器只允许本地服务这么做。

param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Url = "http://127.0.0.1:$Port/guide/index.html"

Write-Host "项目目录：$ProjectRoot" -ForegroundColor DarkGray
Write-Host "空闲端口：$Port" -ForegroundColor DarkGray

$busy = $null
if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $busy = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
}
if ($busy) {
    Write-Host "端口 $Port 已被占用，换一个端口试试：" -ForegroundColor Yellow
    Write-Host "  powershell -File .\guide\start-server.ps1 -Port 8899" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n学习指引地址：$Url" -ForegroundColor Green
Write-Host "按 Ctrl + C 停止服务器。`n" -ForegroundColor DarkGray

Start-Process $Url
& $Python (Join-Path $PSScriptRoot "server.py") --port $Port --bind 127.0.0.1
