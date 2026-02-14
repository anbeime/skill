# Auto-Installation Scripts

This directory contains automatic installation scripts for agent-browser that handle all dependencies without user confirmation.

## Scripts

### `auto-install-mac.sh`
Automatic installation script for macOS that:
- Checks if agent-browser is already installed and working
- Clones repository if needed
- Installs pnpm if missing
- Installs Playwright Chromium
- Checks and installs Rust toolchain (cargo, rustup)
- Sets up stable Rust toolchain
- Builds native binary
- Verifies installation

**Usage:**
```bash
bash ~/.claude/skills/chrome-automation/scripts/auto-install-mac.sh
```

### `auto-install-windows.ps1`
Automatic installation script for Windows (PowerShell) that:
- Checks if agent-browser is already installed and working
- Clones repository if needed
- Installs pnpm if missing
- Installs Playwright Chromium
- Downloads and installs Rust toolchain if needed
- Sets up stable Rust toolchain
- Builds native binary
- Verifies installation

**Usage:**
```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\chrome-automation\scripts\auto-install-windows.ps1"
```

## Requirements

### macOS
- Node.js (script will notify if missing)
- Git
- Internet connection

### Windows
- Node.js (script will notify if missing - download from https://nodejs.org/)
- Git
- Internet connection
- PowerShell (built-in)

## What Gets Installed

Both scripts automatically install these dependencies if missing:

1. **pnpm** - Fast, disk space efficient package manager
2. **Playwright Chromium** - Browser automation library
3. **Rust toolchain** - Required for building native binary
   - rustup (Rust installer)
   - cargo (Rust package manager)
   - stable toolchain
4. **agent-browser** - Native binary compiled from source

## Installation Location

- Repository: `~/Documents/agent-browser` (Mac) or `$HOME\Documents\agent-browser` (Windows)
- Binary: `~/Documents/agent-browser/bin/agent-browser` (Mac) or `$HOME\Documents\agent-browser\bin\agent-browser.cmd` (Windows)
- Rust: `~/.cargo/` (Mac) or `$HOME\.cargo\` (Windows)

## Troubleshooting

If installation fails:

1. **Check Node.js**: Ensure Node.js is installed
   - Mac: `node --version`
   - Windows: `node --version`
   - Download from: https://nodejs.org/

2. **Check Git**: Ensure Git is installed
   - Mac: `git --version`
   - Windows: `git --version`
   - Download from: https://git-scm.com/

3. **Re-run script**: The script is idempotent and can be run multiple times safely

4. **Check logs**: Script outputs detailed progress - review error messages

5. **Manual installation**: See main SKILL.md for manual installation steps

## Script Features

- ✅ Idempotent - safe to run multiple times
- ✅ Checks existing installation before proceeding
- ✅ Installs only missing dependencies
- ✅ Verifies installation success
- ✅ Provides detailed progress output
- ✅ Handles Rust PATH configuration automatically
- ✅ Sets up stable Rust toolchain
- ✅ No user confirmation required (fully automatic)
