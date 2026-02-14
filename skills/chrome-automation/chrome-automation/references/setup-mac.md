# agent-browser Installation Guide for Mac

Complete installation guide for setting up agent-browser on macOS.

## Prerequisites

Before installing agent-browser, ensure you have:

1. **Node.js** (v18 or higher)
2. **pnpm** package manager
3. **Git**
4. **Google Chrome** browser

### Check Prerequisites

```bash
# Check Node.js version
node --version
# Should show v18.x.x or higher

# Check pnpm
pnpm --version
# If not installed, run: npm install -g pnpm

# Check Git
git --version

# Check Chrome
ls /Applications/Google\ Chrome.app
```

## Installation Steps

### Step 1: Clone Repository

```bash
# Navigate to Documents folder
cd ~/Documents

# Clone agent-browser from GitHub
git clone https://github.com/vercel-labs/agent-browser.git

# Enter directory
cd agent-browser
```

### Step 2: Install Dependencies

```bash
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

```bash
# Install Playwright's Chromium browser
npx playwright install chromium
```

**Expected output:**
```
Downloading Chromium XXX.X - XX.X Mb [====================] 100%
Chromium XXX.X downloaded to /Users/.../Library/Caches/ms-playwright/chromium-XXXX
```

### Step 4: Build TypeScript Code

```bash
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

```bash
# Check if binary exists
test -f ~/Documents/agent-browser/bin/agent-browser && echo "✓ Installation successful" || echo "✗ Installation failed"

# Test basic command
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser ./bin/agent-browser --version
```

## Post-Installation Setup

### Set Up Environment Variables (Optional)

Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
# agent-browser shortcuts
export AGENT_BROWSER_HOME="$HOME/Documents/agent-browser"
export PATH="$AGENT_BROWSER_HOME/bin:$PATH"

# Alias for quick access
alias ab='AGENT_BROWSER_HOME=$HOME/Documents/agent-browser $HOME/Documents/agent-browser/bin/agent-browser'
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

### Configure Chrome for Remote Debugging

Create a launch script for Chrome with debugging enabled:

```bash
# Create script
cat > ~/launch-chrome-debug.sh << 'EOF'
#!/bin/bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug &
EOF

# Make executable
chmod +x ~/launch-chrome-debug.sh
```

Usage:
```bash
~/launch-chrome-debug.sh
```

## Verification Tests

### Test 1: Basic Command

```bash
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --help
```

### Test 2: Start Chrome and Connect

```bash
# Start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug &

# Wait for Chrome to start
sleep 2

# Open a page
osascript -e 'tell application "Google Chrome" to open location "https://google.com"'

# Test connection
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 get url
```

**Expected output:**
```
https://google.com
```

### Test 3: Take Screenshot

```bash
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 screenshot ~/Desktop/test.png

# Check if file exists
ls -lh ~/Desktop/test.png
```

## Troubleshooting

### Issue: "pnpm: command not found"

**Solution:**
```bash
npm install -g pnpm
```

### Issue: "Permission denied" when running agent-browser

**Solution:**
```bash
chmod +x ~/Documents/agent-browser/bin/agent-browser
```

### Issue: "Daemon not found" error

**Solution:**
Always set `AGENT_BROWSER_HOME` environment variable:
```bash
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command>
```

### Issue: Chrome connection refused

**Solution:**
1. Check if Chrome is running with debug port:
```bash
ps aux | grep "remote-debugging-port=9222"
```

2. If not running, start it:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug &
```

### Issue: Build fails with TypeScript errors

**Solution:**
```bash
# Clean and rebuild
cd ~/Documents/agent-browser
rm -rf node_modules dist
pnpm install
npm run build
```

### Issue: Chromium download fails

**Solution:**
```bash
# Try manual installation
npx playwright install chromium --force

# Or use system proxy if behind firewall
export HTTPS_PROXY=http://your-proxy:port
npx playwright install chromium
```

## Updating agent-browser

To update to the latest version:

```bash
cd ~/Documents/agent-browser

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

```bash
# Remove directory
rm -rf ~/Documents/agent-browser

# Remove Playwright cache (optional)
rm -rf ~/Library/Caches/ms-playwright

# Remove environment variables from ~/.zshrc or ~/.bash_profile
# (manually edit the file)
```

## Additional Resources

- Official Repository: https://github.com/vercel-labs/agent-browser
- Playwright Documentation: https://playwright.dev
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/

## Quick Reference

```bash
# Installation check
test -f ~/Documents/agent-browser/bin/agent-browser && echo "✓ Installed" || echo "✗ Not installed"

# Start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug &

# Basic command format
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command>

# Common commands
./bin/agent-browser --cdp 9222 open <url>
./bin/agent-browser --cdp 9222 snapshot -i
./bin/agent-browser --cdp 9222 screenshot <path>
./bin/agent-browser --cdp 9222 get url
```
