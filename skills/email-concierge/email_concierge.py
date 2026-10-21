#!/usr/bin/env python3
"""
Email Concierge — Local AI Email Assistant
Read, understand, and draft replies to emails. All data stays on your machine.

Tools:
  read_mailbox       — Fetch unread emails via IMAP
  classify_summarize  — Classify intent + generate one-line summary (OpenVINO GenAI, NPU > GPU > CPU)
  check_calendar      — Check iCal files for schedule conflicts
  start_voice_memo    — Record audio from microphone
  transcribe_memo     — Transcribe audio to text (distil-whisper / Ollama, optional)
  draft_reply         — Generate 3-style draft replies (OpenVINO GenAI)

Platforms: Windows, macOS, Linux
"""

import argparse
import contextlib
import copy
import email.message
import getpass
import io
import json
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import time
import wave
import smtplib
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PLATFORM = platform.system()  # "Windows", "Darwin", "Linux"

# ──────────────────────────────────────────────
# Platform helpers
# ──────────────────────────────────────────────

def _venv_python(venv_dir: Path) -> Path:
    """Return the Python executable inside a venv, cross-platform."""
    if PLATFORM == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_pip(venv_dir: Path) -> Path:
    if PLATFORM == "Windows":
        return venv_dir / "Scripts" / "pip.exe"
    return venv_dir / "bin" / "pip"


def _default_calendar_dir() -> Path:
    """Platform-appropriate default calendar directory."""
    if PLATFORM == "Darwin":
        return Path.home() / "Library" / "Calendars"
    if PLATFORM == "Windows":
        return Path.home() / "Documents" / "Calendars"
    return Path.home() / "Calendar"


def _portaudio_hint() -> str:
    if PLATFORM == "Darwin":
        return "  macOS: brew install portaudio"
    if PLATFORM == "Linux":
        # Detect distro
        try:
            import distro  # optional
            name = distro.id()
        except ImportError:
            name = ""
        if name in ("ubuntu", "debian", "linuxmint", "pop"):
            return "  Linux (Debian/Ubuntu): sudo apt install libportaudio2 portaudio19-dev"
        if name in ("fedora", "rhel", "centos"):
            return "  Linux (Fedora/RHEL): sudo dnf install portaudio-devel"
        return "  Linux: install libportaudio2 via your package manager"
    if PLATFORM == "Windows":
        return "  Windows: pip install sounddevice usually bundles PortAudio; if it fails, install pipwin then: pipwin install pyaudio"
    return "  Install PortAudio for your OS."


def _is_openvino_supported() -> bool:
    """OpenVINO supports Windows/Linux/macOS (x86-64 and arm64 with caveats)."""
    machine = platform.machine().lower()
    # arm64 macOS has limited OpenVINO support; CPU plugin works from 2024.x
    return True


def local_ai_environment_supported() -> bool:
    """Return whether this platform can run the bundled local AI stack."""
    return PLATFORM in {"Windows", "Darwin", "Linux"} and sys.version_info >= (3, 10)


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

CONFIG_PATH = SCRIPT_DIR / "email_concierge_config.json"

DEFAULT_CONFIG = {
    "imap_host": "",
    "imap_port": 993,
    "imap_user": "",
    "imap_password": "",
    "imap_folder": "INBOX",
    "llm_model_id": "OpenVINO/Qwen3-4B-int4-ov",
    "llm_model_dir": "",
    "ollama_model_transcribe": "",
    "calendar_dir": str(_default_calendar_dir()),
    "whisper_model_dir": "",
    "device": "AUTO",
    "max_emails": 20,
    "smtp_host": "",
    "smtp_port": 465,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_use_tls": True,
    "state_dir": str(SCRIPT_DIR / "state"),
}

ENV_CONFIG_MAP = {
    "imap_host": "EMAIL_CONCIERGE_IMAP_HOST",
    "imap_port": "EMAIL_CONCIERGE_IMAP_PORT",
    "imap_user": "EMAIL_CONCIERGE_IMAP_USER",
    "imap_password": "EMAIL_CONCIERGE_IMAP_PASSWORD",
    "imap_folder": "EMAIL_CONCIERGE_IMAP_FOLDER",
    "llm_model_id": "EMAIL_CONCIERGE_LLM_MODEL_ID",
    "llm_model_dir": "EMAIL_CONCIERGE_LLM_MODEL_DIR",
    "ollama_model_transcribe": "EMAIL_CONCIERGE_OLLAMA_MODEL_TRANSCRIBE",
    "calendar_dir": "EMAIL_CONCIERGE_CALENDAR_DIR",
    "whisper_model_dir": "EMAIL_CONCIERGE_WHISPER_MODEL_DIR",
    "device": "EMAIL_CONCIERGE_DEVICE",
    "max_emails": "EMAIL_CONCIERGE_MAX_EMAILS",
    "smtp_host": "EMAIL_CONCIERGE_SMTP_HOST",
    "smtp_port": "EMAIL_CONCIERGE_SMTP_PORT",
    "smtp_user": "EMAIL_CONCIERGE_SMTP_USER",
    "smtp_password": "EMAIL_CONCIERGE_SMTP_PASSWORD",
    "smtp_use_tls": "EMAIL_CONCIERGE_SMTP_USE_TLS",
    "state_dir": "EMAIL_CONCIERGE_STATE_DIR",
}

QUEUE_FILENAME = "draft_queue.json"
MAILBOX_CACHE_FILENAME = "mailbox_cache.json"


class MailboxError(RuntimeError):
    pass


class MailboxConfigurationError(MailboxError):
    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing IMAP configuration: {', '.join(missing_fields)}")


class MailboxConnectionError(MailboxError):
    pass


def apply_environment_overrides(cfg: dict) -> dict:
    for key, env_name in ENV_CONFIG_MAP.items():
        value = os.environ.get(env_name)
        if value is None or value == "":
            continue
        if key in {"imap_port", "max_emails", "smtp_port"}:
            try:
                cfg[key] = int(value)
            except ValueError:
                print(f"[Config] Ignoring invalid {env_name}: expected an integer.")
        elif key == "smtp_use_tls":
            cfg[key] = value.lower() not in {"0", "false", "no", "off"}
        else:
            cfg[key] = value
    return cfg


def missing_imap_fields(cfg: dict) -> List[str]:
    return [key for key in ("imap_host", "imap_user", "imap_password") if not cfg.get(key)]


def load_config(config_path: Optional[Path] = None) -> dict:
    path = config_path or CONFIG_PATH
    cfg = dict(DEFAULT_CONFIG)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    if not cfg.get("calendar_dir"):
        cfg["calendar_dir"] = str(_default_calendar_dir())
    if not cfg.get("state_dir"):
        cfg["state_dir"] = str(SCRIPT_DIR / "state")
    return apply_environment_overrides(cfg)


def diagnose_runtime(cfg: dict) -> dict:
    profile = platform_profile()
    environment_supported = local_ai_environment_supported()
    result = {
        "platform": PLATFORM,
        "architecture": profile["architecture"],
        "shell": profile["shell"],
        "package_manager": profile["package_manager"],
        "python_executable": profile["python_executable"],
        "venv_python": str(_venv_python(SCRIPT_DIR / "venv")),
        "recommended_install": profile["recommended_install"],
        "python": sys.version.split()[0],
        "intel_npu_detected": False,
        "openvino_installed": False,
        "openvino_genai_installed": False,
        "openvino_devices": [],
        "ollama_installed": bool(shutil.which("ollama")),
        "qoder_skills_dir": str(Path.home() / ".qoder" / "skills"),
        "qoder_installed": (Path.home() / ".qoder" / "skills").exists(),
        "missing_imap_fields": missing_imap_fields(cfg),
        "missing_smtp_fields": _smtp_missing_fields(cfg),
        "environment_supported": environment_supported,
    }
    if PLATFORM == "Windows":
        try:
            devices = subprocess.run(
                ["pnputil", "/enum-devices", "/connected"],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ).stdout
            result["intel_npu_detected"] = "Intel(R) AI Boost" in devices
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        from openvino import Core
        result["openvino_installed"] = True
        result["openvino_devices"] = list(Core().available_devices)
    except (ImportError, RuntimeError):
        pass
    try:
        import openvino_genai  # noqa: F401
        result["openvino_genai_installed"] = True
    except ImportError:
        pass
    result["llm_model_id"] = cfg.get("llm_model_id", "")
    result["llm_model_downloaded"] = llm_model_downloaded(cfg)
    result["llm_device"] = resolve_llm_devices(cfg)[0]
    result["intel_npu_detected"] = result["intel_npu_detected"] or "NPU" in result["openvino_devices"]
    result["aipc_ready"] = bool(result["openvino_installed"] and "NPU" in result["openvino_devices"])
    result["text_model_backend"] = "openvino-genai" if result["openvino_genai_installed"] else "offline-template"
    result["transcription_backend"] = preferred_model_backend(result)
    result["local_ai_installed"] = (
        result["openvino_installed"] and result["openvino_genai_installed"] and result["llm_model_downloaded"]
    )
    result["setup_required"] = environment_supported and not result["local_ai_installed"]
    # Installation state is handled by setup_auto.py.  A supported computer is
    # considered AI-ready by default so first-run automation can install the
    # missing local engines instead of prematurely degrading to templates.
    result["local_ai_ready"] = environment_supported
    return result


def platform_profile() -> dict:
    """Describe local execution tools without assuming a particular shell."""
    system = PLATFORM
    arch = platform.machine().lower() or "unknown"
    shell = "powershell" if system == "Windows" else ("zsh" if system == "Darwin" and shutil.which("zsh") else "bash")
    if system == "Windows":
        manager = "winget" if shutil.which("winget") else ("choco" if shutil.which("choco") else "pip")
        install = "Run setup_auto.py --project-dir . (installs openvino-genai and downloads the local LLM model)"
    elif system == "Darwin":
        manager = "brew" if shutil.which("brew") else "pip"
        install = "brew install portaudio (optional, for voice), then run setup_auto.py --project-dir ."
    elif system == "Linux":
        manager = next((m for m in ("apt-get", "dnf", "pacman", "zypper") if shutil.which(m)), "pip")
        install = {
            "apt-get": "sudo apt-get install -y libportaudio2 portaudio19-dev",
            "dnf": "sudo dnf install -y portaudio-devel",
            "pacman": "sudo pacman -S --noconfirm portaudio",
            "zypper": "sudo zypper install -y portaudio-devel",
        }.get(manager, "Install PortAudio with your distribution package manager")
    else:
        manager = "pip"
        install = "Install Python and PortAudio for this platform"
    return {
        "system": system,
        "architecture": arch,
        "shell": shell,
        "package_manager": manager,
        "python_executable": sys.executable,
        "recommended_install": install,
        "supports_openvino": system in {"Windows", "Linux", "Darwin"},
    }


def preferred_model_backend(diagnostics: dict) -> str:
    if diagnostics.get("aipc_ready"):
        return "openvino-npu"
    if diagnostics.get("openvino_installed") and "GPU" in diagnostics.get("openvino_devices", []):
        return "openvino-gpu"
    if diagnostics.get("openvino_installed"):
        return "openvino-cpu"
    if diagnostics.get("ollama_installed"):
        return "ollama"
    return "offline-template"


def save_config(cfg: dict, config_path: Optional[Path] = None):
    path = config_path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"[Config] Saved to {path}")


def _state_path(cfg: dict) -> Path:
    path = Path(cfg.get("state_dir") or SCRIPT_DIR / "state")
    path.mkdir(parents=True, exist_ok=True)
    return path / QUEUE_FILENAME


def _mailbox_cache_path(cfg: dict) -> Path:
    path = Path(cfg.get("state_dir") or SCRIPT_DIR / "state")
    path.mkdir(parents=True, exist_ok=True)
    return path / MAILBOX_CACHE_FILENAME


def load_mailbox_cache(cfg: dict) -> List[dict]:
    path = _mailbox_cache_path(cfg)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_mailbox_cache(cfg: dict, emails: List[dict]):
    with open(_mailbox_cache_path(cfg), "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)


def load_draft_queue(cfg: dict) -> List[dict]:
    path = _state_path(cfg)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError) as error:
        print(f"[queue] Failed to read {path}: {error}")
        return []


def save_draft_queue(cfg: dict, queue: List[dict]):
    path = _state_path(cfg)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _queue_drafts(cfg: dict, results: List[dict]) -> List[dict]:
    queue = load_draft_queue(cfg)
    existing = {item.get("id") for item in queue}
    for result in results:
        email_data = result["email"]
        source_id = str(email_data.get("id", ""))
        item_id = source_id or hashlib.sha256(
            f"{email_data.get('from', '')}|{email_data.get('subject', '')}".encode("utf-8")
        ).hexdigest()[:16]
        item = {
            "id": item_id,
            "email": copy.deepcopy(email_data),
            "drafts": copy.deepcopy(result.get("drafts", {})),
            "selected_style": next(iter(result.get("drafts", {})), "formal"),
            "calendar_conflicts": result.get("calendar_conflicts", ""),
            "user_input": result.get("user_input", ""),
            "approved": False,
            "sent": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        if item_id in existing:
            for old in queue:
                if old.get("id") == item_id and not old.get("sent"):
                    old.update(item)
                    break
        else:
            queue.append(item)
    save_draft_queue(cfg, queue)
    return queue


def network_available(host: str = "", port: int = 0) -> bool:
    """Return whether a network endpoint can be reached without sending data."""
    import socket
    target = host or "1.1.1.1"
    try:
        socket.create_connection((target, port or (443 if host else 53)), timeout=2).close()
        return True
    except OSError:
        return False


def _smtp_missing_fields(cfg: dict) -> List[str]:
    return [key for key in ("smtp_host", "smtp_user", "smtp_password") if not cfg.get(key)]


def interactive_smtp_setup(cfg: dict, config_path: Optional[Path] = None) -> bool:
    missing = _smtp_missing_fields(cfg)
    if not missing:
        return True
    if not sys.stdin.isatty():
        return False
    print("\n── SMTP Configuration ──")
    try:
        if "smtp_host" in missing:
            cfg["smtp_host"] = input("  SMTP host: ").strip()
        if "smtp_user" in missing:
            cfg["smtp_user"] = input("  SMTP email address: ").strip()
        if "smtp_password" in missing:
            cfg["smtp_password"] = getpass.getpass("  SMTP app password: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    if _smtp_missing_fields(cfg):
        return False
    save_config(cfg, config_path=config_path)
    return True


def approve_drafts(cfg: dict, ids: Optional[List[str]] = None) -> List[str]:
    queue = load_draft_queue(cfg)
    wanted = set(ids or [])
    approved = []
    for item in queue:
        if item.get("sent"):
            continue
        if not wanted or item.get("id") in wanted:
            item["approved"] = True
            approved.append(item["id"])
    save_draft_queue(cfg, queue)
    return approved


def send_pending_drafts(
    cfg: dict,
    ids: Optional[List[str]] = None,
    confirm: bool = False,
    wait_for_network: bool = False,
    retry_seconds: int = 60,
) -> dict:
    queue = load_draft_queue(cfg)
    pending = [item for item in queue if not item.get("sent") and (not ids or item.get("id") in set(ids))]
    if not pending:
        return {"status": "empty", "sent": []}
    missing = _smtp_missing_fields(cfg)
    if missing:
        return {"status": "needs_input", "missing_fields": missing}
    approved_pending = [item for item in pending if item.get("approved")]
    unapproved = [item.get("id") for item in pending if not item.get("approved")]
    if not confirm:
        return {"status": "needs_confirmation", "pending": unapproved or [item.get("id") for item in approved_pending]}
    if not approved_pending:
        return {"status": "needs_approval", "pending": unapproved}
    while not network_available(cfg["smtp_host"], int(cfg.get("smtp_port", 465))):
        if not wait_for_network:
            return {"status": "offline", "sent": [], "pending": [item.get("id") for item in approved_pending]}
        print(f"[send] Offline. Retrying in {retry_seconds}s; Ctrl+C keeps drafts queued.")
        try:
            time.sleep(max(1, retry_seconds))
        except KeyboardInterrupt:
            return {"status": "cancelled", "sent": [], "pending": [item.get("id") for item in approved_pending]}
    sent = []
    try:
        smtp_host = cfg["smtp_host"]
        smtp_port = int(cfg.get("smtp_port", 465))
        use_tls = bool(cfg.get("smtp_use_tls", True))
        client = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) if use_tls else smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        with client:
            if not use_tls:
                client.starttls()
            client.login(cfg["smtp_user"], cfg["smtp_password"])
            for item in approved_pending:
                msg = email.message.EmailMessage()
                original = item.get("email", {})
                msg["From"] = cfg["smtp_user"]
                msg["To"] = original.get("reply_to") or original.get("from", "")
                msg["Subject"] = "Re: " + original.get("subject", "")
                body = item.get("drafts", {}).get(item.get("selected_style", "formal"), "")
                msg.set_content(body)
                client.send_message(msg)
                item["sent"] = True
                item["sent_at"] = datetime.now().isoformat(timespec="seconds")
                sent.append(item["id"])
    except (OSError, smtplib.SMTPException) as error:
        return {"status": "error", "message": str(error), "sent": sent}
    save_draft_queue(cfg, queue)
    return {"status": "sent", "sent": sent}


def edit_draft(cfg: dict, item_id: str, text: str, style: str = "") -> dict:
    queue = load_draft_queue(cfg)
    for item in queue:
        if item.get("id") == item_id:
            selected = style or item.get("selected_style", "formal")
            item.setdefault("drafts", {})[selected] = text
            item["selected_style"] = selected
            item["approved"] = False
            save_draft_queue(cfg, queue)
            return {"status": "ok", "id": item_id, "selected_style": selected}
    return {"status": "not_found", "id": item_id}


def queue_status(cfg: dict) -> dict:
    queue = load_draft_queue(cfg)
    return {
        "status": "ok",
        "queue_file": str(_state_path(cfg)),
        "items": [
            {
                "id": item.get("id"),
                "subject": item.get("email", {}).get("subject", ""),
                "to": item.get("email", {}).get("reply_to") or item.get("email", {}).get("from", ""),
                "selected_style": item.get("selected_style", "formal"),
                "approved": bool(item.get("approved")),
                "sent": bool(item.get("sent")),
            }
            for item in queue
        ],
    }


# ──────────────────────────────────────────────
# Tool 1: read_mailbox
# ──────────────────────────────────────────────

def _send_imap_id(mail, name: str = "email-concierge", version: str = "1.0") -> None:
    """Send IMAP ID command; required by some providers (e.g. 163) before login."""
    import imaplib

    if "ID" not in imaplib.Commands:
        imaplib.Commands["ID"] = ("NONAUTH", "AUTH", "SELECTED")
    try:
        tag = mail._command("ID", f'("name" "{name}" "version" "{version}")')
        while True:
            line = mail.readline()
            if line.startswith(tag):
                break
    except Exception:
        pass


def read_mailbox(cfg: dict, max_emails: Optional[int] = None) -> List[dict]:
    """Fetch unread emails via IMAP, return list of dicts."""
    import email
    import imaplib
    from email.header import decode_header

    missing_fields = missing_imap_fields(cfg)
    if missing_fields:
        raise MailboxConfigurationError(missing_fields)

    host = cfg["imap_host"]
    port = cfg["imap_port"]
    user = cfg["imap_user"]
    pwd = cfg["imap_password"]
    folder = cfg.get("imap_folder", "INBOX")
    limit = max_emails if max_emails is not None else cfg.get("max_emails", 20)
    mail = None

    try:
        print(f"[read_mailbox] Connecting to {host}:{port} ...")
        mail = imaplib.IMAP4_SSL(host, port)
        _send_imap_id(mail)
        mail.login(user, pwd)
        status, _ = mail.select(folder, readonly=True)
        if status != "OK":
            raise MailboxConnectionError(f"Unable to select IMAP folder: {folder}")

        status, msg_ids = mail.search(None, "UNSEEN")
        if status != "OK":
            raise MailboxConnectionError("Unable to search the IMAP mailbox.")
        id_list = msg_ids[0].split()
        id_list = id_list[-limit:]
        id_list.reverse()

        emails = []
        for mid in id_list:
            status, data = mail.fetch(mid, "(RFC822)")
            if status != "OK" or not data or not data[0]:
                continue
            msg = email.message_from_bytes(data[0][1])

            def _decode_header(raw) -> str:
                if not raw:
                    return ""
                parts = decode_header(raw)
                out = ""
                for part, enc in parts:
                    if isinstance(part, bytes):
                        out += part.decode(enc or "utf-8", errors="replace")
                    else:
                        out += str(part)
                return out

            subject = _decode_header(msg["Subject"]) or "(no subject)"
            sender = _decode_header(msg["From"])

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset, errors="replace")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")

            emails.append({
                "id": mid.decode(),
                "from": sender.strip(),
                "reply_to": _decode_header(msg.get("Reply-To")),
                "subject": subject.strip(),
                "date": msg["Date"],
                "body": body.strip(),
            })
    except (imaplib.IMAP4.error, OSError, ssl.SSLError) as error:
        raise MailboxConnectionError(
            "Unable to connect or authenticate with IMAP. Check the host, account, and app password."
        ) from error
    finally:
        if mail is not None:
            try:
                mail.logout()
            except (imaplib.IMAP4.error, OSError):
                pass

    save_mailbox_cache(cfg, emails)
    print(f"[read_mailbox] Fetched {len(emails)} unread email(s)")
    return emails


# ──────────────────────────────────────────────
# Tool 2: classify_summarize
# ──────────────────────────────────────────────

def _keyword_classify(em: dict) -> None:
    """Deterministic offline classification used as the baseline and fallback."""
    subject = em.get("subject", "").lower()
    body = em.get("body", "").lower()
    haystack = subject + " " + body
    if any(word in haystack for word in ("meeting", "invite", "calendar", "会议", "日程")):
        em["category"] = "meeting"
    elif any(word in haystack for word in ("unsubscribe", "sale", "促销", "优惠")):
        em["category"] = "promotion"
    elif any(word in haystack for word in ("notification", "alert", "通知", "提醒")):
        em["category"] = "notification"
    else:
        em["category"] = "todo"
    em["summary"] = (em.get("body", "").replace("\n", " ").strip()[:200] or "No summary available offline.")


def classify_summarize(emails: List[dict], cfg: dict) -> List[dict]:
    """Classify all emails and summarize them in one batched LLM call."""
    for em in emails:
        _keyword_classify(em)
    if not emails:
        return emails

    entries = "\n".join(
        f"### Email {i}\nFrom: {em['from']}\nSubject: {em['subject']}\nBody:\n{em['body'][:1500]}\n"
        for i, em in enumerate(emails, 1)
    )
    prompt = (
        "Classify each email below into exactly ONE category: todo, meeting, notification, promotion.\n"
        "Also write a one-line summary in the email's language.\n\n"
        f"{entries}\n"
        "Respond with ONLY a JSON array, one object per email in order, no markdown:\n"
        '[{"id": 1, "category": "<category>", "summary": "<one-line summary>"}]'
    )
    result = _ov_generate(prompt, cfg, max_new_tokens=200 + 120 * len(emails))
    array_match = re.search(r"\[[\s\S]*\]", result)
    if array_match:
        try:
            for item in json.loads(array_match.group()):
                idx = int(item.get("id", 0)) - 1
                if not 0 <= idx < len(emails):
                    continue
                if item.get("category") in ("todo", "meeting", "notification", "promotion"):
                    emails[idx]["category"] = item["category"]
                if item.get("summary"):
                    emails[idx]["summary"] = str(item["summary"])
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            print(f"[classify] Batch parse failed ({error}); keeping keyword fallback.")
    elif result:
        print("[classify] LLM response was not a JSON array; keeping keyword fallback.")

    for em in emails:
        print(f"  [{em['category']}] {em['subject'][:60]} → {em['summary'][:80]}")
    return emails


# ──────────────────────────────────────────────
# Tool 3: check_calendar
# ──────────────────────────────────────────────

def check_calendar(cfg: dict, target_date: str = "", hours_range: int = 1) -> List[dict]:
    """Parse .ics files in calendar_dir, return events near target_date."""
    try:
        from icalendar import Calendar as iCal
    except ImportError:
        print("[check_calendar] icalendar not installed. Run: pip install icalendar")
        return []

    cal_dir = Path(cfg["calendar_dir"])
    if not cal_dir.exists():
        print(f"[check_calendar] Calendar dir not found: {cal_dir}")
        print(f"  Create the directory or update 'calendar_dir' in config.")
        return []

    if target_date and target_date.lower() != "today":
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                print(f"[check_calendar] Unrecognised date format: {target_date}")
                target_dt = datetime.now()
    else:
        target_dt = datetime.now()

    target_start = target_dt.replace(tzinfo=None)
    target_end = target_start + timedelta(hours=hours_range)

    events = []
    for ics_file in cal_dir.glob("**/*.ics"):
        try:
            with open(ics_file, "rb") as f:
                cal = iCal.from_ical(f.read())
            for component in cal.walk():
                if component.name != "VEVENT":
                    continue
                dtstart = component.get("dtstart")
                dtend = component.get("dtend")
                if not dtstart or not dtend:
                    continue
                start = dtstart.dt
                end = dtend.dt
                if hasattr(start, "astimezone"):
                    start = start.astimezone().replace(tzinfo=None)
                if hasattr(end, "astimezone"):
                    end = end.astimezone().replace(tzinfo=None)
                if isinstance(start, datetime) and isinstance(end, datetime):
                    if start < target_end and end > target_start:
                        events.append({
                            "summary": str(component.get("summary", "")),
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "location": str(component.get("location", "")),
                        })
        except Exception as e:
            print(f"[check_calendar] Failed to parse {ics_file.name}: {e}")

    events.sort(key=lambda e: e["start"])
    print(f"[check_calendar] Found {len(events)} event(s) around {target_start.isoformat()}")
    for ev in events:
        print(f"  {ev['start'][:16]} - {ev['end'][:16]}  {ev['summary']}")
    return events


# ──────────────────────────────────────────────
# Tool 4: start_voice_memo
# ──────────────────────────────────────────────

def start_voice_memo(output_path: str = "", duration: int = 30) -> str:
    """Record audio from the default microphone. Returns path to WAV file."""
    try:
        import sounddevice as sd
    except ImportError:
        print("[start_voice_memo] sounddevice not installed.")
        print(f"  Run: pip install sounddevice")
        print(_portaudio_hint())
        return ""
    except OSError as e:
        # PortAudio not found
        print(f"[start_voice_memo] PortAudio error: {e}")
        print(_portaudio_hint())
        return ""

    try:
        import numpy as np
    except ImportError:
        print("[start_voice_memo] numpy not installed. Run: pip install numpy")
        return ""

    if not output_path:
        output_path = str(SCRIPT_DIR / f"voice_memo_{int(time.time())}.wav")

    sample_rate = 16000
    channels = 1
    print(f"[start_voice_memo] Recording {duration}s ... Press Ctrl+C to stop early.")
    recording = []

    def callback(indata, frames, time_info, status):
        if status:
            pass  # ignore overflow warnings silently
        recording.append(indata.copy())

    try:
        with sd.InputStream(samplerate=sample_rate, channels=channels,
                            dtype="float32", callback=callback):
            start = time.time()
            while time.time() - start < duration:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[start_voice_memo] Recording stopped by user.")
    except Exception as e:
        print(f"[start_voice_memo] Recording error: {e}")
        return ""

    if not recording:
        print("[start_voice_memo] No audio captured.")
        return ""

    audio_data = np.concatenate(recording, axis=0)

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

    print(f"[start_voice_memo] Saved to {output_path} ({len(audio_data)/sample_rate:.1f}s)")
    return output_path


# ──────────────────────────────────────────────
# Tool 5: transcribe_memo
# ──────────────────────────────────────────────

def transcribe_memo(audio_path: str, cfg: dict) -> str:
    """Transcribe audio file to text.
    Priority: distil-whisper (OpenVINO) → Ollama whisper → transcribe-translate skill.
    """
    if not os.path.exists(audio_path):
        print(f"[transcribe_memo] File not found: {audio_path}")
        return ""

    whisper_dir = cfg.get("whisper_model_dir", "")
    if whisper_dir and Path(whisper_dir).exists():
        result = _transcribe_whisper(audio_path, whisper_dir, cfg)
        if result:
            return result

    model = cfg.get("ollama_model_transcribe") or ""
    if model:
        return _transcribe_ollama(audio_path, model, cfg)

    return _transcribe_via_skill(audio_path)


def _transcribe_whisper(audio_path: str, model_dir: str, cfg: dict) -> str:
    """Transcribe using distil-whisper OpenVINO model (Windows/Linux/macOS x86-64)."""
    try:
        from optimum.intel.openvino import OVModelForSpeechSeq2Seq
        from transformers import AutoProcessor
        import librosa
        import numpy as np
    except ImportError as e:
        print(f"[transcribe_memo] Missing OpenVINO dependency: {e}")
        print("  Run: pip install openvino optimum[openvino] transformers librosa")
        return ""

    print(f"[transcribe_memo] Loading whisper model from {model_dir} ...")
    device = cfg.get("device", "CPU").upper()
    try:
        model = OVModelForSpeechSeq2Seq.from_pretrained(model_dir, device=device)
        processor = AutoProcessor.from_pretrained(model_dir)
    except Exception as e:
        print(f"[transcribe_memo] Failed to load model: {e}")
        return ""

    audio, _ = librosa.load(audio_path, sr=16000)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")

    print("[transcribe_memo] Transcribing ...")
    result = model.generate(**inputs, max_new_tokens=448, num_beams=1)
    text = processor.batch_decode(result, skip_special_tokens=True)[0].strip()
    print(f"[transcribe_memo] → {text[:100]}")
    return text


def _transcribe_ollama(audio_path: str, model: str, cfg: dict) -> str:
    """Transcribe using an Ollama audio model (optional backend)."""
    if not shutil.which("ollama"):
        print("[transcribe_memo] Ollama not found.")
        return ""
    try:
        listed = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if PLATFORM == "Windows" else 0,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        listed = ""
    if model not in listed:
        print(f"[transcribe_memo] Ollama model '{model}' not pulled. Run: ollama pull {model}")
        return ""
    cmd = ["ollama", "run", model, f"Transcribe this audio file: {audio_path}"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            # Windows: hide console window
            creationflags=subprocess.CREATE_NO_WINDOW if PLATFORM == "Windows" else 0,
        )
        text = result.stdout.strip()
        print(f"[transcribe_memo] (ollama) → {text[:100]}")
        return text
    except FileNotFoundError:
        print("[transcribe_memo] Ollama not found.")
        return ""
    except subprocess.TimeoutExpired:
        print("[transcribe_memo] Ollama timeout.")
        return ""


def _transcribe_via_skill(audio_path: str) -> str:
    """Delegate to the transcribe-translate skill if installed alongside."""
    tt_dir = SCRIPT_DIR.parent / "transcribe-translate"
    tt_script = tt_dir / "transcribe_translate.py"
    if not tt_script.exists():
        print("[transcribe_memo] No transcription engine available.")
        print("  Configure 'whisper_model_dir' or 'ollama_model_transcribe' in setup.")
        return ""

    print("[transcribe_memo] Delegating to transcribe-translate skill ...")
    venv_python = _venv_python(tt_dir / "venv")
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    try:
        result = subprocess.run(
            [str(venv_python), str(tt_script), "--audio", audio_path, "--no-translate"],
            capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if PLATFORM == "Windows" else 0,
        )
        for line in result.stdout.splitlines():
            if "English Transcription:" in line:
                return line.split(":", 1)[1].strip()
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        return lines[-1] if lines else ""
    except Exception as e:
        print(f"[transcribe_memo] transcribe-translate error: {e}")
        return ""


# ──────────────────────────────────────────────
# Tool 6: draft_reply
# ──────────────────────────────────────────────

REPLY_STYLES = {
    "formal": "Write a formal, professional email reply.",
    "friendly": "Write a warm, friendly email reply.",
    "concise": "Write a brief, concise email reply (2-3 sentences max).",
}


def draft_reply(
    original_email: dict,
    cfg: dict,
    user_input: str = "",
    calendar_context: str = "",
    styles: List[str] = None,
) -> Dict[str, str]:
    """Generate draft replies in all requested styles with a single LLM call."""
    styles = [s for s in (styles or ["formal", "friendly", "concise"]) if s in REPLY_STYLES] or ["formal"]
    drafts = {}

    style_specs = "\n".join(f'- "{style}": {REPLY_STYLES[style]}' for style in styles)
    prompt = (
        "You are an email assistant. Generate a reply to the following email.\n\n"
        f"Original email from: {original_email.get('from', '')}\n"
        f"Subject: {original_email.get('subject', '')}\n"
        f"Body:\n{original_email.get('body', '')[:3000]}\n"
    )
    if user_input:
        prompt += f"\nUser's additional input: {user_input}\n"
    if calendar_context:
        prompt += f"\nCalendar context: {calendar_context}\n"
    prompt += (
        f"\nWrite one reply for each requested style:\n{style_specs}\n\n"
        "Respond with ONLY a JSON object (no markdown) mapping each style name to its reply body, "
        "with newlines inside strings escaped as \\n:\n"
        "{" + ", ".join(f'"{style}": "<reply body>"' for style in styles) + "}"
    )

    result = _ov_generate(prompt, cfg, max_new_tokens=800)
    parsed = {}
    object_match = re.search(r"\{[\s\S]*\}", result)
    if object_match:
        try:
            candidate = json.loads(object_match.group())
            if isinstance(candidate, dict):
                parsed = candidate
        except json.JSONDecodeError:
            print("[draft] JSON parse failed; using offline template for missing styles.")
    for style in styles:
        text = str(parsed.get(style, "")).strip()
        drafts[style] = text or _offline_draft(original_email, user_input, style, calendar_context)
        print(f"\n── Draft ({style}) ──\n{drafts[style]}\n")

    return drafts


def _offline_draft(original_email: dict, user_input: str, style: str, calendar_context: str) -> str:
    """Create an editable local draft when no model/network is available."""
    greeting = "Hello," if style == "formal" else "Hi," if style == "friendly" else "Hi,"
    subject = original_email.get("subject", "")
    lines = [greeting, "", f"Thanks for your email about {subject or 'this'}. "]
    if user_input:
        lines.append(f"I will {user_input.rstrip('.')}.")
    else:
        lines.append("I have received your message and will follow up shortly.")
    if calendar_context:
        lines.append(f"I checked my calendar; current conflicts are: {calendar_context}.")
    lines.extend(["", "Best regards,"])
    return "\n".join(lines)


# ──────────────────────────────────────────────
# OpenVINO GenAI LLM helper (device priority: NPU > GPU > CPU)
# ──────────────────────────────────────────────

_LLM_PIPELINES: Dict[str, "object"] = {}


def llm_model_path(cfg: dict) -> Path:
    """Local directory of the OpenVINO LLM model."""
    explicit = cfg.get("llm_model_dir") or ""
    if explicit:
        return Path(explicit)
    state_dir = Path(cfg.get("state_dir") or SCRIPT_DIR / "state")
    return state_dir / "models" / str(cfg.get("llm_model_id", "")).split("/")[-1]


def llm_model_downloaded(cfg: dict) -> bool:
    path = llm_model_path(cfg)
    xmls = [xml for xml in path.glob("*.xml") if not xml.name.startswith(".")]
    # An OpenVINO export ships .xml+.bin pairs; weights exist only when every
    # graph file has its binary counterpart (a lone detokenizer.bin is not a model).
    return bool(xmls) and all(xml.with_suffix(".bin").exists() for xml in xmls)


def resolve_llm_devices(cfg: dict) -> List[str]:
    """Ordered devices to try for LLM inference: explicit device, else NPU > GPU > CPU."""
    requested = str(cfg.get("device", "AUTO")).upper()
    if requested in {"NPU", "GPU", "CPU"}:
        return [requested]
    if requested != "AUTO":
        print(f"[LLM] Unknown device '{cfg.get('device')}'; falling back to AUTO priority.")
    try:
        from openvino import Core
        available = set(Core().available_devices)
    except (ImportError, RuntimeError):
        return ["CPU"]
    return [d for d in ("NPU", "GPU", "CPU") if d in available] or ["CPU"]


MODELSCOPE_URL = "https://modelscope.cn/models/{repo}/resolve/master/{file}"
LLM_MODEL_FILES = (
    "openvino_model.xml", "openvino_model.bin", "openvino_config.json",
    "openvino_detokenizer.xml", "openvino_detokenizer.bin",
    "openvino_tokenizer.xml", "openvino_tokenizer.bin",
    "config.json", "generation_config.json", "tokenizer_config.json",
    "tokenizer.json", "vocab.json", "merges.txt", "chat_template.jinja",
    "special_tokens_map.json", "added_tokens.json",
)


def _remote_file_size(url: str) -> int:
    """Total size of a remote file via a 1-byte range request, or 0 if unknown."""
    import urllib.request
    request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            content_range = resp.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.rsplit("/", 1)[-1])
            return int(resp.headers.get("Content-Length", "0"))
    except Exception:
        return 0


def _download_file_resumable(url: str, target: Path, expected_size: int) -> bool:
    """Download url to target with byte-range resume; True when the full size is on disk."""
    import urllib.request
    for _ in range(30):
        start = target.stat().st_size if target.exists() else 0
        if expected_size and start == expected_size:
            return True
        if expected_size and start > expected_size:
            target.unlink(missing_ok=True)
            start = 0
        headers = {"Range": f"bytes={start}-"} if start else {}
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as resp, \
                    open(target, "ab" if start else "wb") as f:
                if start and resp.status != 206:
                    # Server ignored the range; restart from scratch.
                    f.close()
                    target.unlink(missing_ok=True)
                    continue
                shutil.copyfileobj(resp, f)
        except Exception:
            continue  # connection dropped; resume from what we have
        if not expected_size or target.stat().st_size == expected_size:
            return True
    return False


def _download_from_modelscope(model_id: str, dest: Path) -> bool:
    """Fetch the model bundle directly from ModelScope (fast when HF endpoints are throttled)."""
    print(f"[LLM] Trying ModelScope mirror for {model_id} ...")
    for name in LLM_MODEL_FILES:
        url = MODELSCOPE_URL.format(repo=model_id, file=name)
        target = dest / name
        expected = _remote_file_size(url)
        if not expected:
            print(f"[LLM] ModelScope does not serve {name}; aborting fallback.")
            return False
        if target.exists() and target.stat().st_size == expected:
            continue
        print(f"[LLM] Downloading {name} ({expected / (1024**2):.1f} MiB) from ModelScope ...")
        if not _download_file_resumable(url, target, expected):
            print(f"[LLM] ModelScope download of {name} failed.")
            return False
    return True


def download_llm_model(cfg: dict) -> Optional[str]:
    """Download the OpenVINO LLM model directly from ModelScope.

    Returns the model directory, or None if ModelScope cannot provide a complete export.
    """
    model_id = cfg.get("llm_model_id", "")
    if not model_id:
        print("[LLM] No llm_model_id configured.")
        return None

    dest = llm_model_path(cfg)
    dest.mkdir(parents=True, exist_ok=True)
    if not llm_model_downloaded(cfg) and not _download_from_modelscope(model_id, dest):
        return None
    if not llm_model_downloaded(cfg):
        return None
    print(f"[LLM] Model saved to {dest}")
    return str(dest)


def _get_llm_pipeline(cfg: dict):
    """Create (or reuse) the OpenVINO GenAI pipeline, trying devices in priority order."""
    model_dir = llm_model_path(cfg)
    key = str(model_dir)
    if key in _LLM_PIPELINES:
        return _LLM_PIPELINES[key]

    if not llm_model_downloaded(cfg):
        if download_llm_model(cfg) is None or not llm_model_downloaded(cfg):
            return None

    import openvino_genai as ov

    cache_root = Path(cfg.get("state_dir") or SCRIPT_DIR / "state") / "ov_cache"
    for device in resolve_llm_devices(cfg):
        try:
            cache_dir = cache_root / device
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[LLM] Loading model on {device} (first compile can take minutes; cached afterwards) ...")
            pipe = ov.LLMPipeline(str(model_dir), device, {"CACHE_DIR": str(cache_dir)})
            _LLM_PIPELINES[key] = pipe
            return pipe
        except Exception as error:
            print(f"[LLM] Failed to initialize on {device}: {error}")
    return None


def _ov_generate(prompt: str, cfg: dict, max_new_tokens: int = 400, temperature: float = 0.7) -> str:
    """Generate text with the local OpenVINO model. Returns '' on any failure."""
    try:
        import openvino_genai as ov
    except ImportError:
        print("[LLM] openvino-genai not installed. Run: pip install openvino-genai")
        return ""

    pipe = _get_llm_pipeline(cfg)
    if pipe is None:
        return ""

    if "qwen3" in str(cfg.get("llm_model_id", "")).lower():
        prompt = f"{prompt} /no_think"

    config = ov.GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=temperature > 0,
    )
    try:
        # Fresh chat context per call so separate emails don't bleed into each other.
        pipe.start_chat()
        try:
            text = pipe.generate(prompt, config)
        finally:
            pipe.finish_chat()
    except Exception as error:
        print(f"[LLM] Generation failed: {error}")
        return ""
    # Defensive: strip reasoning blocks if the /no_think soft switch was ignored.
    return re.sub(r"<(?:think)>[\s\S]*?(?:</think)>\s*", "", text, flags=re.DOTALL).strip()


# ──────────────────────────────────────────────
# Full pipeline
# ──────────────────────────────────────────────

def _select_emails(emails: List[dict], args) -> List[dict]:
    if args.email_index is not None:
        if not 1 <= args.email_index <= len(emails):
            raise ValueError(f"Email index must be between 1 and {len(emails)}.")
        return [emails[args.email_index - 1]]

    if not args.interactive:
        return emails
    if not sys.stdin.isatty():
        raise ValueError("Interactive selection requires a terminal. Use --email-index instead.")

    try:
        index = int(input("\nWhich email to process? (number): "))
    except (ValueError, EOFError):
        raise ValueError("No email was selected.") from None
    if not 1 <= index <= len(emails):
        raise ValueError(f"Email index must be between 1 and {len(emails)}.")
    return [emails[index - 1]]


def _print_missing_configuration(missing_fields: List[str], as_json: bool):
    result = {"status": "needs_input", "missing_fields": missing_fields}
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
        return
    fields = ", ".join(missing_fields)
    print(f"IMAP configuration is required: {fields}.")
    print("Set the matching EMAIL_CONCIERGE_* variables or run --setup in a terminal.")


def _run_pipeline(cfg: dict, args) -> dict:
    print("\n" + "=" * 60)
    print("  Email Concierge — Local AI Email Assistant")
    print(f"  Platform: {PLATFORM} / Python {sys.version.split()[0]}")
    print("=" * 60)

    missing_fields = missing_imap_fields(cfg)
    if missing_fields:
        if sys.stdin.isatty() and not args.non_interactive:
            print("\n▶ IMAP setup is required ...")
            if not interactive_setup(cfg):
                return {"status": "needs_input", "missing_fields": missing_imap_fields(cfg)}
        else:
            if not args.json:
                _print_missing_configuration(missing_fields, as_json=False)
            return {"status": "needs_input", "missing_fields": missing_fields}

    print("\n▶ STEP 1: Reading mailbox ...")
    try:
        emails = read_mailbox(cfg, max_emails=args.max_emails)
    except MailboxConfigurationError as error:
        if not args.json:
            _print_missing_configuration(error.missing_fields, as_json=False)
        return {"status": "needs_input", "missing_fields": error.missing_fields}
    except MailboxConnectionError as error:
        emails = load_mailbox_cache(cfg)
        if not emails:
            if not args.json:
                print(f"[read_mailbox] {error}")
            return {"status": "offline", "message": str(error), "emails": []}
        if not args.json:
            print(f"[read_mailbox] Offline; using {len(emails)} cached email(s).")

    if not emails:
        if not args.json:
            print("No unread emails found. Done.")
        return {"status": "empty", "emails": []}

    print("\n▶ STEP 2: Classifying & summarizing ...")
    emails = classify_summarize(emails, cfg)

    print("\n" + "─" * 60)
    print("  Email Summary")
    print("─" * 60)
    for i, em in enumerate(emails, 1):
        print(f"  {i}. [{em.get('category', '?').upper()}] {em['subject'][:50]}")
        print(f"     From: {em['from'][:40]}  |  {em.get('summary', '')[:60]}")

    try:
        selected_emails = _select_emails(emails, args)
    except ValueError as error:
        if not args.json:
            print(f"Cancelled: {error}")
        return {"status": "cancelled", "message": str(error)}

    user_input = args.user_text or ""
    if args.voice:
        print("\n▶ STEP 3: Recording voice memo ...")
        audio_path = start_voice_memo(duration=args.voice_duration or 30)
        if audio_path:
            print("\n▶ STEP 4: Transcribing voice memo ...")
            user_input = transcribe_memo(audio_path, cfg)

    styles = [style.strip() for style in args.styles.split(",") if style.strip()]
    results = []
    for selected in selected_emails:
        print(f"\n▶ Processing: [{selected.get('category', '')}] {selected['subject']}")
        calendar_ctx = ""
        if selected.get("category") == "meeting":
            print("\n▶ Checking calendar ...")
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', selected["body"])
            date_hint = date_match.group(1) if date_match else ""
            events = check_calendar(cfg, target_date=date_hint, hours_range=2)
            if events:
                calendar_ctx = "; ".join(
                    f"{event['start'][:16]} - {event['end'][:16]}: {event['summary']}"
                    for event in events
                )

        print("\n▶ Drafting reply ...")
        drafts = draft_reply(
            original_email=selected,
            cfg=cfg,
            user_input=user_input,
            calendar_context=calendar_ctx,
            styles=styles,
        )
        results.append({
            "email": selected,
            "calendar_conflicts": calendar_ctx,
            "user_input": user_input,
            "drafts": drafts,
        })

    output = {"status": "ok", "emails": results}
    _queue_drafts(cfg, results)
    output["queue_file"] = str(_state_path(cfg))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")

    print("\nDone.")
    return output


def run_pipeline(cfg: dict, args) -> dict:
    configure_console()
    if args.json:
        with contextlib.redirect_stdout(io.StringIO()):
            output = _run_pipeline(cfg, args)
        print(json.dumps(output, ensure_ascii=False))
        return output
    return _run_pipeline(cfg, args)


# ──────────────────────────────────────────────
# Setup & Config
# ──────────────────────────────────────────────

def interactive_setup(cfg: dict, config_path: Optional[Path] = None) -> bool:
    configure_console()
    missing_fields = missing_imap_fields(cfg)
    if not missing_fields:
        print("IMAP configuration is already complete.")
        return True
    if not sys.stdin.isatty():
        _print_missing_configuration(missing_fields, as_json=False)
        return False

    print("\n── IMAP Configuration ──")
    print("  Use an app password, not your account password.")
    print("  Gmail: Security → App passwords")
    print("  Outlook: Security → Advanced → App passwords")
    print("  Yahoo: Account → Security → App passwords\n")

    try:
        if "imap_host" in missing_fields:
            cfg["imap_host"] = input("  IMAP host: ").strip()
        if "imap_user" in missing_fields:
            cfg["imap_user"] = input("  Email address: ").strip()
        if "imap_password" in missing_fields:
            cfg["imap_password"] = getpass.getpass("  App password: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.")
        return False

    remaining_fields = missing_imap_fields(cfg)
    if remaining_fields:
        print(f"Setup needs: {', '.join(remaining_fields)}.")
        return False

    if config_path is None:
        save_config(cfg)
    else:
        save_config(cfg, config_path=config_path)
    print("\nSetup complete. Continuing automatically.")
    return True


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def configure_console():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except OSError:
            pass


def main():
    configure_console()
    parser = argparse.ArgumentParser(
        description="Email Concierge — Local AI Email Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python email_concierge.py --setup\n"
            "  python email_concierge.py --inbox\n"
            "  python email_concierge.py --inbox --interactive\n"
            "  python email_concierge.py --inbox --email-index 1 --user-text \"Accept\"\n"
            "  python email_concierge.py --inbox --json\n"
            "  python email_concierge.py --check-cal 2026-09-01\n"
            "  python email_concierge.py --record 20\n"
            "  python email_concierge.py --transcribe voice_memo.wav\n"
        ),
    )

    parser.add_argument("--setup", action="store_true", help="Configure missing IMAP settings")
    parser.add_argument("--diagnose", action="store_true", help="Check AI PC, local model, Qoder, and mail readiness")
    parser.add_argument("--inbox", action="store_true",
                        help="Process unread emails through summary, calendar checks, and drafts")
    parser.add_argument("--check-cal", nargs="?", const="today", default=None,
                        metavar="DATE", help="Check calendar (YYYY-MM-DD or 'today')")
    parser.add_argument("--record", type=int, nargs="?", const=30, default=None,
                        metavar="SECONDS", help="Record voice memo (default 30s)")
    parser.add_argument("--transcribe", type=str, metavar="FILE", help="Transcribe an audio file")
    parser.add_argument("--queue", action="store_true", help="Show local draft queue")
    parser.add_argument("--approve", type=str, nargs="*", metavar="ID", help="Approve queued drafts (all if no IDs)")
    parser.add_argument("--edit", nargs=2, metavar=("ID", "TEXT"), help="Edit selected queued draft text")
    parser.add_argument("--style", type=str, default="", help="Draft style for --edit")
    parser.add_argument("--send", action="store_true", help="Send approved queued drafts when online")
    parser.add_argument("--confirm-send", action="store_true", help="Confirm sending approved drafts")
    parser.add_argument("--wait-for-network", action="store_true", help="Wait and send approved drafts when connectivity returns")
    parser.add_argument("--retry-seconds", type=int, default=60, help="Network retry interval (default: 60)")
    parser.add_argument("--draft", action="store_true", help="Deprecated: --inbox drafts automatically")

    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Select one email interactively instead of processing all")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Never prompt; report any required IMAP fields")
    parser.add_argument("--email-index", type=int, metavar="N",
                        help="Process Nth email only (1-based)")
    parser.add_argument("--voice", action="store_true", help="Record voice input before drafting")
    parser.add_argument("--voice-duration", type=int, default=30,
                        metavar="SECONDS", help="Voice memo duration (default 30)")
    parser.add_argument("--user-text", type=str, metavar="TEXT",
                        help="Text input added to every generated draft")
    parser.add_argument("--styles", type=str, default="formal,friendly,concise",
                        help="Comma-separated reply styles (default: formal,friendly,concise)")
    parser.add_argument("--max-emails", type=int, default=None,
                        help="Max emails to fetch (defaults to configured value)")
    parser.add_argument("--output", "-o", type=str, metavar="FILE",
                        help="Save aggregate results to JSON file")
    parser.add_argument("--json", action="store_true", help="Print aggregate results as JSON")
    parser.add_argument("--device", type=str, default=None,
                        help="OpenVINO inference device: CPU / GPU / NPU / AUTO")
    parser.add_argument("--config", type=str, metavar="FILE",
                        help="Path to config JSON; environment variables still take precedence")

    args = parser.parse_args()
    config_path = Path(args.config) if args.config else None
    cfg = load_config(config_path)
    if args.device is not None:
        cfg["device"] = args.device

    if args.diagnose:
        print(json.dumps(diagnose_runtime(cfg), ensure_ascii=False, indent=None if args.json else 2))
    elif args.setup:
        interactive_setup(cfg, config_path=config_path)
    elif args.queue:
        result = queue_status(cfg)
        print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
    elif args.approve is not None:
        approved = approve_drafts(cfg, args.approve or None)
        result = {"status": "approved", "approved": approved}
        print(json.dumps(result, ensure_ascii=False))
    elif args.edit:
        result = edit_draft(cfg, args.edit[0], args.edit[1], args.style)
        print(json.dumps(result, ensure_ascii=False))
    elif args.send:
        if _smtp_missing_fields(cfg) and not args.non_interactive:
            interactive_smtp_setup(cfg, config_path=config_path)
        result = send_pending_drafts(
            cfg,
            confirm=args.confirm_send,
            wait_for_network=args.wait_for_network,
            retry_seconds=args.retry_seconds,
        )
        print(json.dumps(result, ensure_ascii=False))
    elif args.inbox or args.interactive:
        run_pipeline(cfg, args)
    elif args.check_cal is not None:
        date_str = "" if args.check_cal == "today" else args.check_cal
        check_calendar(cfg, target_date=date_str)
    elif args.record is not None:
        start_voice_memo(duration=args.record)
    elif args.transcribe:
        text = transcribe_memo(args.transcribe, cfg)
        if text:
            print(f"\nTranscription:\n{text}")
    elif args.draft:
        print("Use --inbox to process unread emails and generate drafts automatically.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
