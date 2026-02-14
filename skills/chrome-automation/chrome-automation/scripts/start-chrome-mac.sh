#!/bin/bash
# Chrome startup script with persistent profile support
# This script starts Chrome with a dedicated automation profile that preserves login states

set -e

# Define paths
CHROME_AUTOMATION_DIR="$HOME/Library/Application Support/Google/Chrome-Automation"
CHROME_DEFAULT_DIR="$HOME/Library/Application Support/Google/Chrome"
CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT=9222

echo "🔍 Checking Chrome automation profile..."

# Check if Chrome is already running with debug port
if ps aux | grep -v grep | grep "remote-debugging-port=$DEBUG_PORT" > /dev/null; then
    echo "✓ Chrome is already running with debug port $DEBUG_PORT"
    exit 0
fi

# Check if dedicated automation directory exists
if [ ! -d "$CHROME_AUTOMATION_DIR" ]; then
    echo "📦 First time setup: Creating dedicated Chrome automation profile..."

    # Create the automation directory
    mkdir -p "$CHROME_AUTOMATION_DIR"

    # Check if default Chrome profile exists
    if [ -d "$CHROME_DEFAULT_DIR/Default" ]; then
        echo "📋 Importing configuration from your existing Chrome profile..."
        echo "   (This includes your login states, cookies, and settings)"

        # Copy the Default profile, excluding large cache files
        rsync -av --progress \
            --exclude='Cache' \
            --exclude='Code Cache' \
            --exclude='GPUCache' \
            --exclude='Service Worker' \
            --exclude='ShaderCache' \
            --exclude='GrShaderCache' \
            --exclude='component_crx_cache' \
            --exclude='BrowserMetrics' \
            --exclude='CertificateRevocation' \
            --exclude='Crashpad' \
            --exclude='FileTypePolicies' \
            --exclude='OptimizationGuidePredictionModels' \
            --exclude='SafetyTips' \
            --exclude='SSLErrorAssistant' \
            --exclude='Subresource Filter' \
            --exclude='ZxcvbnData' \
            "$CHROME_DEFAULT_DIR/Default/" \
            "$CHROME_AUTOMATION_DIR/Default/"

        # Also copy Local State file for profile settings
        if [ -f "$CHROME_DEFAULT_DIR/Local State" ]; then
            cp "$CHROME_DEFAULT_DIR/Local State" "$CHROME_AUTOMATION_DIR/"
        fi

        echo "✓ Configuration imported successfully!"
    else
        echo "⚠️  No existing Chrome profile found. Starting with fresh profile."
        echo "   You'll need to log in manually on first use."
    fi
else
    echo "✓ Chrome automation profile found"
    echo "   Location: $CHROME_AUTOMATION_DIR"
fi

# Close any existing Chrome instances that might conflict
# (Optional: uncomment if you want to ensure clean start)
# pkill -f "Google Chrome" 2>/dev/null || true
# sleep 1

# Start Chrome with the dedicated automation profile
echo "🚀 Starting Chrome with automation profile..."
"$CHROME_APP" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$CHROME_AUTOMATION_DIR" &

# Wait for Chrome to start
sleep 3

# Verify Chrome started successfully
if ps aux | grep -v grep | grep "remote-debugging-port=$DEBUG_PORT" > /dev/null; then
    echo "✓ Chrome started successfully with debug port $DEBUG_PORT"
    echo ""
    echo "📍 Profile location: $CHROME_AUTOMATION_DIR"
    echo "🔗 Debug port: $DEBUG_PORT"
    echo ""
    echo "Your login states and cookies are preserved in this profile."
    echo "You only need to log in once - it will be remembered for future sessions."
else
    echo "❌ Failed to start Chrome"
    exit 1
fi
