# 任嘉伦AI伴侣 - GPT-SoVITS TTS 测试脚本
# 使用 PowerShell 调用 GPT-SoVITS API

$BASE_URL = "http://localhost:9874"
$OUTPUT_DIR = "D:\tool\skill\projects\xiaoyue-web\tts_audio"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  任嘉伦AI伴侣 - GPT-SoVITS 音色克隆测试" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查服务状态
Write-Host "1. 检查 GPT-SoVITS 服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   [OK] GPT-SoVITS 服务运行正常" -ForegroundColor Green
    }
} catch {
    Write-Host "   [ERROR] 无法连接到 GPT-SoVITS 服务" -ForegroundColor Red
    Write-Host "   请确保服务已启动: http://localhost:9874/" -ForegroundColor Red
    exit
}

Write-Host ""

# 测试文本
$TEST_TEXT = "你好，我是任嘉伦，很高兴认识你。"

# 测试第一个音频文件
$AUDIO_PATH = "$OUTPUT_DIR\02_红人面对面_采访.wav"
$OUTPUT_NAME = "test_output_01.wav"
$OUTPUT_PATH = "$OUTPUT_DIR\$OUTPUT_NAME"

Write-Host "2. 测试音频素材: 红人面对面采访" -ForegroundColor Yellow
Write-Host "   文件路径: $AUDIO_PATH" -ForegroundColor Gray

# 检查文件是否存在
if (-not (Test-Path $AUDIO_PATH)) {
    Write-Host "   [ERROR] 文件不存在" -ForegroundColor Red
    exit
}

Write-Host "   正在合成音频..." -ForegroundColor Cyan

try {
    # 使用 GET 方式调用 API
    $encodedText = [System.Web.HttpUtility]::UrlEncode($TEST_TEXT)
    $refPath = [System.Web.HttpUtility]::UrlEncode($AUDIO_PATH)
    $refText = [System.Web.HttpUtility]::UrlEncode("大家好，我是任嘉伦")
    
    $url = "$BASE_URL/?refer_wav_path=$refPath&prompt_text=$refText&prompt_language=zh&text=$encodedText&text_language=zh"
    
    Write-Host "   请求URL长度: $($url.Length)" -ForegroundColor DarkGray
    
    # 发送请求
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 120
    
    if ($response.StatusCode -eq 200) {
        # 保存音频
        [System.IO.File]::WriteAllBytes($OUTPUT_PATH, $response.Content)
        $fileSize = [math]::Round((Get-Item $OUTPUT_PATH).Length / 1KB, 2)
        Write-Host "   [SUCCESS] 合成成功!" -ForegroundColor Green
        Write-Host "   文件大小: $fileSize KB" -ForegroundColor Gray
        Write-Host "   保存位置: $OUTPUT_PATH" -ForegroundColor Gray
        
        # 播放音频
        Write-Host ""
        Write-Host "3. 正在播放生成的音频..." -ForegroundColor Yellow
        $player = New-Object System.Media.SoundPlayer $OUTPUT_PATH
        $player.PlaySync()
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  测试完成！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
    } else {
        Write-Host "   [ERROR] 失败: HTTP $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERROR] 错误: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   详细错误: $($_.Exception)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "提示: 如果测试成功，可以打开 GPT-SoVITS WebUI" -ForegroundColor Cyan
Write-Host "      进行更多参数调整和批量测试" -ForegroundColor Cyan
Write-Host "      地址: http://localhost:9874/" -ForegroundColor Gray
