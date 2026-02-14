# Auto-install script for agent-browser on Windows
# This script checks and installs all required dependencies automatically

Write-Host "🔍 Checking agent-browser installation..." -ForegroundColor Cyan

# Define paths
$AB_HOME = "$HOME\Documents\agent-browser"
$AB_BIN = "$AB_HOME\bin\agent-browser.cmd"

# Check if agent-browser binary exists
if (Test-Path $AB_BIN) {
    Write-Host "✓ agent-browser binary found" -ForegroundColor Green
    
    # Test if it works
    Set-Location $AB_HOME
    $env:AGENT_BROWSER_HOME = $AB_HOME
    try {
        & $AB_BIN --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ agent-browser is working correctly" -ForegroundColor Green
            exit 0
        }
    } catch {
        Write-Host "⚠️  agent-browser binary exists but not working, rebuilding..." -ForegroundColor Yellow
    }
}

# Check if repository exists
if (-not (Test-Path $AB_HOME)) {
    Write-Host "📦 Cloning agent-browser repository..." -ForegroundColor Cyan
    Set-Location "$HOME\Documents"
    git clone https://github.com/vercel-labs/agent-browser.git
    Set-Location agent-browser
} else {
    Write-Host "✓ Repository found" -ForegroundColor Green
    Set-Location $AB_HOME
}

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Node.js found: $(node --version)" -ForegroundColor Green

# Check pnpm
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing pnpm..." -ForegroundColor Cyan
    npm install -g pnpm
}
Write-Host "✓ pnpm found: $(pnpm --version)" -ForegroundColor Green

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
pnpm install

# Install Playwright Chromium
Write-Host "📦 Installing Playwright Chromium..." -ForegroundColor Cyan
npx playwright install chromium

# Check Rust/Cargo
$cargoPath = "$HOME\.cargo\bin\cargo.exe"
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    if (Test-Path $cargoPath) {
        Write-Host "✓ Cargo found in ~/.cargo/bin, adding to PATH" -ForegroundColor Green
        $env:PATH = "$HOME\.cargo\bin;$env:PATH"
    } else {
        Write-Host "❌ Rust/Cargo not found. Installing rustup..." -ForegroundColor Yellow
        Write-Host "Downloading rustup installer..." -ForegroundColor Cyan
        
        # Download and run rustup installer
        $rustupInit = "$env:TEMP\rustup-init.exe"
        Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $rustupInit
        
        Write-Host "Running rustup installer (this may take a few minutes)..." -ForegroundColor Cyan
        & $rustupInit -y --default-toolchain stable --profile minimal
        
        Remove-Item $rustupInit
        $env:PATH = "$HOME\.cargo\bin;$env:PATH"
    }
}

# Ensure cargo is in PATH
$env:PATH = "$HOME\.cargo\bin;$env:PATH"

# Check if default toolchain is set
try {
    $rustupOutput = rustup default 2>&1
    if ($rustupOutput -notmatch "stable") {
        Write-Host "📦 Setting up Rust stable toolchain..." -ForegroundColor Cyan
        rustup default stable
    }
} catch {
    Write-Host "📦 Setting up Rust stable toolchain..." -ForegroundColor Cyan
    rustup default stable
}

$rustVersion = rustc --version
Write-Host "✓ Rust found: $rustVersion" -ForegroundColor Green

# Build agent-browser
Write-Host "🔨 Building agent-browser..." -ForegroundColor Cyan
npm run build:native

# Verify installation
if (Test-Path $AB_BIN) {
    Write-Host "✅ agent-browser installed successfully!" -ForegroundColor Green
    Write-Host "Binary location: $AB_BIN" -ForegroundColor Cyan
} else {
    Write-Host "❌ Installation failed - binary not found" -ForegroundColor Red
    exit 1
}
