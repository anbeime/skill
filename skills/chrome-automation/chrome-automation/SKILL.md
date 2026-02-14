---
name: chrome-automation
description: Connect to and control Google Chrome browser using agent-browser with CDP (Chrome DevTools Protocol). Use when the user wants to automate their existing Chrome browser, see browser actions in real-time, or needs to control the Chrome instance they're already using. Handles installation, setup, connecting via remote debugging, and all browser automation tasks with live visual feedback.
allowed-tools: Bash(*)
---

# Chrome Browser Automation with Real-time Control

Control the user's Google Chrome browser using agent-browser connected via Chrome DevTools Protocol (CDP). All actions are visible in real-time in the user's browser window.

## ⚠️ CRITICAL: Automatic Installation & Dependency Check

**BEFORE using this skill, ALWAYS run the auto-installation check:**

This skill automatically checks and installs all required dependencies without user confirmation. The installation process verifies:
- agent-browser repository and binary
- Node.js and pnpm
- Playwright Chromium
- Rust toolchain (cargo)
- Native binary compilation

**Auto-installation workflow:**

```bash
# Mac: Run auto-install script
bash ~/.claude/skills/chrome-automation/scripts/auto-install-mac.sh

# Windows: Run auto-install script (PowerShell)
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\auto-install-windows.ps1"
```

**The script will:**
1. Check if agent-browser binary exists and works
2. Install missing dependencies automatically (pnpm, Rust, etc.)
3. Clone repository if not present
4. Build native binary with proper Rust toolchain
5. Verify installation success

**Critical rules:**
- ❌ DO NOT fall back to using built-in browser tools (browser_use_desktop)
- ✅ MUST run auto-install script before any browser automation
- ✅ Only proceed with browser automation AFTER successful installation
- ✅ Script handles all dependency checks automatically

**Why agent-browser is required:**
- Provides real-time visual feedback in user's actual Chrome browser
- Allows user to see and interact with automation in progress
- Offers precise element selection and interaction capabilities
- Built-in browser tools are NOT a substitute for this skill's functionality

## Quick Start

### First-time setup (automatic)

**Run the auto-install script first:**

```bash
# Mac
bash ~/.claude/skills/chrome-automation/scripts/auto-install-mac.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\auto-install-windows.ps1"
```

The script automatically handles:
- Repository cloning
- Dependency installation (pnpm, Playwright)
- Rust toolchain setup
- Native binary compilation

### Connect and control Chrome

**IMPORTANT: Use the start-chrome script to preserve login states across sessions**

```bash
# Mac: Start Chrome with persistent profile (RECOMMENDED)
# This preserves your login states, cookies, and settings
bash ~/.claude/skills/chrome-automation/scripts/start-chrome-mac.sh

# Windows: Start Chrome with persistent profile (PowerShell)
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\start-chrome-windows.ps1"

# Use agent-browser with --cdp flag
cd /Users/jyxc-dz-0100272/Documents/agent-browser
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 snapshot -i
```

**What the start-chrome script does:**
1. First run: Creates a dedicated automation profile at `~/Library/Application Support/Google/Chrome-Automation`
2. First run: Imports your existing Chrome configuration (login states, cookies, settings)
3. Subsequent runs: Uses the existing automation profile - all your logins are preserved
4. You only need to log in once - it will be remembered for future sessions

## Core Workflow

**CRITICAL: Always show browser state to user after each significant action using screenshots.**

1. **Connect**: Ensure Chrome running with remote debugging port 9222
2. **Navigate**: Open pages using `--cdp 9222` flag
3. **Snapshot**: Get interactive elements with `snapshot -i`
4. **Interact**: Use element refs (@e1, @e2, etc.)
5. **Screenshot**: Capture state and show to user
6. **Report**: Describe what's visible in browser

### Standard operation pattern

```bash
# Set path variables
export AB_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser
cd $AB_HOME

# Navigate
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 open https://example.com
sleep 2

# Get interactive elements
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 snapshot -i

# Screenshot to show user
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot /tmp/state.png

# Interact
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 fill @e1 "text"
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 press Enter

# Capture result
sleep 2
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot /tmp/result.png
```

## Installation & Setup

### Automatic Installation (RECOMMENDED)

**Always use the auto-install script - it handles all dependencies automatically:**

#### Mac Installation

```bash
# Run auto-install script
bash ~/.claude/skills/chrome-automation/scripts/auto-install-mac.sh
```

**What it does:**
1. Checks if agent-browser binary exists and works
2. Clones repository if missing
3. Installs Node.js dependencies (pnpm)
4. Installs Playwright Chromium
5. Checks/installs Rust toolchain (cargo, rustup)
6. Sets up stable Rust toolchain if needed
7. Builds native binary with `npm run build:native`
8. Verifies installation success

**Requirements:**
- Node.js (will notify if missing)
- Git (for cloning repository)
- Internet connection

#### Windows Installation

```powershell
# Run auto-install script (PowerShell)
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\auto-install-windows.ps1"
```

**What it does:**
1. Checks if agent-browser binary exists and works
2. Clones repository if missing
3. Installs Node.js dependencies (pnpm)
4. Installs Playwright Chromium
5. Downloads and installs Rust toolchain if needed
6. Sets up stable Rust toolchain
7. Builds native binary with `npm run build:native`
8. Verifies installation success

**Requirements:**
- Node.js (will notify if missing - download from https://nodejs.org/)
- Git (for cloning repository)
- Internet connection

### Manual Installation (Advanced Users Only)

If you prefer manual installation or need to troubleshoot:

#### Mac Manual Steps

```bash
# 1. Clone repository
cd ~/Documents
git clone https://github.com/vercel-labs/agent-browser.git
cd agent-browser

# 2. Install Node dependencies
pnpm install
npx playwright install chromium

# 3. Install Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
rustup default stable

# 4. Build native binary
npm run build:native
```

#### Windows Manual Steps

```powershell
# 1. Clone repository
Set-Location "$HOME\Documents"
git clone https://github.com/vercel-labs/agent-browser.git
Set-Location agent-browser

# 2. Install Node dependencies
pnpm install
npx playwright install chromium

# 3. Install Rust (if not installed)
# Download from: https://win.rustup.rs/x86_64
# Or use the auto-install script

# 4. Build native binary
npm run build:native
```

### Verify Installation

After installation (automatic or manual), verify it works:

```bash
# Mac
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser ./bin/agent-browser --version

# Windows (PowerShell)
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME = "$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --version
```

### Troubleshooting Installation

**"No binary found for darwin-arm64" or "No binary found for win32-x64":**
- Rust is not installed or not in PATH
- Run the auto-install script, it will handle Rust installation
- Or manually install Rust and run `npm run build:native`

**"cargo: command not found":**
- Rust toolchain not in PATH
- Mac: `export PATH="$HOME/.cargo/bin:$PATH"`
- Windows: `$env:PATH = "$HOME\.cargo\bin;$env:PATH"`
- Then run `rustup default stable` and `npm run build:native`

**"rustup could not choose a version":**
- Default toolchain not set
- Run: `rustup default stable`
- Then rebuild: `npm run build:native`

#### Common Rust Installation Issues

**Issue 1: Permission denied when installing Rust (Mac)**

When running the Rust installer, you may encounter:
```
error: could not amend shell profile: '/Users/username/.bash_profile': 
could not write rcfile file: Permission denied (os error 13)
```

**Solution:**
This error is usually **harmless** - Rust binaries are still installed successfully to `~/.cargo/bin/`. The error only affects automatic PATH configuration in shell profiles.

**Fix steps:**
```bash
# Mac: Set default toolchain manually
/Users/username/.cargo/bin/rustup default stable

# This will download and install:
# - cargo, clippy, rust-docs, rust-std, rustc, rustfmt
```

**Issue 2: Rust installed but cargo not found (Mac)**

After Rust installation, running `cargo` fails with "command not found".

**Root cause:** 
- Rust binaries are in `~/.cargo/bin/` but not in current shell's PATH
- Default toolchain not configured

**Solution:**
```bash
# Use full path to set default toolchain
~/.cargo/bin/rustup default stable

# Then build with full path
cd ~/Documents/agent-browser/cli
~/.cargo/bin/cargo build --release

# Or add to PATH for current session
export PATH="$HOME/.cargo/bin:$PATH"
cargo build --release
```

**Issue 3: Rust installation permission errors (Windows)**

On Windows, Rust installer may fail with access denied errors.

**Solution:**
```powershell
# Run PowerShell as Administrator, then:
# Download and run Rust installer
Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile "$env:TEMP\rustup-init.exe"
& "$env:TEMP\rustup-init.exe" -y

# Set default toolchain
& "$env:USERPROFILE\.cargo\bin\rustup.exe" default stable

# Add to PATH for current session
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
```

**Issue 4: Build fails even after Rust installation**

**Symptoms:**
- `npm run build:native` fails
- "cargo: command not found" in build output

**Solution:**
```bash
# Mac: Build with explicit cargo path
cd ~/Documents/agent-browser/cli
~/.cargo/bin/cargo build --release

# Then copy binary manually
cd ~/Documents/agent-browser
node scripts/copy-native.js

# Windows: Build with explicit cargo path
Set-Location "$HOME\Documents\agent-browser\cli"
& "$env:USERPROFILE\.cargo\bin\cargo.exe" build --release

# Then copy binary manually
Set-Location "$HOME\Documents\agent-browser"
node scripts/copy-native.js
```

**Key Takeaway:**
Even if Rust installation shows permission errors, the binaries are usually installed successfully. The main issue is:
1. Default toolchain not configured → Run `rustup default stable` with full path
2. PATH not updated → Use full paths to cargo/rustup, or manually add `~/.cargo/bin` to PATH

For detailed troubleshooting, see:
- `references/setup-mac.md`
- `references/setup-windows.md`
- `references/troubleshooting.md`

## Chrome Connection

### Method 1: Start Chrome with persistent profile (Recommended)

**Use the start-chrome script to preserve login states across sessions:**

```bash
# Mac: Start Chrome with persistent profile
bash ~/.claude/skills/chrome-automation/scripts/start-chrome-mac.sh

# Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\start-chrome-windows.ps1"
```

**First time setup (automatic):**
- Creates dedicated profile at `~/Library/Application Support/Google/Chrome-Automation` (Mac)
- Or `%USERPROFILE%\AppData\Local\Google\Chrome-Automation` (Windows)
- Imports your existing Chrome configuration (login states, cookies, bookmarks)
- Excludes large cache files to save space

**Subsequent runs:**
- Uses the existing automation profile
- All your logins are preserved
- No need to log in again

```bash
# Verify connection after starting Chrome
cd /Users/jyxc-dz-0100272/Documents/agent-browser
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 get url
```

### Method 2: Connect to existing Chrome

```bash
# Check if Chrome already running with debug port
ps aux | grep "remote-debugging-port=9222"

# If yes, connect directly
cd /Users/jyxc-dz-0100272/Documents/agent-browser
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 get url
```

### Method 3: Start Chrome manually (not recommended)

If you need to start Chrome manually without the script:

```bash
# Mac: Start with persistent profile directory
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Automation" &

# Windows (PowerShell):
Start-Process "chrome.exe" -ArgumentList @(
    "--remote-debugging-port=9222",
    "--user-data-dir=`"$HOME\AppData\Local\Google\Chrome-Automation`""
)
```

**Note:** Using `--user-data-dir=/tmp/chrome-debug` (temporary directory) will NOT preserve login states.

## Usage Patterns

### Pattern 1: Web Search

```bash
cd /Users/jyxc-dz-0100272/Documents/agent-browser
export AB_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser

# Open search site
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 open xiaohongshu.com
sleep 2

# Get elements
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 snapshot -i
# Output: textbox "搜索小红书" [ref=e2]

# Fill and search
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 fill @e2 "labubu"
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 press Enter

# Capture result
sleep 2
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot ~/Desktop/result.png
```

### Pattern 2: Form Automation

```bash
cd /Users/jyxc-dz-0100272/Documents/agent-browser
export AB_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser

# Navigate
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 open https://example.com/form

# Get form fields
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 snapshot -i

# Fill form
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 fill @e1 "John Doe"
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 fill @e2 "john@example.com"
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 click @e3

# Verify
sleep 2
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot ~/Desktop/submitted.png
```

### Pattern 3: Handle Security Verification

When sites show security verification (QR codes, captchas):

```bash
# Take screenshot
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot ~/Desktop/verification.png

# Show user and inform them
echo "Site requires verification - please complete in browser window"

# User completes verification manually

# Check URL after verification
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 get url

# Continue workflow
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 snapshot -i
```

## Real-time Feedback Protocol

**MANDATORY: Provide visual feedback after every significant action**

After navigation, clicks, or form submissions:
1. Take screenshot
2. Get current URL
3. Read screenshot and describe to user

```bash
# After any action
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 screenshot ~/Desktop/current.png
AGENT_BROWSER_HOME=$AB_HOME ./bin/agent-browser --cdp 9222 get url

# Then use Read tool on screenshot
# Describe what's visible to user
```

## Command Reference

All commands use this format:
```bash
cd /Users/jyxc-dz-0100272/Documents/agent-browser
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command>
```

### Essential Commands

**Navigation:**
- `open <url>` - Navigate to URL
- `back` - Go back
- `reload` - Reload page
- `get url` - Get current URL

**Page Analysis:**
- `snapshot -i` - Get interactive elements (RECOMMENDED)
- `get title` - Get page title

**Interaction:**
- `click @e1` - Click element
- `fill @e1 "text"` - Fill input
- `press Enter` - Press key
- `scroll down 500` - Scroll

**Capture:**
- `screenshot path.png` - Screenshot
- `get text @e1` - Get element text

**JavaScript:**
- `eval "code"` - Execute JavaScript

For complete command reference, see the agent-browser skill at:
`/Users/jyxc-dz-0100272/Documents/agent-browser/skills/agent-browser/SKILL.md`

## Troubleshooting

### Installation Issues

**"No binary found for darwin-arm64/win32-x64":**
```bash
# Mac: Run auto-install script - it handles Rust installation
bash ~/.claude/skills/chrome-automation/scripts/auto-install-mac.sh

# Windows: Run auto-install script
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\auto-install-windows.ps1"

# Or manually:
# Mac:
# 1. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# 2. Set toolchain: ~/.cargo/bin/rustup default stable
# 3. Build: cd ~/Documents/agent-browser/cli && ~/.cargo/bin/cargo build --release
# 4. Copy: cd ~/Documents/agent-browser && node scripts/copy-native.js

# Windows:
# 1. Download Rust: https://win.rustup.rs/x86_64
# 2. Set toolchain: & "$env:USERPROFILE\.cargo\bin\rustup.exe" default stable
# 3. Build: cd "$HOME\Documents\agent-browser\cli"; & "$env:USERPROFILE\.cargo\bin\cargo.exe" build --release
# 4. Copy: cd "$HOME\Documents\agent-browser"; node scripts/copy-native.js
```

**"cargo: command not found":**
```bash
# Mac: Use full path to cargo
~/.cargo/bin/rustup default stable
cd ~/Documents/agent-browser/cli
~/.cargo/bin/cargo build --release

# Windows: Use full path to cargo
& "$env:USERPROFILE\.cargo\bin\rustup.exe" default stable
Set-Location "$HOME\Documents\agent-browser\cli"
& "$env:USERPROFILE\.cargo\bin\cargo.exe" build --release
```

**"rustup could not choose a version":**
```bash
# Mac: Set default Rust toolchain with full path
~/.cargo/bin/rustup default stable

# Windows: Set default Rust toolchain with full path
& "$env:USERPROFILE\.cargo\bin\rustup.exe" default stable
```

**Rust installation shows permission errors but completes:**
```bash
# Mac: This is usually harmless - binaries are installed
# Just set default toolchain manually:
~/.cargo/bin/rustup default stable

# Windows: Run installer as Administrator if needed
# Then set default toolchain:
& "$env:USERPROFILE\.cargo\bin\rustup.exe" default stable
```

### Runtime Issues

**"Daemon not found" error:**
```bash
# Must set AGENT_BROWSER_HOME and run from project directory
cd /Users/jyxc-dz-0100272/Documents/agent-browser
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command>
```

### "No page found" error
```bash
# Chrome needs at least one page open
osascript -e 'tell application "Google Chrome" to open location "https://google.com"'
sleep 2

# Then retry
AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \
./bin/agent-browser --cdp 9222 snapshot -i
```

### Connection refused
```bash
# Check if Chrome running with debug port
ps aux | grep "remote-debugging-port=9222"

# If not, start it with persistent profile
bash ~/.claude/skills/chrome-automation/scripts/start-chrome-mac.sh
```

## Best Practices

1. **Auto-install first** - ALWAYS run the auto-install script before first use
2. **Use start-chrome script** - Use `start-chrome-mac.sh` or `start-chrome-windows.ps1` to preserve login states
3. **Check dependencies** - Script automatically verifies all required tools (Node.js, Rust, pnpm)
4. **Never use fallback tools** - Do NOT use browser_use_desktop or other built-in browser tools when this skill is requested
5. **Rebuild if needed** - If binary errors occur, re-run auto-install script
6. **Never use detached mode** - Do NOT use terminal detached mode when starting Chrome
7. **Always screenshot** - Show user what's happening
8. **Wait after navigation** - Use `sleep 2` after page loads
9. **Check URL** - Verify navigation succeeded
10. **Handle security** - Inform user, wait for manual completion
11. **Re-snapshot** - Get fresh refs after DOM changes
12. **Descriptive paths** - Save screenshots with clear names
13. **Report state** - Describe browser content to user

## Profile Management

### Reset automation profile

If you want to reset the automation profile and re-import from your main Chrome:

```bash
# Mac: Remove automation profile and restart
rm -rf ~/Library/Application\ Support/Google/Chrome-Automation
bash ~/.claude/skills/chrome-automation/scripts/start-chrome-mac.sh

# Windows (PowerShell): Remove automation profile and restart
Remove-Item -Recurse -Force "$HOME\AppData\Local\Google\Chrome-Automation"
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\start-chrome-windows.ps1"
```

### Profile locations

| Platform | Automation Profile Location |
|----------|----------------------------|
| Mac | `~/Library/Application Support/Google/Chrome-Automation` |
| Windows | `%USERPROFILE%\AppData\Local\Google\Chrome-Automation` |

This profile is separate from your daily Chrome, so automation activities won't affect your main browser.
