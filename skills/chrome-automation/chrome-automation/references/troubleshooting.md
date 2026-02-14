# Troubleshooting Chrome Automation

Common issues and solutions when using agent-browser with Chrome CDP on Mac and Windows.

## Installation Issues

### Mac: "command not found: agent-browser"

**Cause:** Binary not in PATH or doesn't exist

**Solution:**
```bash
# Check if binary exists
ls -la ~/Documents/agent-browser/bin/agent-browser

# If not found, run setup (see references/setup-mac.md)
cd ~/Documents/agent-browser
pnpm install
npm run build
```

### Windows: "agent-browser.cmd not recognized"

**Cause:** Binary not found or PATH not set

**Solution:**
```powershell
# Check if binary exists
Test-Path "$HOME\Documents\agent-browser\bin\agent-browser.cmd"

# If not found, run setup (see references/setup-windows.md)
Set-Location "$HOME\Documents\agent-browser"
pnpm install
npm run build
```

### "No binary found for darwin-arm64" (Mac)

**Cause:** Native binary not downloaded during postinstall

**Solution:**
```bash
cd ~/Documents/agent-browser
pnpm install --force
# Or manually download from GitHub releases
```

### Windows: "Execution policy" error

**Cause:** PowerShell execution policy blocking scripts

**Solution:**
```powershell
# Set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single session
powershell -ExecutionPolicy Bypass
```

## Connection Issues

### "Daemon not found"

**Cause:** AGENT_BROWSER_HOME not set or not running from project directory

**Mac Solution:**
```bash
# Always set AGENT_BROWSER_HOME and run from project directory
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command>
```

**Windows Solution:**
```powershell
# Set environment variable and run
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 <command>
```

### "No page found. Make sure the app has loaded content."

**Cause:** Chrome running but no pages open

**Mac Solution:**
```bash
# Open a page with AppleScript
osascript -e 'tell application "Google Chrome" to open location "https://google.com"'

# Wait for load
sleep 2

# Then retry
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 snapshot -i
```

**Windows Solution:**
```powershell
# Open Chrome and navigate (Chrome will open automatically)
Start-Process chrome "https://google.com"

# Wait for load
Start-Sleep -Seconds 2

# Then retry
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 snapshot -i
```

### "Connection refused" or "Failed to connect"

**Cause:** Chrome not running with remote debugging port

**Mac Solution:**
```bash
# Check if Chrome running with debug port
ps aux | grep "remote-debugging-port=9222"

# If not, start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug &

# Wait and open page
sleep 2
osascript -e 'tell application "Google Chrome" to open location "https://google.com"'
```

**Windows Solution:**
```powershell
# Check if Chrome running with debug port
Get-Process chrome | Where-Object {$_.CommandLine -like "*remote-debugging-port*"}

# If not, start Chrome with debugging (64-bit)
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\chrome-debug"

# Wait and Chrome will open automatically
Start-Sleep -Seconds 2
```

## Runtime Issues

### "(no interactive elements)" when expecting elements

**Cause:** Page not fully loaded or elements not interactive

**Solutions:**
1. Wait longer after navigation
```bash
agent-browser --cdp 9222 open https://example.com
sleep 3  # Increase wait time
agent-browser --cdp 9222 snapshot -i
```

2. Use full snapshot to see all elements
```bash
agent-browser --cdp 9222 snapshot
```

3. Check if page is in an iframe
```bash
agent-browser --cdp 9222 frame "#iframe-id"
agent-browser --cdp 9222 snapshot -i
```

### Element refs (@e1, @e2) not working

**Cause:** Refs invalidated after DOM changes

**Solution:**
Re-snapshot after any navigation or significant page change:
```bash
agent-browser --cdp 9222 click @e1
sleep 1
agent-browser --cdp 9222 snapshot -i  # Get new refs
```

### JavaScript eval errors

**Cause:** Invalid JavaScript syntax or security restrictions

**Solution:**
1. Use proper JavaScript syntax (no fancy quotes)
```bash
# Wrong
agent-browser --cdp 9222 eval "input?.value"

# Right
agent-browser --cdp 9222 eval "document.querySelector('input').value"
```

2. Use variables for complex operations
```bash
agent-browser --cdp 9222 eval "var el = document.querySelector('input'); el.value = 'text';"
```

## Site-Specific Issues

### Security verification / QR codes

**Cause:** Site detected automation and requires manual verification

**Solution:**
1. Take screenshot to show user
```bash
agent-browser --cdp 9222 screenshot ~/Desktop/verification.png
```

2. Inform user to complete verification manually in Chrome window

3. Wait for completion

4. Check URL to confirm verification passed
```bash
agent-browser --cdp 9222 get url
```

5. Continue workflow

### "Network connection error" or similar messages

**Cause:** Site blocking automated browsers

**Solutions:**
1. Use --headed mode (already visible with CDP)
2. User may need to manually interact first
3. Some sites cannot be automated and require manual access

### Page stuck loading

**Cause:** Waiting for network requests that never complete

**Solution:**
Use network idle wait:
```bash
agent-browser --cdp 9222 wait --load networkidle
```

Or just proceed after timeout:
```bash
sleep 5
agent-browser --cdp 9222 snapshot -i
```

## Performance Issues

### Commands slow or timing out

**Cause:** Large page or slow network

**Solutions:**
1. Increase timeouts
2. Use scoped snapshots
```bash
agent-browser --cdp 9222 snapshot -i -s "#main-content"
```

3. Use compact mode
```bash
agent-browser --cdp 9222 snapshot -c
```

### Multiple Chrome instances

**Cause:** Starting new Chrome without closing old ones

**Solution:**
```bash
# Kill all Chrome processes
pkill -f "Google Chrome"

# Or kill specific debug instance
pkill -f "remote-debugging-port=9222"

# Then restart
./scripts/connect_chrome.sh
```

## Data Issues

### Screenshots are blank or wrong content

**Cause:** Timing issue or wrong tab

**Solutions:**
1. Wait longer before screenshot
```bash
sleep 2
agent-browser --cdp 9222 screenshot output.png
```

2. Check current URL
```bash
agent-browser --cdp 9222 get url
```

3. List tabs and switch if needed
```bash
agent-browser --cdp 9222 tab
agent-browser --cdp 9222 tab 1
```

### Cannot get element text or values

**Cause:** Element not visible or wrong selector

**Solutions:**
1. Check if element visible
```bash
agent-browser --cdp 9222 is visible @e1
```

2. Use snapshot to verify ref
```bash
agent-browser --cdp 9222 snapshot -i
```

3. Try JavaScript eval as fallback
```bash
agent-browser --cdp 9222 eval "document.querySelector('.target').textContent"
```

## Environment Issues

### macOS: "Chrome" is damaged and can't be opened

**Cause:** Running Chrome from non-standard location

**Solution:**
Use standard Chrome path:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug
```

### Mac: Permission denied errors

**Cause:** Script not executable or directory permissions

**Solution:**
```bash
# Make scripts executable
chmod +x ~/Documents/agent-browser/scripts/*.sh

# Fix directory permissions
chmod -R u+rw ~/Documents/agent-browser
```

### Windows: Chrome path not found

**Cause:** Chrome installed in non-standard location

**Solution:**
```powershell
# Try 64-bit path
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"

# Or 32-bit path
Start-Process "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222"

# Or find Chrome location
Get-ChildItem "C:\Program Files" -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue
```

### Windows: Long path errors

**Cause:** Windows path length limitation

**Solution:**
```powershell
# Enable long paths (run as Administrator)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use shorter installation path
# Install to C:\agent-browser instead of Documents
```

## Debug Workflow

When facing unknown issues:

### Mac Debug Steps

1. Check Chrome is running
```bash
ps aux | grep Chrome
```

2. Check debug port
```bash
ps aux | grep "remote-debugging-port=9222"
```

3. Test basic connection
```bash
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 get url
```

4. Take screenshot to see current state
```bash
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 screenshot /tmp/debug.png
```

5. Check console for errors
```bash
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 console
```

6. Get page errors
```bash
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 errors
```

### Windows Debug Steps

1. Check Chrome is running
```powershell
Get-Process chrome
```

2. Check debug port
```powershell
Get-Process chrome | Where-Object {$_.CommandLine -like "*remote-debugging-port*"}
```

3. Test basic connection
```powershell
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 get url
```

4. Take screenshot to see current state
```powershell
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 screenshot "$env:TEMP\debug.png"
```

5. Check console for errors
```powershell
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 console
```

6. Get page errors
```powershell
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 errors
```

## Platform-Specific Resources

- **Mac Installation**: See `references/setup-mac.md`
- **Windows Installation**: See `references/setup-windows.md`
- **Command Reference**: See `references/commands.md`
