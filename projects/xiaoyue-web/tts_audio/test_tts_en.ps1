# GPT-SoVITS TTS Test Script for Ren Jialun AI Companion
# This script tests voice cloning using GPT-SoVITS API

$BASE_URL = "http://localhost:9874"
$OUTPUT_DIR = "D:\tool\skill\projects\xiaoyue-web\tts_audio"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ren Jialun AI - GPT-SoVITS TTS Test  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check service status
Write-Host "Step 1: Checking GPT-SoVITS service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   [OK] Service is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   [ERROR] Cannot connect to service" -ForegroundColor Red
    Write-Host "   Please ensure GPT-SoVITS is running at: http://localhost:9874/" -ForegroundColor Red
    exit
}

Write-Host ""

# Test parameters
$TEST_TEXT = "Hello, I am Ren Jialun. Nice to meet you."
$AUDIO_FILE = "02_red_face_to_face_interview.wav"
$AUDIO_PATH = "$OUTPUT_DIR\02_红人面对面_采访.wav"
$OUTPUT_FILE = "test_output_01.wav"
$OUTPUT_PATH = "$OUTPUT_DIR\$OUTPUT_FILE"

Write-Host "Step 2: Testing audio file..." -ForegroundColor Yellow
Write-Host "   Audio: $AUDIO_PATH" -ForegroundColor Gray

# Check if file exists
if (-not (Test-Path $AUDIO_PATH)) {
    Write-Host "   [ERROR] Audio file not found" -ForegroundColor Red
    exit
}

Write-Host "   Generating speech..." -ForegroundColor Cyan

try {
    # Encode parameters
    $encodedText = [System.Web.HttpUtility]::UrlEncode($TEST_TEXT)
    $refPath = [System.Web.HttpUtility]::UrlEncode($AUDIO_PATH)
    $refText = [System.Web.HttpUtility]::UrlEncode("Hello everyone")
    
    # Build API URL
    $url = "$BASE_URL/?refer_wav_path=$refPath&prompt_text=$refText&prompt_language=zh&text=$encodedText&text_language=zh"
    
    Write-Host "   URL length: $($url.Length) chars" -ForegroundColor DarkGray
    
    # Call API
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 120
    
    if ($response.StatusCode -eq 200) {
        # Save audio file
        [System.IO.File]::WriteAllBytes($OUTPUT_PATH, $response.Content)
        $fileSize = [math]::Round((Get-Item $OUTPUT_PATH).Length / 1KB, 2)
        
        Write-Host "   [SUCCESS] Audio generated!" -ForegroundColor Green
        Write-Host "   File size: $fileSize KB" -ForegroundColor Gray
        Write-Host "   Saved to: $OUTPUT_PATH" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  Test completed successfully!          " -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Listen to the generated audio file" -ForegroundColor White
        Write-Host "2. Open GPT-SoVITS WebUI for fine-tuning" -ForegroundColor White
        Write-Host "3. Test with different audio samples" -ForegroundColor White
        Write-Host ""
        Write-Host "WebUI: http://localhost:9874/" -ForegroundColor Gray
    } else {
        Write-Host "   [ERROR] Failed: HTTP $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}
