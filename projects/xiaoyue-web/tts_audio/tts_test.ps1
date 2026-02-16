# 任嘉伦AI伴侣 - GPT-SoVITS TTS 测试脚本
# 使用 PowerShell 调用 GPT-SoVITS API

$BASE_URL = "http://localhost:9874"
$OUTPUT_DIR = "D:\tool\skill\projects\xiaoyue-web\tts_audio"

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan
Write-Host "任嘉伦AI伴侣 - GPT-SoVITS 音色克隆测试" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

# 检查服务状态
Write-Host "1. 检查 GPT-SoVITS 服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ GPT-SoVITS 服务运行正常" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ 无法连接到 GPT-SoVITS 服务" -ForegroundColor Red
    Write-Host "   请确保服务已启动: http://localhost:9874/" -ForegroundColor Red
    exit
}

Write-Host ""

# 测试音频文件列表
$AUDIO_FILES = @(
    @{ Name = "红人面对面采访"; Path = "$OUTPUT_DIR\02_红人面对面_采访.wav"; Priority = 1 },
    @{ Name = "娱匠采访"; Path = "$OUTPUT_DIR\03_娱匠_采访.wav"; Priority = 2 },
    @{ Name = "芭莎星榜样采访"; Path = "$OUTPUT_DIR\04_芭莎星榜样_采访.wav"; Priority = 3 },
    @{ Name = "红人面对面花絮"; Path = "$OUTPUT_DIR\05_红人面对面_花絮.wav"; Priority = 4 }
)

# 测试文本
$TEST_TEXT = "你好，我是任嘉伦，很高兴认识你。"

# 测试每个音频文件
$RESULTS = @()

foreach ($audio in $AUDIO_FILES | Sort-Object Priority) {
    Write-Host "2. 测试音频素材: $($audio.Name)" -ForegroundColor Yellow
    Write-Host "   文件路径: $($audio.Path)" -ForegroundColor Gray
    
    # 检查文件是否存在
    if (-not (Test-Path $audio.Path)) {
        Write-Host "   ❌ 文件不存在，跳过" -ForegroundColor Red
        continue
    }
    
    # 构建输出文件名
    $outputName = "test_$($audio.Name -replace ' ', '_')_output.wav"
    $outputPath = "$OUTPUT_DIR\$outputName"
    
    Write-Host "   正在合成: $outputName..." -ForegroundColor Cyan
    
    try {
        # 使用 GET 方式调用 API
        $encodedText = [System.Web.HttpUtility]::UrlEncode($TEST_TEXT)
        $refPath = [System.Web.HttpUtility]::UrlEncode($audio.Path)
        $refText = [System.Web.HttpUtility]::UrlEncode("大家好，我是任嘉伦")
        
        $url = "$BASE_URL/?refer_wav_path=$refPath&prompt_text=$refText&prompt_language=zh&text=$encodedText&text_language=zh"
        
        Write-Host "   请求URL: $url" -ForegroundColor DarkGray
        
        # 发送请求
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 120
        
        if ($response.StatusCode -eq 200) {
            # 保存音频
            [System.IO.File]::WriteAllBytes($outputPath, $response.Content)
            $fileSize = [math]::Round((Get-Item $outputPath).Length / 1KB, 2)
            Write-Host "   ✅ 成功! 文件大小: $fileSize KB" -ForegroundColor Green
            Write-Host "   📁 保存位置: $outputPath" -ForegroundColor Gray
            $RESULTS += @{ Name = $audio.Name; Success = $true; Output = $outputName }
        } else {
            Write-Host "   ❌ 失败: HTTP $($response.StatusCode)" -ForegroundColor Red
            $RESULTS += @{ Name = $audio.Name; Success = $false; Output = $null }
        }
    } catch {
        Write-Host "   ❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
        $RESULTS += @{ Name = $audio.Name; Success = $false; Output = $null }
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# 输出测试结果汇总
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan

foreach ($result in $RESULTS) {
    if ($result.Success) {
        Write-Host "✅ 成功" -ForegroundColor Green -NoNewline
        Write-Host " - $($result.Name)" -ForegroundColor White
        Write-Host "       输出文件: $($result.Output)" -ForegroundColor Gray
    } else {
        Write-Host "❌ 失败" -ForegroundColor Red -NoNewline
        Write-Host " - $($result.Name)" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "请试听生成的音频文件，选择效果最好的素材。" -ForegroundColor Cyan
Write-Host "输出目录: $OUTPUT_DIR" -ForegroundColor Gray

# 打开输出目录
# Start-Process "explorer.exe" "$OUTPUT_DIR"
