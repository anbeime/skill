---
name: email-concierge
description: Local AI email assistant that automates unread-mail processing, offline-safe classification and reply drafting, local draft editing/approval queues, calendar conflict checks, voice transcription, and confirmed SMTP sending when connectivity returns. Use when the user wants to manage email, check inbox, draft or edit replies, queue messages offline, approve/send email, handle meeting invites, or mentions email assistant, IMAP, SMTP, voice memo, local AI email.
---

# Email Concierge — Local AI Email Assistant

A privacy-first email agent that reads, understands, and drafts replies to your emails. Text inference runs locally via OpenVINO GenAI with device priority NPU > GPU > CPU — no data leaves your machine.

**Platforms:** Windows · macOS · Linux (x86-64 and arm64)

## Architecture

```
IMAP Mailbox ──→ read_mailbox ──→ classify_summarize (OpenVINO GenAI, batched)
                                        │
iCal Files  ──→ check_calendar          │
                                        ▼
Microphone  ──→ start_voice_memo ──→ transcribe_memo (distil-whisper, optional)
                                        │
                                        ▼
                                 draft_reply (OpenVINO GenAI, 3 styles, single call)
```

**Models:** `OpenVINO/Qwen3-4B-int4-ov` (~2 GB, int4 OpenVINO format, auto-downloaded to `state/models/`) for classification and drafting; `distil-whisper-large-v3-int8-ov` (optional) for transcription.

## Agent execution

Treat this as a cross-platform skill. Resolve `SKILL_DIR` from the loaded `SKILL.md`; never assume a Windows path or a particular shell. The bundled `setup_auto.py` detects OS, architecture, shell, package manager, Python, Intel NPU/OpenVINO devices, and local model availability, then installs only compatible components. `setup.bat` and `setup.sh` are thin wrappers.

Resolve this `SKILL.md` directory as `SKILL_DIR`; do not assume the current workspace contains the executable. On Windows/Qoder, prefer:

```powershell
$skillDir = Join-Path $env:USERPROFILE ".qoder\skills\email-concierge"
& "$skillDir\venv\Scripts\python.exe" "$skillDir\email_concierge.py" --diagnose --json
```

Run `setup_auto.py --project-dir "$skillDir"` before automated inbox work, or when diagnostics report `setup_required=true`; setup installs missing components (including `openvino-genai`) and downloads the configured LLM model. Run `--diagnose --json` after setup. `local_ai_ready` defaults to `true` on supported Windows, macOS, and Linux systems. `local_ai_installed` reports whether OpenVINO, openvino-genai, and the model are all present. `llm_device` shows the device inference will use (highest available of NPU/GPU/CPU unless `device` pins one) and `llm_model_downloaded` whether the model files exist locally. NPU acceleration is ready only when `aipc_ready=true` and `openvino_devices` includes `NPU`.

The bootstrapper supports Windows PowerShell/CMD, macOS zsh/Bash, and Linux shells. It creates a local venv, installs core dependencies and OpenVINO GenAI via pip (no system elevation required), and downloads the LLM model directly from the ModelScope domestic source (`https://modelscope.cn`). Use `--no-openvino` or `--no-llm-model` only for constrained/offline environments. Setup also deletes the legacy `EmailConcierge-Ollama` logon task registered by older versions.

When executed without a TTY (e.g. by Qoder), `setup_auto.py` automatically enables `--yes` and skips system package manager installs on non-first installs. A marker file at `state/.setup_completed.json` records completion.

**Performance notes:** the first generation on a device compiles the model graph — on NPU this can take several minutes; the compiled cache in `state/ov_cache/<device>` makes subsequent runs start in seconds. Classification is one batched call for all emails and drafting is one merged call for all three styles (JSON-parsed), with keyword classification and template drafts as fallbacks so the workflow never blocks on model failure.

## Automation policy

For inbox requests, run `--inbox` by default. It automatically reads unread mail without marking it read, falls back to cached mail while offline, classifies every message, checks calendar conflicts for meeting messages, creates local reply drafts, and persists them in `state/draft_queue.json`. If the local LLM is unavailable, create an editable deterministic draft and continue.

Only request user input for missing required IMAP/SMTP credentials, explicit reply instructions, draft edits, or final send confirmation. Never send automatically: require `--confirm-send` after the user has approved the queued draft. When offline, finish all local work and leave sending pending for a later `--send`.

---

## Installation

### Automated install for Qoder

A `qoder.json` manifest is included. Qoder can install the skill automatically with the platform-specific installer below. Existing `email_concierge_config.json` and `state/` are preserved across reinstalls.

**Windows**
```powershell
.\install_qoder.ps1

# Copy files only, without package/model installation
.\install_qoder.ps1 -NoSetup
```
All dependencies (openvino-genai included) install into the local venv and the model downloads to `state/models/`; no administrator elevation is needed. Subsequent reinstalls are silent and preserve `email_concierge_config.json` and `state/`.

From CMD, run `install_qoder.bat`; it delegates to the same PowerShell flow and returns the installer exit code.

**macOS / Linux**
```bash
bash install_qoder.sh
```
Everything installs into the local venv without root. PortAudio (for voice recording) is the only optional system package; install it with your package manager when needed.

After installation, restart Qoder or open a new agent session so it reloads `SKILL.md`.

### Manual install

Copy the skill directory into the target app's skill folder and run the bootstrapper:

```bash
python3 install_skill.py --target qoder --destination ~/.qoder/skills
# or
python3 install_skill.py --target codex --destination ~/.codex/skills
```

Use `--no-setup` to copy files without installing dependencies. The installer honours `.qoderignore`, merges upgrades, and skips `venv/`, `__pycache__/`, `state/`, `tests/`, and transient audio files. A non-zero setup result is returned to the caller and included in `--json` output.

### Windows (manual)

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt -r requirements-openvino.txt
venv\Scripts\python email_concierge.py --diagnose --json
```

### macOS / Linux (manual)

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt -r requirements-openvino.txt
venv/bin/python email_concierge.py --diagnose --json
```

For system audio recording on Unix, install PortAudio first:

```bash
# macOS
brew install portaudio

# Debian/Ubuntu
sudo apt install libportaudio2 portaudio19-dev

# Fedora/RHEL
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio
```

---

## Configuration

Run the interactive wizard only when IMAP details are missing. It asks only for the required host, email address, and app password; defaults cover the port, folder, model, calendar, and transcription settings.

```bash
# macOS / Linux
venv/bin/python email_concierge.py --setup

# Windows
venv\Scripts\python.exe email_concierge.py --setup
```

For unattended use, set local environment variables instead. Environment values override JSON configuration.

```bash
EMAIL_CONCIERGE_IMAP_HOST=imap.example.com
EMAIL_CONCIERGE_IMAP_PORT=993
EMAIL_CONCIERGE_IMAP_USER=you@example.com
EMAIL_CONCIERGE_IMAP_PASSWORD=your-app-password
EMAIL_CONCIERGE_IMAP_FOLDER=INBOX
```

Optional overrides use the same pattern: `EMAIL_CONCIERGE_LLM_MODEL_ID`, `EMAIL_CONCIERGE_LLM_MODEL_DIR`, `EMAIL_CONCIERGE_OLLAMA_MODEL_TRANSCRIBE` (optional Ollama transcription backend), `EMAIL_CONCIERGE_CALENDAR_DIR`, `EMAIL_CONCIERGE_WHISPER_MODEL_DIR`, `EMAIL_CONCIERGE_DEVICE` (`AUTO`/`NPU`/`GPU`/`CPU`), `EMAIL_CONCIERGE_MAX_EMAILS`, `EMAIL_CONCIERGE_SMTP_HOST`, `EMAIL_CONCIERGE_SMTP_PORT`, `EMAIL_CONCIERGE_SMTP_USER`, `EMAIL_CONCIERGE_SMTP_PASSWORD`, `EMAIL_CONCIERGE_SMTP_USE_TLS`, and `EMAIL_CONCIERGE_STATE_DIR`.

Key JSON fields:

| Field | Meaning |
|---|---|
| `llm_model_id` | HuggingFace repo of the OpenVINO int4 model (default `OpenVINO/Qwen3-4B-int4-ov`) |
| `llm_model_dir` | Explicit model directory override; empty → `state/models/<repo-name>` |
| `device` | `AUTO` (default, NPU → GPU → CPU) or a pinned `NPU`/`GPU`/`CPU` |
| `ollama_model_transcribe` | Optional Ollama model for transcription only (e.g. `whisper`); empty disables |

**IMAP app passwords:**
- Gmail: Google Account → Security → App passwords
- Outlook: Microsoft → Security → Advanced → App passwords
- Yahoo: Account → Security → App passwords

---

## Tools Reference

### read_mailbox
Fetches unread emails via IMAP.
```bash
python email_concierge.py --inbox
```

### classify_summarize
Classifies each email into `todo|meeting|notification|promotion` and generates a one-line summary. One batched OpenVINO GenAI call for all emails; keyword fallback when the model is unavailable. Runs automatically with `--inbox`.

### check_calendar
Parses `.ics` files and finds events overlapping a target time.
```bash
python email_concierge.py --check-cal 2026-09-01
python email_concierge.py --check-cal today
```

### start_voice_memo
Records audio from the default microphone.
```bash
python email_concierge.py --record 30
```
Saves 16 kHz mono WAV. Ctrl+C stops early.

### transcribe_memo
Transcribes audio to text. Priority: distil-whisper (OpenVINO) → Ollama (if `ollama_model_transcribe` set) → transcribe-translate skill.
```bash
python email_concierge.py --transcribe voice_memo.wav
```

### draft_reply
Generates 3-style replies (formal / friendly / concise) in a single merged OpenVINO GenAI call; per-style template fallback.

### Offline queue and sending
```bash
python email_concierge.py --queue --json
python email_concierge.py --edit MESSAGE_ID "Updated reply text" --style friendly
python email_concierge.py --approve MESSAGE_ID
python email_concierge.py --send
python email_concierge.py --send --confirm-send
python email_concierge.py --send --confirm-send --wait-for-network --retry-seconds 60
```
`--send` never transmits without both prior approval and `--confirm-send`. With `--wait-for-network`, keep retrying locally and send only those approved drafts after connectivity returns. Missing SMTP settings are reported as structured input requirements.

---

## Workflow Examples

### Automatic inbox workflow
Reads every unread email, classifies it, checks calendar conflicts for meeting messages, and writes local reply drafts without sending mail.

```bash
python email_concierge.py --inbox
```

When disconnected, the same command uses the local mailbox cache and writes drafts to the queue. Re-run `--send` after connectivity is restored; inspect and approve drafts first.

### Non-interactive automation
Reports the exact missing configuration fields instead of prompting when IMAP configuration is unavailable.

```bash
python email_concierge.py --inbox --non-interactive --json
```

### Process or guide one email explicitly
```bash
python email_concierge.py --inbox --email-index 1 --user-text "Accept the meeting, suggest 2pm instead"
python email_concierge.py --inbox --interactive
```

### With voice input
```bash
python email_concierge.py --inbox --interactive --voice --voice-duration 20
```

### Save aggregate results
```bash
python email_concierge.py --inbox --output results.json --json
```

### Standalone tools
```bash
python email_concierge.py --check-cal today
python email_concierge.py --record 15
python email_concierge.py --transcribe voice_memo.wav
```

---

## Transcription (Optional)

Voice transcription uses distil-whisper through OpenVINO on supported platforms (Windows x64, Linux x64, macOS x64/arm64 CPU).

```bash
pip install openvino "optimum[openvino]" transformers librosa
```

Set `whisper_model_dir` in config to the downloaded distil-whisper model path.
Use `--device CPU` (default), `GPU`, `NPU`, or `AUTO` for inference device selection.

Alternatively, set `ollama_model_transcribe` (e.g. `whisper`) to use a locally installed Ollama for transcription only. Ollama is never used for text inference.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Model download fails or is slow | Downloads use `https://modelscope.cn` directly and resume interrupted files automatically. Check domestic network access to ModelScope and rerun setup. |
| First NPU generation takes minutes | Normal: one-time graph compilation; cached in `state/ov_cache`, later runs start in seconds |
| NPU/GPU init fails | Device chain auto-falls back NPU → GPU → CPU; pin `device: GPU` or `CPU` to skip a broken device |
| `openvino-genai` import error | Version must match the openvino line; rerun `pip install -r requirements-openvino.txt` |
| Ollama transcription missing | Install Ollama separately and `ollama pull whisper`, or use `whisper_model_dir` instead |
| IMAP auth failed | Use app password, not account password |
| `sounddevice` OSError (PortAudio) | See platform install steps above |
| No calendar events found | Export `.ics` files from Calendar app to configured `calendar_dir` |
| Windows venv not found | Use `venv\Scripts\python.exe` directly, not `python` |
| `icalendar` not found | `pip install icalendar` inside venv |
| Legacy `EmailConcierge-Ollama` startup task remains | Re-run setup (removes it automatically) or `schtasks /Delete /TN EmailConcierge-Ollama /F` |
