@echo off
chcp 65001 >nul
title HR招聘管理系统

echo ============================================
echo   HR招聘管理系统 — 启动中...
echo ============================================
echo.

cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 检查Python版本...
python --version

echo.
echo [2/3] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

echo.
echo [3/3] 启动服务...
echo.
echo ============================================
echo   系统启动中，请稍候...
echo   启动后将自动打开浏览器
echo   按 Ctrl+C 可以停止服务
echo ============================================
echo.

:: 自动打开浏览器
start "" http://localhost:8080

:: 启动Flask应用
python app.py

pause
