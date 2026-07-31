# Agent Deployment Guide

## Core Principle

**Always use the `manageAgent` MCP tool to deploy Agent services.**

It natively supports SSE streaming, session persistence, and Python 3.10 runtime — purpose-built for Agent scenarios.

Do **NOT** use `createFunction` or `manageCloudRun` for Agent deployment.

## Why HTTP Cloud Functions First

| Dimension | HTTP Cloud Functions | CloudRun |
|-----------|---------------------|----------|
| SSE Streaming | ✅ Native support | ✅ Supported |
| WebSocket | ✅ Native support | ✅ Supported |
| Deployment Complexity | Low (no Dockerfile needed) | High (container config required) |
| Cost | Pay-per-invocation, scales to zero | Pay-per-instance-hour |
| Cold Start | Yes, mitigated with provisioned instances | Yes, mitigated with min instances |
| Supported Runtimes | Node.js, Python | Any |

---

## ⚠️ DEPLOYMENT IS A 4-STEP BLOCKING PIPELINE

<!-- INSTRUCTION (AI MUST EXECUTE EVERY STEP IN ORDER) -->

> **AI: You MUST execute Steps 1→2→3→4 in order. Do NOT skip any step.**
> **Do NOT call `manageAgent` until Step 3 (Verification) passes ALL checks.**

```
Step 1: Ensure Python 3.10  ──▶  Step 2: Build env/  ──▶  Step 3: Verify  ──▶  Step 4: Deploy
       (BLOCKING)                   (BLOCKING)              (BLOCKING)           (final)
```

---

## Step 1: Ensure Python 3.10

<!-- INSTRUCTION (AI MUST EXECUTE) -->

Execute one of the following to ensure Python 3.10 is available:

```bash
# Check if python3.10 already exists
python3.10 --version 2>/dev/null || python3 --version

# If NOT 3.10.x, install it:
# Option A: brew (macOS)
brew install python@3.10

# Option B: pyenv
pyenv install 3.10
pyenv local 3.10
```

**Verification (REQUIRED before proceeding):**
```bash
python3.10 --version
# MUST output: Python 3.10.x
# If it shows 3.11+ or 3.9-, STOP and fix before continuing.
```

<details>
<summary>Why must it be Python 3.10? (background info, AI may skip)</summary>

pip's `--python-version` flag correctly selects wheel files for the target version, but it does **NOT** reliably evaluate environment markers (e.g., `exceptiongroup; python_version < "3.11"`) — it may use the **host interpreter's version** instead of the target version. This causes conditional dependencies like `exceptiongroup` (required by `anyio` on Python < 3.11) to be silently skipped, leading to `ModuleNotFoundError` at runtime on the cloud (which runs Python 3.10).
</details>

---

## Step 2: Build env/ (One-Shot Install)

<!-- INSTRUCTION (AI MUST EXECUTE) -->

> ### ⚠️ CRITICAL: `env/` is an immutable build artifact
>
> The ONLY correct workflow is:
> 1. **Delete** → `rm -rf ./env`
> 2. **Install** → single `pip install` command (below)
> 3. **Never touch again**
>
> **NEVER** run a second `pip install` into `env/`. **NEVER** manually copy/move/delete files inside `env/`.
> If you need to change anything, edit `requirements.txt` and redo steps 1–2 from scratch.

**Execute this script as-is. Do NOT break it into separate steps. Do NOT modify any line.**

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(pwd)"

# ── Detect Python 3.10 ──
PYTHON_BIN=""
if command -v python3.10 &>/dev/null; then
  PYTHON_BIN="python3.10"
elif python3 --version 2>&1 | grep -q "3\.10\."; then
  PYTHON_BIN="python3"
else
  echo "❌ ERROR: Python 3.10 not found. Run Step 1 first."
  exit 1
fi
echo "✅ Using: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"

# ── Atomic env/ rebuild ──
rm -rf ./env && mkdir ./env

# ── One-shot install ALL deps ──
$PYTHON_BIN -m pip install -r ./requirements.txt \
  --platform manylinux2014_x86_64 \
  --target ./env \
  --python-version 3.10 \
  --only-binary=:all: \
  --upgrade

echo "✅ env/ built successfully"
```

If `pip install` reports **any** errors, **STOP** and resolve the error first. Do NOT ignore errors and proceed to deploy — the resulting `env/` will be incomplete.

---

## Step 3: Verify env/ Integrity (MANDATORY)

<!-- INSTRUCTION (AI MUST EXECUTE) -->

> **Do NOT call `manageAgent` until ALL checks below pass.**
> **If ANY check fails, the ONLY fix is: edit requirements.txt → rm -rf env/ → re-run Step 2.**

### 3a. Verify all top-level packages are present

```bash
# List all packages from requirements.txt and verify they exist in env/
# This works for ANY framework — no hardcoded package names
python3.10 -c "
import subprocess, sys, os

# Read requirements.txt
with open('requirements.txt') as f:
    reqs = [line.strip().split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('[')[0].strip()
            for line in f if line.strip() and not line.startswith('#') and not line.startswith('-')]

# For each requirement, check if it's importable from env/
env_path = os.path.abspath('./env')
failed = []
for req in reqs:
    # Convert package name to import name (hyphens → underscores)
    import_name = req.replace('-', '_').lower()
    # Check if directory or .py file exists
    found = (os.path.isdir(os.path.join(env_path, import_name)) or
             os.path.isfile(os.path.join(env_path, import_name + '.py')) or
             os.path.isfile(os.path.join(env_path, import_name + '.so')))
    if not found:
        # Some packages have different import names, try dist-info
        dist_matches = [d for d in os.listdir(env_path) 
                       if d.endswith('.dist-info') and req.replace('-','_').lower() in d.lower()]
        if dist_matches:
            found = True
    if not found:
        failed.append(f'{req} (expected: {import_name})')
    else:
        print(f'  ✅ {req}')

if failed:
    print()
    for f in failed:
        print(f'  ❌ MISSING: {f}')
    print()
    print('Fix: Check requirements.txt spelling, then rm -rf env/ and re-run Step 2')
    sys.exit(1)
else:
    print()
    print('✅ All packages verified in env/')
"
```

### 3b. Verify entry point imports work

```bash
# Dynamically test that the project's main entry file can resolve imports
# Replace 'server.py' with whatever file the project uses as entry point
PYTHONPATH=./env python3.10 -c "
import sys, ast, os

# Find entry point (server.py or main.py)
entry = None
for candidate in ['server.py', 'main.py', 'app.py']:
    if os.path.isfile(candidate):
        entry = candidate
        break

if not entry:
    print('⚠️  No standard entry file found (server.py/main.py/app.py). Skipping import check.')
    sys.exit(0)

print(f'Checking imports from {entry}...')

# Parse and extract top-level imports
with open(entry) as f:
    tree = ast.parse(f.read())

modules = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            modules.add(alias.name.split('.')[0])
    elif isinstance(node, ast.ImportFrom) and node.module:
        modules.add(node.module.split('.')[0])

# Filter to non-stdlib, non-relative modules
import importlib.util
failed = []
for mod in sorted(modules):
    if mod.startswith('_') or mod in ('os', 'sys', 'json', 'logging', 'typing', 'datetime', 'pathlib', 'asyncio', 'abc', 'enum', 'dataclasses', 'collections', 'functools', 'importlib', 'contextlib', 'inspect', 'traceback', 're', 'io', 'copy', 'math', 'time', 'uuid', 'hashlib', 'base64', 'urllib', 'http', 'socket', 'subprocess', 'platform', 'struct', 'itertools', 'operator', 'warnings', 'signal', 'threading', 'multiprocessing', 'concurrent', 'queue', 'pickle', 'shelve', 'tempfile', 'shutil', 'glob', 'fnmatch', 'string', 'textwrap', 'codecs', 'csv', 'configparser', 'argparse', 'getpass', 'secrets', 'hmac', 'ssl', 'email', 'html', 'xml', 'pprint'):
        continue
    spec = importlib.util.find_spec(mod)
    if spec:
        print(f'  ✅ {mod}')
    else:
        failed.append(mod)
        print(f'  ❌ {mod}')

if failed:
    print(f'\n❌ Import verification failed for: {failed}')
    print('Fix: Ensure these are in requirements.txt, then rm -rf env/ and re-run Step 2')
    sys.exit(1)
else:
    print('\n✅ All imports verified')
"
```

### 3c. Verify scf_bootstrap

```bash
# Check scf_bootstrap exists, is executable, and sets PYTHONPATH
test -f ./scf_bootstrap || { echo "❌ scf_bootstrap not found"; exit 1; }
test -x ./scf_bootstrap || { echo "❌ scf_bootstrap not executable. Run: chmod +x scf_bootstrap"; exit 1; }
grep -q 'PYTHONPATH.*env' ./scf_bootstrap || { echo "❌ scf_bootstrap missing PYTHONPATH=./env"; exit 1; }
echo "✅ scf_bootstrap OK"
```

**All 3 checks passed? → Proceed to Step 4.**

---

## Step 4: Deploy with manageAgent

```
manageAgent(action="create", runtime="Python3.10", installDependency=false, targetPath="...")
```

**IMPORTANT**: Do NOT add `env/` to the `ignore` list — it must be uploaded with the code.

---

## Error Recovery Playbook

> **Golden Rule: ANY problem with `env/` has exactly ONE fix:**
> ```
> edit requirements.txt (if needed) → rm -rf env/ → re-run Step 2 script → re-run Step 3
> ```
> **There is NO other fix. Never deviate from this.**

### Error: `pip install` reports "no matching distribution"

- **Cause**: A package doesn't have a `manylinux2014_x86_64` wheel for Python 3.10
- **Fix**: Pin a version in `requirements.txt` that has a compatible wheel, or check spelling
- **Then**: `rm -rf env/` → re-run Step 2

### Error: `ModuleNotFoundError` at runtime (ANY module)

- **Cause 1**: The module is missing from `requirements.txt` → add it
- **Cause 2**: `env/` was built with Python 3.11+ → ensure Python 3.10, rebuild
- **Cause 3**: `env/` was built incrementally (multiple pip installs) → rebuild atomically
- **Fix**: `rm -rf env/` → re-run Step 2

### Error: Namespace package submodule missing (e.g., `cloudbase_agent.xxx`)

- **Cause**: Multiple `pip install` commands into `env/` caused namespace package fragmentation
- **Fix**: `rm -rf env/` → re-run Step 2 (single command installs all packages atomically)

### ⛔ PROHIBITED OPERATIONS (will cause deployment failures)

- ⛔ Running a second `pip install` into an existing `env/`
- ⛔ Copying files from another project directory into `env/`
- ⛔ Manually creating or modifying `__init__.py` inside `env/`
- ⛔ Deleting selective directories inside `env/` and reinstalling partial deps
- ⛔ Using `pip install` inside `scf_bootstrap` (wastes cold-start time)

---

## Python Runtime Version

**Always select Python 3.10 runtime** (`runtime="Python3.10"`). This is the recommended version for CloudBase Agent Python SDK because:

- Full compatibility with all `cloudbase-agent-*` packages
- Best performance for async/await patterns used by FastAPI
- Stable and well-tested on the CloudBase platform

Do **NOT** use Python 3.9 or earlier — many SDK features require Python >= 3.10.

## Code Adaptation Notes

### Port Listening

Your server **must** listen on the port from environment variable `SCF_RUNTIME_PORT`:

```python
import os
from cloudbase_agent.server import AgentServiceApp

port = int(os.environ.get("SCF_RUNTIME_PORT", "9000"))
AgentServiceApp().run(create_agent, port=port, host="0.0.0.0")
```

### Startup Script

The startup script must be named `scf_bootstrap` (no file extension), placed in the project root, and have executable permissions:

```bash
#!/bin/bash
export PYTHONPATH="./env:$PYTHONPATH"
/var/lang/python310/bin/python3 -u server.py
```

Make it executable:

```bash
chmod +x scf_bootstrap
```

### CORS Configuration

Ensure CORS is properly configured for cross-origin requests:

```python
from cloudbase_agent.server import AgentServiceApp

app = AgentServiceApp()
app.set_cors_config(allow_origins=["*"])
app.run(create_agent, port=port)
```

Or if using FastAPI directly:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Complete Deployment Example

### Project Structure

```
my-agent/
├── agents/
│   └── chat/agent.py        # Agent workflow (any framework)
├── env/                      # Pre-installed dependencies (built by Step 2)
├── server.py                 # Main entry point
├── scf_bootstrap             # CloudBase startup script
├── requirements.txt          # Dependencies
└── .env                      # Environment variables (local only)
```

### scf_bootstrap

```bash
#!/bin/bash
export PYTHONPATH="./env:$PYTHONPATH"
/var/lang/python310/bin/python3 -u server.py
```

### requirements.txt (example — varies by framework)

```
# Core (always needed)
cloudbase-agent-server
python-dotenv

# Framework adapter (pick ONE based on your choice)
cloudbase-agent-langgraph   # For LangGraph-based agents
# cloudbase-agent-crewai    # For CrewAI-based agents
# cloudbase-agent-coze      # For Coze platform agents

# LLM provider (example)
langchain-openai
```

## When to Use CloudRun Instead

Despite HTTP Cloud Functions being preferred, use CloudRun in these cases:

- Custom Docker image required (special system-level dependencies like FFmpeg, Chromium, etc.)
- Resource requirements exceed Cloud Function limits
- Persistent local file storage needed
- Need to install native C extensions that require specific OS packages

For CloudRun deployment, use a Dockerfile with Python 3.11:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=9000
CMD ["python", "server.py"]
```

## Summary

| Decision | Choice |
|----------|--------|
| **Deployment tool** | `manageAgent` MCP tool (MUST USE) |
| **Python runtime** | Python 3.10 (MUST USE, `runtime="Python3.10"`) |
| **Dependency strategy** | Local pre-packaging to `./env` (**MUST use Python 3.10 interpreter**, `installDependency=false`) |
| **Build workflow** | Step 1 (Python) → Step 2 (build env/) → Step 3 (verify) → Step 4 (deploy) |
| **env/ rebuild rule** | ALWAYS atomic: `rm -rf env/` → single `pip install` — NEVER incremental |
| **Default platform** | HTTP Cloud Functions |
| **Fallback platform** | CloudRun (only for special requirements) |
| **Startup script** | `scf_bootstrap` — set `PYTHONPATH="./env:$PYTHONPATH"`, do NOT `pip install` at startup |
| **Port** | Read from `SCF_RUNTIME_PORT` env var |
