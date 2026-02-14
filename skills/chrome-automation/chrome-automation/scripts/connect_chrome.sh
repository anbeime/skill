#!/bin/bash
# Connect to or start Chrome with remote debugging
# Usage: ./connect_chrome.sh [port]

PORT="${1:-9222}"

echo "🔍 Checking for Chrome with remote debugging on port $PORT..."

# Check if Chrome already running with debug port
if ps aux | grep -q "[r]emote-debugging-port=$PORT"; then
    echo "✅ Chrome already running with remote debugging on port $PORT"
    echo ""
    echo "Test connection with:"
    echo "  cd /Users/jyxc-dz-0100272/Documents/agent-browser"
    echo "  AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \\"
    echo "  ./bin/agent-browser --cdp $PORT get url"
    exit 0
fi

echo "🚀 Starting Chrome with remote debugging on port $PORT..."

# Start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=$PORT \
  --user-data-dir=/tmp/chrome-debug-$PORT &

# Wait for Chrome to start
echo "⏳ Waiting for Chrome to start..."
sleep 3

# Open initial page
echo "📄 Opening initial page..."
osascript -e 'tell application "Google Chrome" to activate' \
  -e 'tell application "Google Chrome" to open location "https://google.com"' 2>/dev/null

# Wait for page load
sleep 2

echo ""
echo "✅ Chrome started successfully!"
echo ""
echo "Chrome is now running with remote debugging on port $PORT"
echo "You should see a Chrome window open"
echo ""
echo "Test connection with:"
echo "  cd /Users/jyxc-dz-0100272/Documents/agent-browser"
echo "  AGENT_BROWSER_HOME=/Users/jyxc-dz-0100272/Documents/agent-browser \\"
echo "  ./bin/agent-browser --cdp $PORT snapshot -i"
