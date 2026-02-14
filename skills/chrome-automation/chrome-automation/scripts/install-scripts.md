# Installation Scripts

Quick installation scripts for agent-browser on Mac and Windows.

## Mac Installation Script

Save as `install-agent-browser.sh`:

```bash
#!/bin/bash

# agent-browser installation script for Mac
# Usage: bash install-agent-browser.sh

set -e

echo "=== agent-browser Installation for Mac ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher required. Current: $(node --version)"
    exit 1
fi
echo "✓ Node.js $(node --version)"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    echo "⚠️  pnpm not found. Installing..."
    npm install -g pnpm
fi
echo "✓ pnpm $(pnpm --version)"

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install from https://git-scm.com/"
    exit 1
fi
echo "✓ Git $(git --version)"

# Check Chrome
if [ ! -d "/Applications/Google Chrome.app" ]; then
    echo "⚠️  Google Chrome not found. Please install from https://www.google.com/chrome/"
    echo "Installation will continue, but Chrome is required to use agent-browser."
fi

echo ""
echo "Installing agent-browser..."
echo ""

# Navigate to Documents
cd ~/Documents

# Clone or update repository
if [ -d "agent-browser" ]; then
    echo "agent-browser directory exists. Updating..."
    cd agent-browser
    git pull origin main
else
    echo "Cloning agent-browser repository..."
    git clone https://github.com/vercel-labs/agent-browser.git
    cd agent-browser
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pnpm install

# Install Chromium
echo ""
echo "Installing Chromium browser..."
npx playwright install chromium

# Build
echo ""
echo "Building TypeScript code..."
npm run build

# Verify installation
echo ""
echo "Verifying installation..."
if [ -f "bin/agent-browser" ]; then
    echo "✓ Binary found: bin/agent-browser"
    chmod +x bin/agent-browser
else
    echo "❌ Binary not found. Installation may have failed."
    exit 1
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "agent-browser installed to: ~/Documents/agent-browser"
echo ""
echo "To use agent-browser:"
echo "  cd ~/Documents/agent-browser"
echo "  AGENT_BROWSER_HOME=~/Documents/agent-browser \\"
echo "  ./bin/agent-browser --cdp 9222 <command>"
echo ""
echo "To start Chrome with debugging:"
echo "  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\"
echo "    --remote-debugging-port=9222 \\"
echo "    --user-data-dir=/tmp/chrome-debug &"
echo ""
echo "For more information, see:"
echo "  - Setup guide: ~/.claude/skills/chrome-automation/references/setup-mac.md"
echo "  - Commands: ~/.claude/skills/chrome-automation/references/commands.md"
echo ""
```

Make executable and run:
```bash
chmod +x install-agent-browser.sh
./install-agent-browser.sh
```

## Windows Installation Script

Save as `install-agent-browser.ps1`:

```powershell
# agent-browser installation script for Windows
# Usage: powershell -ExecutionPolicy Bypass -File install-agent-browser.ps1

Write-Host "=== agent-browser Installation for Windows ===" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js
try {
    $nodeVersion = node --version
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -lt 18) {
        Write-Host "❌ Node.js version 18 or higher required. Current: $nodeVersion" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check pnpm
try {
    $pnpmVersion = pnpm --version
    Write-Host "✓ pnpm $pnpmVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  pnpm not found. Installing..." -ForegroundColor Yellow
    npm install -g pnpm
    Write-Host "✓ pnpm installed" -ForegroundColor Green
}

# Check Git
try {
    $gitVersion = git --version
    Write-Host "✓ $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found. Please install from https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# Check Chrome
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromeFound = $true
        break
    }
}
if (-not $chromeFound) {
    Write-Host "⚠️  Google Chrome not found. Please install from https://www.google.com/chrome/" -ForegroundColor Yellow
    Write-Host "Installation will continue, but Chrome is required to use agent-browser." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installing agent-browser..." -ForegroundColor Yellow
Write-Host ""

# Navigate to Documents
Set-Location "$HOME\Documents"

# Clone or update repository
if (Test-Path "agent-browser") {
    Write-Host "agent-browser directory exists. Updating..." -ForegroundColor Yellow
    Set-Location agent-browser
    git pull origin main
} else {
    Write-Host "Cloning agent-browser repository..." -ForegroundColor Yellow
    git clone https://github.com/vercel-labs/agent-browser.git
    Set-Location agent-browser
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pnpm install

# Install Chromium
Write-Host ""
Write-Host "Installing Chromium browser..." -ForegroundColor Yellow
npx playwright install chromium

# Build
Write-Host ""
Write-Host "Building TypeScript code..." -ForegroundColor Yellow
npm run build

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
if (Test-Path "bin\agent-browser.cmd") {
    Write-Host "✓ Binary found: bin\agent-browser.cmd" -ForegroundColor Green
} else {
    Write-Host "❌ Binary not found. Installation may have failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "agent-browser installed to: $HOME\Documents\agent-browser" -ForegroundColor Cyan
Write-Host ""
Write-Host "To use agent-browser:" -ForegroundColor Cyan
Write-Host '  Set-Location "$HOME\Documents\agent-browser"'
Write-Host '  $env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"'
Write-Host '  .\bin\agent-browser.cmd --cdp 9222 <command>'
Write-Host ""
Write-Host "To start Chrome with debugging (64-bit):" -ForegroundColor Cyan
Write-Host '  Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" \'
Write-Host '    -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"'
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Cyan
Write-Host "  - Setup guide: ~/.claude/skills/chrome-automation/references/setup-windows.md"
Write-Host "  - Commands: ~/.claude/skills/chrome-automation/references/commands.md"
Write-Host ""
```

Run in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File install-agent-browser.ps1
```

## Quick Install Commands

### Mac One-liner

```bash
curl -fsSL https://raw.githubusercontent.com/vercel-labs/agent-browser/main/install.sh | bash
```

Or manual:
```bash
cd ~/Documents && \
git clone https://github.com/vercel-labs/agent-browser.git && \
cd agent-browser && \
pnpm install && \
npx playwright install chromium && \
npm run build
```

### Windows One-liner (PowerShell)

```powershell
Set-Location "$HOME\Documents"; `
git clone https://github.com/vercel-labs/agent-browser.git; `
Set-Location agent-browser; `
pnpm install; `
npx playwright install chromium; `
npm run build
```

## Uninstall Scripts

### Mac Uninstall

```bash
#!/bin/bash
# Uninstall agent-browser

echo "Removing agent-browser..."
rm -rf ~/Documents/agent-browser

echo "Removing Playwright cache..."
rm -rf ~/Library/Caches/ms-playwright

echo "agent-browser uninstalled."
echo "Note: pnpm and Node.js were not removed."
```

### Windows Uninstall

```powershell
# Uninstall agent-browser

Write-Host "Removing agent-browser..."
Remove-Item -Recurse -Force "$HOME\Documents\agent-browser" -ErrorAction SilentlyContinue

Write-Host "Removing Playwright cache..."
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ms-playwright" -ErrorAction SilentlyContinue

Write-Host "agent-browser uninstalled."
Write-Host "Note: pnpm and Node.js were not removed."
```

## Update Scripts

### Mac Update

```bash
#!/bin/bash
# Update agent-browser to latest version

cd ~/Documents/agent-browser
echo "Pulling latest changes..."
git pull origin main

echo "Updating dependencies..."
pnpm install

echo "Rebuilding..."
npm run build

echo "Updating Chromium..."
npx playwright install chromium

echo "Update complete!"
```

### Windows Update

```powershell
# Update agent-browser to latest version

Set-Location "$HOME\Documents\agent-browser"
Write-Host "Pulling latest changes..."
git pull origin main

Write-Host "Updating dependencies..."
pnpm install

Write-Host "Rebuilding..."
npm run build

Write-Host "Updating Chromium..."
npx playwright install chromium

Write-Host "Update complete!"
```
