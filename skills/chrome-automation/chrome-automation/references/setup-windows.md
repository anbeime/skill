# agent-browser Installation Guide for Windows

Complete installation guide for setting up agent-browser on Windows.

## Prerequisites

Before installing agent-browser, ensure you have:

1. **Node.js** (v18 or higher)
2. **pnpm** package manager
3. **Git for Windows**
4. **Google Chrome** browser
5. **PowerShell** (comes with Windows)

### Check Prerequisites

Open PowerShell and run:

```powershell
# Check Node.js version
node --version
# Should show v18.x.x or higher

# Check pnpm
pnpm --version
# If not installed, run: npm install -g pnpm

# Check Git
git --version

# Check Chrome
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
# Or for 32-bit: Test-Path "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
```

### Install Missing Prerequisites

**Node.js:**
- Download from: https://nodejs.org/
- Install LTS version (v18 or higher)

**pnpm:**
```powershell
npm install -g pnpm
```

**Git:**
- Download from: https://git-scm.com/download/win
- Install with default options

**Chrome:**
- Download from: https://www.google.com/chrome/

## Installation Steps

### Step 1: Clone Repository

Open PowerShell:

```powershell
# Navigate to Documents folder
Set-Location "$HOME\Documents"

# Clone agent-browser from GitHub
git clone https://github.com/vercel-labs/agent-browser.git

# Enter directory
Set-Location agent-browser
```

### Step 2: Install Dependencies

```powershell
# Install Node.js dependencies using pnpm
pnpm install

# This will install all required packages including:
# - Playwright
# - TypeScript
# - Other dependencies
```

**Expected output:**
```
Packages: +XXX
Progress: resolved XXX, reused XXX, downloaded XX
```

### Step 3: Install Chromium Browser

```powershell
# Install Playwright's Chromium browser
npx playwright install chromium
```

**Expected output:**
```
Downloading Chromium XXX.X - XX.X Mb [====================] 100%
Chromium XXX.X downloaded to C:\Users\...\AppData\Local\ms-playwright\chromium-XXXX
```

### Step 4: Build TypeScript Code

```powershell
# Compile TypeScript to JavaScript
npm run build
```

**Expected output:**
```
> agent-browser@x.x.x build
> tsc

Build completed successfully
```

### Step 5: Verify Installation

```powershell
# Check if binary exists
Test-Path "$HOME\Documents\agent-browser\bin\agent-browser.cmd"
# Should return: True

# Test basic command
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --version
```

## Post-Installation Setup

### Set Up Environment Variables (Optional)

**Method 1: PowerShell Profile (Recommended)**

```powershell
# Open PowerShell profile
notepad $PROFILE
# If file doesn't exist, create it first:
# New-Item -Path $PROFILE -Type File -Force

# Add these lines:
$env:AGENT_BROWSER_HOME = "$HOME\Documents\agent-browser"
$env:PATH = "$env:AGENT_BROWSER_HOME\bin;$env:PATH"

# Create alias
function ab { 
    $env:AGENT_BROWSER_HOME = "$HOME\Documents\agent-browser"
    & "$HOME\Documents\agent-browser\bin\agent-browser.cmd" $args 
}

# Save and reload
. $PROFILE
```

**Method 2: System Environment Variables**

1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `AGENT_BROWSER_HOME`
6. Variable value: `C:\Users\YourUsername\Documents\agent-browser`
7. Click OK

### Configure Chrome for Remote Debugging

Create a launch script for Chrome with debugging enabled:

```powershell
# Create script
@"
@echo off
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=%TEMP%\chrome-debug
"@ | Out-File -FilePath "$HOME\launch-chrome-debug.bat" -Encoding ASCII

# Or for 32-bit Chrome:
@"
@echo off
start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=%TEMP%\chrome-debug
"@ | Out-File -FilePath "$HOME\launch-chrome-debug.bat" -Encoding ASCII
```

Usage:
```powershell
& "$HOME\launch-chrome-debug.bat"
```

## Verification Tests

### Test 1: Basic Command

```powershell
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --help
```

### Test 2: Start Chrome and Connect

```powershell
# Start Chrome with debugging (64-bit)
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"

# Wait for Chrome to start
Start-Sleep -Seconds 2

# Open a page (Chrome should open automatically)
# Or manually navigate to https://google.com

# Test connection
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 get url
```

**Expected output:**
```
https://google.com
```

### Test 3: Take Screenshot

```powershell
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 screenshot "$HOME\Desktop\test.png"

# Check if file exists
Test-Path "$HOME\Desktop\test.png"
```

## Troubleshooting

### Issue: "pnpm: command not found"

**Solution:**
```powershell
npm install -g pnpm

# If still not working, restart PowerShell
```

### Issue: "Execution policy" error when running scripts

**Solution:**
```powershell
# Check current policy
Get-ExecutionPolicy

# Set to RemoteSigned (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or Bypass (less secure)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

### Issue: "Daemon not found" error

**Solution:**
Always set `AGENT_BROWSER_HOME` environment variable:
```powershell
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 <command>
```

### Issue: Chrome connection refused

**Solution:**
1. Check if Chrome is running with debug port:
```powershell
Get-Process chrome | Where-Object {$_.CommandLine -like "*remote-debugging-port*"}
```

2. If not running, start it:
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"
```

### Issue: Build fails with TypeScript errors

**Solution:**
```powershell
# Clean and rebuild
Set-Location "$HOME\Documents\agent-browser"
Remove-Item -Recurse -Force node_modules, dist -ErrorAction SilentlyContinue
pnpm install
npm run build
```

### Issue: Chromium download fails

**Solution:**
```powershell
# Try manual installation
npx playwright install chromium --force

# Or use system proxy if behind firewall
$env:HTTPS_PROXY="http://your-proxy:port"
npx playwright install chromium
```

### Issue: Path with spaces causes errors

**Solution:**
Use quotes around paths:
```powershell
& "$HOME\Documents\agent-browser\bin\agent-browser.cmd" --cdp 9222 open "https://example.com"
```

### Issue: Long path errors during installation

**Solution:**
Enable long paths in Windows:
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use Git Bash for installation instead of PowerShell
```

## Updating agent-browser

To update to the latest version:

```powershell
Set-Location "$HOME\Documents\agent-browser"

# Pull latest changes
git pull origin main

# Reinstall dependencies
pnpm install

# Rebuild
npm run build

# Update Chromium if needed
npx playwright install chromium
```

## Uninstallation

To completely remove agent-browser:

```powershell
# Remove directory
Remove-Item -Recurse -Force "$HOME\Documents\agent-browser"

# Remove Playwright cache (optional)
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ms-playwright"

# Remove environment variables
# - Edit PowerShell profile: notepad $PROFILE
# - Or remove from System Environment Variables via GUI
```

## Additional Resources

- Official Repository: https://github.com/vercel-labs/agent-browser
- Playwright Documentation: https://playwright.dev
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- PowerShell Documentation: https://docs.microsoft.com/powershell/

## Quick Reference

```powershell
# Installation check
Test-Path "$HOME\Documents\agent-browser\bin\agent-browser.cmd"

# Start Chrome with debugging (64-bit)
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"

# Start Chrome with debugging (32-bit)
Start-Process "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"

# Basic command format
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 <command>

# Common commands
.\bin\agent-browser.cmd --cdp 9222 open <url>
.\bin\agent-browser.cmd --cdp 9222 snapshot -i
.\bin\agent-browser.cmd --cdp 9222 screenshot <path>
.\bin\agent-browser.cmd --cdp 9222 get url
```

## Notes for Windows Users

1. **Use PowerShell, not Command Prompt** - PowerShell has better support for modern tools
2. **Watch out for path separators** - Use `\` for Windows paths, not `/`
3. **Quotes are important** - Always quote paths with spaces
4. **Execution policy** - You may need to adjust PowerShell execution policy
5. **Antivirus** - Some antivirus software may flag Chromium downloads; add exception if needed
6. **Firewall** - Chrome debugging port (9222) may need firewall exception
