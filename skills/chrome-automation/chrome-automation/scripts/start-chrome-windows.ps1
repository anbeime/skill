# Chrome startup script with persistent profile support for Windows
# This script starts Chrome with a dedicated automation profile that preserves login states

$ErrorActionPreference = "Stop"

# Define paths
$CHROME_AUTOMATION_DIR = "$HOME\AppData\Local\Google\Chrome-Automation"
$CHROME_DEFAULT_DIR = "$HOME\AppData\Local\Google\Chrome\User Data"
$CHROME_APP = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$DEBUG_PORT = 9222

Write-Host "🔍 Checking Chrome automation profile..." -ForegroundColor Cyan

# Check if Chrome is already running with debug port
$chromeProcess = Get-Process -Name "chrome" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*remote-debugging-port=$DEBUG_PORT*" }

if ($chromeProcess) {
    Write-Host "✓ Chrome is already running with debug port $DEBUG_PORT" -ForegroundColor Green
    exit 0
}

# Check if dedicated automation directory exists
if (-not (Test-Path $CHROME_AUTOMATION_DIR)) {
    Write-Host "📦 First time setup: Creating dedicated Chrome automation profile..." -ForegroundColor Cyan

    # Create the automation directory
    New-Item -ItemType Directory -Path $CHROME_AUTOMATION_DIR -Force | Out-Null

    # Check if default Chrome profile exists
    if (Test-Path "$CHROME_DEFAULT_DIR\Default") {
        Write-Host "📋 Importing configuration from your existing Chrome profile..." -ForegroundColor Cyan
        Write-Host "   (This includes your login states, cookies, and settings)" -ForegroundColor Gray

        # Directories to exclude (large cache files)
        $excludeDirs = @(
            'Cache',
            'Code Cache',
            'GPUCache',
            'Service Worker',
            'ShaderCache',
            'GrShaderCache',
            'component_crx_cache',
            'BrowserMetrics',
            'CertificateRevocation',
            'Crashpad',
            'FileTypePolicies',
            'OptimizationGuidePredictionModels',
            'SafetyTips',
            'SSLErrorAssistant',
            'Subresource Filter',
            'ZxcvbnData'
        )

        # Copy Default profile
        $source = "$CHROME_DEFAULT_DIR\Default"
        $destination = "$CHROME_AUTOMATION_DIR\Default"

        # Create destination directory
        New-Item -ItemType Directory -Path $destination -Force | Out-Null

        # Get all items in source, excluding specified directories
        Get-ChildItem -Path $source -Force | ForEach-Object {
            $itemName = $_.Name
            if ($excludeDirs -notcontains $itemName) {
                $destPath = Join-Path $destination $itemName
                if ($_.PSIsContainer) {
                    Copy-Item -Path $_.FullName -Destination $destPath -Recurse -Force
                } else {
                    Copy-Item -Path $_.FullName -Destination $destPath -Force
                }
                Write-Host "  Copied: $itemName" -ForegroundColor Gray
            }
        }

        # Also copy Local State file for profile settings
        $localState = "$CHROME_DEFAULT_DIR\Local State"
        if (Test-Path $localState) {
            Copy-Item -Path $localState -Destination "$CHROME_AUTOMATION_DIR\Local State" -Force
            Write-Host "  Copied: Local State" -ForegroundColor Gray
        }

        Write-Host "✓ Configuration imported successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No existing Chrome profile found. Starting with fresh profile." -ForegroundColor Yellow
        Write-Host "   You'll need to log in manually on first use." -ForegroundColor Gray
    }
} else {
    Write-Host "✓ Chrome automation profile found" -ForegroundColor Green
    Write-Host "   Location: $CHROME_AUTOMATION_DIR" -ForegroundColor Gray
}

# Start Chrome with the dedicated automation profile
Write-Host "🚀 Starting Chrome with automation profile..." -ForegroundColor Cyan

# Check if Chrome executable exists
if (-not (Test-Path $CHROME_APP)) {
    # Try alternate location
    $CHROME_APP = "$HOME\AppData\Local\Google\Chrome\Application\chrome.exe"
    if (-not (Test-Path $CHROME_APP)) {
        Write-Host "❌ Chrome not found. Please ensure Google Chrome is installed." -ForegroundColor Red
        exit 1
    }
}

Start-Process -FilePath $CHROME_APP -ArgumentList @(
    "--remote-debugging-port=$DEBUG_PORT",
    "--user-data-dir=`"$CHROME_AUTOMATION_DIR`""
)

# Wait for Chrome to start
Start-Sleep -Seconds 3

# Verify Chrome started successfully
$chromeRunning = Get-Process -Name "chrome" -ErrorAction SilentlyContinue

if ($chromeRunning) {
    Write-Host "✓ Chrome started successfully with debug port $DEBUG_PORT" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Profile location: $CHROME_AUTOMATION_DIR" -ForegroundColor Cyan
    Write-Host "🔗 Debug port: $DEBUG_PORT" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Your login states and cookies are preserved in this profile." -ForegroundColor Gray
    Write-Host "You only need to log in once - it will be remembered for future sessions." -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to start Chrome" -ForegroundColor Red
    exit 1
}
