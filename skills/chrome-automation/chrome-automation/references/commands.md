# Agent-Browser Command Reference for CDP

Complete command reference for controlling Chrome via CDP (Chrome DevTools Protocol).

## Command Format

### Mac/Linux

```bash
cd ~/Documents/agent-browser
AGENT_BROWSER_HOME=~/Documents/agent-browser \
./bin/agent-browser --cdp 9222 <command> [options]
```

### Windows (PowerShell)

```powershell
Set-Location "$HOME\Documents\agent-browser"
$env:AGENT_BROWSER_HOME="$HOME\Documents\agent-browser"
.\bin\agent-browser.cmd --cdp 9222 <command> [options]
```

For brevity, examples below show only the command portion (works on both platforms).

## Navigation Commands

### open (goto, navigate)
Navigate to a URL.

```bash
--cdp 9222 open https://example.com
--cdp 9222 open google.com  # Auto-prepends https://
--cdp 9222 open file:///path/to/file.html
```

**Wait after:** Always wait 2-3 seconds for page load
```bash
--cdp 9222 open https://example.com
sleep 2
```

### back
Go back in history.

```bash
--cdp 9222 back
```

### forward
Go forward in history.

```bash
--cdp 9222 forward
```

### reload
Reload current page.

```bash
--cdp 9222 reload
```

## Page Analysis Commands

### snapshot
Get page structure.

```bash
--cdp 9222 snapshot              # Full accessibility tree
--cdp 9222 snapshot -i           # Interactive elements only (RECOMMENDED)
--cdp 9222 snapshot -c           # Compact output
--cdp 9222 snapshot -d 3         # Limit depth to 3
--cdp 9222 snapshot -s "#main"   # Scope to CSS selector
```

**Output format:**
```
- textbox "Email" [ref=e1]
- textbox "Password" [ref=e2]
- button "Submit" [ref=e3]
```

Use refs (@e1, @e2, @e3) in subsequent commands.

### get url
Get current URL.

```bash
--cdp 9222 get url
```

### get title
Get page title.

```bash
--cdp 9222 get title
```

### get text
Get element text content.

```bash
--cdp 9222 get text @e1
```

### get value
Get input field value.

```bash
--cdp 9222 get value @e1
```

### get html
Get element's innerHTML.

```bash
--cdp 9222 get html @e1
```

### get attr
Get element attribute.

```bash
--cdp 9222 get attr @e1 href
--cdp 9222 get attr @e1 class
```

### get count
Count elements matching selector.

```bash
--cdp 9222 get count ".item"
--cdp 9222 get count "button"
```

### get box
Get element bounding box.

```bash
--cdp 9222 get box @e1
```

### get styles
Get computed styles.

```bash
--cdp 9222 get styles @e1
```

## Interaction Commands

### click
Click an element.

```bash
--cdp 9222 click @e1
```

### dblclick
Double-click an element.

```bash
--cdp 9222 dblclick @e1
```

### fill
Clear and type text into input.

```bash
--cdp 9222 fill @e1 "john@example.com"
--cdp 9222 fill @e1 "text with spaces"
```

### type
Type text without clearing (appends).

```bash
--cdp 9222 type @e1 "additional text"
```

### press
Press keyboard key.

```bash
--cdp 9222 press Enter
--cdp 9222 press Tab
--cdp 9222 press Escape
--cdp 9222 press Control+a     # Key combination
--cdp 9222 press Command+c     # macOS
```

### keydown
Hold key down.

```bash
--cdp 9222 keydown Shift
```

### keyup
Release key.

```bash
--cdp 9222 keyup Shift
```

### hover
Hover over element.

```bash
--cdp 9222 hover @e1
```

### check
Check a checkbox.

```bash
--cdp 9222 check @e1
```

### uncheck
Uncheck a checkbox.

```bash
--cdp 9222 uncheck @e1
```

### select
Select dropdown option(s).

```bash
--cdp 9222 select @e1 "option value"
--cdp 9222 select @e1 "value1" "value2"  # Multiple
```

### focus
Focus an element.

```bash
--cdp 9222 focus @e1
```

### scroll
Scroll the page.

```bash
--cdp 9222 scroll down 500      # Scroll down 500px
--cdp 9222 scroll up 300        # Scroll up 300px
--cdp 9222 scroll down          # Default: 300px down
```

### scrollintoview (scrollinto)
Scroll element into view.

```bash
--cdp 9222 scrollintoview @e1
```

### drag
Drag and drop.

```bash
--cdp 9222 drag @e1 @e2  # Drag e1 to e2
```

### upload
Upload file to file input.

```bash
--cdp 9222 upload @e1 /path/to/file.pdf
```

## Wait Commands

### wait
Wait for conditions.

```bash
--cdp 9222 wait @e1                    # Wait for element
--cdp 9222 wait 2000                   # Wait 2000ms
--cdp 9222 wait --text "Success"       # Wait for text
--cdp 9222 wait -t "Success"           # Short form
--cdp 9222 wait --url "**/dashboard"   # Wait for URL pattern
--cdp 9222 wait -u "**/dashboard"      # Short form
--cdp 9222 wait --load networkidle     # Wait for network idle
--cdp 9222 wait -l networkidle         # Short form
--cdp 9222 wait --fn "window.ready"    # Wait for JS condition
--cdp 9222 wait -f "window.ready"      # Short form
```

## State Check Commands

### is visible
Check if element is visible.

```bash
--cdp 9222 is visible @e1
```

### is enabled
Check if element is enabled.

```bash
--cdp 9222 is enabled @e1
```

### is checked
Check if checkbox is checked.

```bash
--cdp 9222 is checked @e1
```

## Capture Commands

### screenshot
Take screenshot.

```bash
--cdp 9222 screenshot                    # Output to stdout
--cdp 9222 screenshot ~/Desktop/page.png # Save to file
--cdp 9222 screenshot --full             # Full page screenshot
--cdp 9222 screenshot -f                 # Short form
```

### pdf
Save page as PDF.

```bash
--cdp 9222 pdf output.pdf
```

## JavaScript Command

### eval
Execute JavaScript in page context.

```bash
--cdp 9222 eval "document.title"
--cdp 9222 eval "window.scrollTo(0, 500)"
--cdp 9222 eval "document.querySelector('.btn').click()"

# Multi-line with variables
--cdp 9222 eval "var el = document.querySelector('input'); el.value = 'text';"
```

**Note:** Use proper JavaScript syntax. Avoid optional chaining (?.),  use standard querySelector instead.

## Find Commands (Semantic Locators)

Alternative to refs when you know specific text/attributes.

### By role
```bash
--cdp 9222 find role button click --name "Submit"
--cdp 9222 find role textbox fill --name "Email" "user@test.com"
```

### By text
```bash
--cdp 9222 find text "Sign In" click
--cdp 9222 find text "Sign In" click --exact  # Exact match only
```

### By label
```bash
--cdp 9222 find label "Email" fill "user@test.com"
```

### By placeholder
```bash
--cdp 9222 find placeholder "Search" type "query"
```

### By alt text
```bash
--cdp 9222 find alt "Logo" click
```

### By title
```bash
--cdp 9222 find title "Close" click
```

### By test ID
```bash
--cdp 9222 find testid "submit-btn" click
```

### By position
```bash
--cdp 9222 find first ".item" click    # First match
--cdp 9222 find last ".item" click     # Last match
--cdp 9222 find nth 2 "a" hover        # 2nd match (0-indexed)
```

## Tab Commands

### tab
List or switch tabs.

```bash
--cdp 9222 tab              # List all tabs
--cdp 9222 tab 2            # Switch to tab index 2
--cdp 9222 tab close        # Close current tab
--cdp 9222 tab close 2      # Close tab index 2
--cdp 9222 tab new          # New tab
--cdp 9222 tab new https://example.com  # New tab with URL
```

## Frame Commands

### frame
Switch to iframe or back to main.

```bash
--cdp 9222 frame "#iframe-id"    # Switch to iframe
--cdp 9222 frame main            # Back to main frame
```

## Dialog Commands

### dialog
Handle JavaScript dialogs (alert, confirm, prompt).

```bash
--cdp 9222 dialog accept           # Accept dialog
--cdp 9222 dialog accept "text"    # Accept with input text
--cdp 9222 dialog dismiss          # Dismiss dialog
```

## Mouse Commands

### mouse move
Move mouse to coordinates.

```bash
--cdp 9222 mouse move 100 200
```

### mouse down
Press mouse button.

```bash
--cdp 9222 mouse down left
--cdp 9222 mouse down right
```

### mouse up
Release mouse button.

```bash
--cdp 9222 mouse up left
```

### mouse wheel
Scroll with mouse wheel.

```bash
--cdp 9222 mouse wheel 100   # Scroll down 100px
--cdp 9222 mouse wheel -100  # Scroll up 100px
```

## Debug Commands

### console
View console messages.

```bash
--cdp 9222 console              # Show all messages
--cdp 9222 console --clear      # Clear console
```

### errors
View page errors.

```bash
--cdp 9222 errors               # Show errors
--cdp 9222 errors --clear       # Clear errors
```

### highlight
Highlight element visually.

```bash
--cdp 9222 highlight @e1
```

## Cookie & Storage Commands

### cookies
Manage cookies.

```bash
--cdp 9222 cookies                      # Get all cookies
--cdp 9222 cookies set name value       # Set cookie
--cdp 9222 cookies clear                # Clear all cookies
```

### storage
Manage localStorage.

```bash
--cdp 9222 storage local                # Get all localStorage
--cdp 9222 storage local key            # Get specific key
--cdp 9222 storage local set key value  # Set value
--cdp 9222 storage local clear          # Clear all
```

## Browser Settings

### set viewport
Set viewport size.

```bash
--cdp 9222 set viewport 1920 1080
```

### set device
Emulate device.

```bash
--cdp 9222 set device "iPhone 14"
--cdp 9222 set device "iPad Pro"
```

### set geo (geolocation)
Set geolocation.

```bash
--cdp 9222 set geo 37.7749 -122.4194
```

### set offline
Toggle offline mode.

```bash
--cdp 9222 set offline on
--cdp 9222 set offline off
```

### set credentials (auth)
Set HTTP basic auth.

```bash
--cdp 9222 set credentials username password
```

### set media
Set media preferences.

```bash
--cdp 9222 set media dark                      # Dark color scheme
--cdp 9222 set media light                     # Light color scheme
--cdp 9222 set media light reduced-motion      # Multiple preferences
```

## Common Workflows

### Form submission workflow

**Mac/Linux:**
```bash
--cdp 9222 open https://example.com/form
sleep 2
--cdp 9222 snapshot -i
# Output: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]
--cdp 9222 fill @e1 "user@example.com"
--cdp 9222 fill @e2 "password123"
--cdp 9222 click @e3
sleep 2
--cdp 9222 screenshot result.png
```

**Windows:**
```powershell
.\bin\agent-browser.cmd --cdp 9222 open https://example.com/form
Start-Sleep -Seconds 2
.\bin\agent-browser.cmd --cdp 9222 snapshot -i
.\bin\agent-browser.cmd --cdp 9222 fill @e1 "user@example.com"
.\bin\agent-browser.cmd --cdp 9222 fill @e2 "password123"
.\bin\agent-browser.cmd --cdp 9222 click @e3
Start-Sleep -Seconds 2
.\bin\agent-browser.cmd --cdp 9222 screenshot result.png
```

### Search workflow

**Mac/Linux:**
```bash
--cdp 9222 open google.com
sleep 2
--cdp 9222 snapshot -i
# Output: textbox "Search" [ref=e1]
--cdp 9222 fill @e1 "search query"
--cdp 9222 press Enter
sleep 2
--cdp 9222 screenshot results.png
```

**Windows:**
```powershell
.\bin\agent-browser.cmd --cdp 9222 open google.com
Start-Sleep -Seconds 2
.\bin\agent-browser.cmd --cdp 9222 snapshot -i
.\bin\agent-browser.cmd --cdp 9222 fill @e1 "search query"
.\bin\agent-browser.cmd --cdp 9222 press Enter
Start-Sleep -Seconds 2
.\bin\agent-browser.cmd --cdp 9222 screenshot results.png
```

### Multi-page workflow
```bash
--cdp 9222 open https://site.com
sleep 2  # Windows: Start-Sleep -Seconds 2
--cdp 9222 snapshot -i
--cdp 9222 click @e1  # Click link
sleep 2  # Windows: Start-Sleep -Seconds 2
--cdp 9222 snapshot -i  # Get new refs after navigation
--cdp 9222 fill @e2 "text"
```

## Best Practices

1. **Always wait after navigation**
   ```bash
   --cdp 9222 open url
   sleep 2  # Wait for load
   ```

2. **Re-snapshot after DOM changes**
   ```bash
   --cdp 9222 click @e1
   sleep 1
   --cdp 9222 snapshot -i  # Get fresh refs
   ```

3. **Use screenshots for feedback**
   ```bash
   --cdp 9222 screenshot ~/Desktop/state.png
   # Then read and show to user
   ```

4. **Check URL after navigation**
   ```bash
   --cdp 9222 click @e1
   sleep 2
   --cdp 9222 get url  # Verify navigation
   ```

5. **Use -i flag for snapshots**
   ```bash
   --cdp 9222 snapshot -i  # Faster, shows only interactive elements
   ```
