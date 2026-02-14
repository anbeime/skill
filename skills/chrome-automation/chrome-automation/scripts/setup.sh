#!/bin/bash
# Setup agent-browser for Chrome automation
# Usage: ./setup.sh [install_directory]

set -e

INSTALL_DIR="${1:-/Users/jyxc-dz-0100272/Documents/agent-browser}"

echo "🚀 Setting up agent-browser at: $INSTALL_DIR"

# Check if directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ Directory not found: $INSTALL_DIR"
    echo "Please clone agent-browser first:"
    echo "  git clone https://github.com/vercel-labs/agent-browser.git $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

# Step 1: Install dependencies
echo "📦 Installing dependencies..."
if command -v pnpm &> /dev/null; then
    pnpm install
elif command -v npm &> /dev/null; then
    npm install
else
    echo "❌ Neither pnpm nor npm found. Please install Node.js first."
    exit 1
fi

# Step 2: Install Chromium
echo "🌐 Installing Chromium browser..."
npx playwright install chromium

# Step 3: Build TypeScript
echo "🔨 Building TypeScript code..."
npm run build

# Step 4: Verify installation
echo "✅ Verifying installation..."
if [ -f "$INSTALL_DIR/bin/agent-browser" ]; then
    echo "✓ Binary found"
else
    echo "❌ Binary not found"
    exit 1
fi

if [ -d "$INSTALL_DIR/node_modules" ]; then
    echo "✓ Dependencies installed"
else
    echo "❌ Dependencies missing"
    exit 1
fi

if [ -d "$INSTALL_DIR/dist" ]; then
    echo "✓ TypeScript compiled"
else
    echo "❌ TypeScript not compiled"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Environment variable to set:"
echo "  export AGENT_BROWSER_HOME=$INSTALL_DIR"
echo ""
echo "Test with:"
echo "  cd $INSTALL_DIR"
echo "  AGENT_BROWSER_HOME=$INSTALL_DIR ./bin/agent-browser --help"
