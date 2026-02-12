@echo off
echo ========================================
echo    小易伴侣 Web 版启动器
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 .env 文件
if not exist .env (
    echo [错误] 未找到 .env 文件
    echo.
    echo 请先配置 API Key:
    echo 1. copy .env.example .env
    echo 2. notepad .env
    echo 3. 填入你的智谱 AI API Key
    echo.
    pause
    exit /b 1
)

REM 检查 API Key
findstr /C:"your-api-key-here" .env >nul
if %errorlevel% equ 0 (
    echo [警告] 检测到默认 API Key，请先配置真实的 API Key
    echo.
    echo 打开 .env 文件并填入你的智谱 AI API Key
    echo 获取地址: https://open.bigmodel.cn/
    echo.
    pause
    notepad .env
    exit /b 1
)

echo [信息] 正在启动小易伴侣服务器...
echo.
echo 服务器地址: http://localhost:3000
echo 按 Ctrl+C 停止服务器
echo.

REM 使用 Node.js 启动
C:\Users\ASUS\.stepfun\runtimes\node\install_1770628825604_th45cs96cig\node-v22.18.0-win-x64\node.exe server.js

pause
