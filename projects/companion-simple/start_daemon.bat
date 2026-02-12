@echo off
chcp 65001 >nul
REM 技能商店自动更新 - 启动脚本

echo ========================================
echo 技能商店自动更新工具
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo [检查] 正在检查依赖包...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [启动] 正在启动定时更新服务...
echo.
python main.py --daemon

pause
