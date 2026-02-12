@echo off
chcp 65001 >nul
REM 技能商店自动更新 - 单次执行脚本

echo ========================================
echo 技能商店自动更新 - 立即执行
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python
    pause
    exit /b 1
)

echo [执行] 正在执行更新任务...
echo.
python main.py --once -v

echo.
echo ========================================
echo 更新完成
echo ========================================
pause
