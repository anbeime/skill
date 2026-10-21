#!/usr/bin/env python3
"""Cross-platform bootstrapper for Email Concierge.

Designed for unattended use by Qoder and other agents. It creates a local
venv, installs Python dependencies (including openvino-genai), downloads the
configured OpenVINO LLM model, and reports structured diagnostics via --json.
"""
from __future__ import annotations
import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_MODE = False

MIN_RAM_BYTES = 6 * 1024 ** 3
MIN_FREE_DISK_BYTES = 5 * 1024 ** 3
SUPPORTED_ARCHS = {"x86_64", "amd64", "arm64", "aarch64"}
LEGACY_OLLAMA_TASK = "EmailConcierge-Ollama"


def _total_memory_bytes() -> int:
    """Return total physical RAM in bytes, or 0 if it cannot be determined."""
    system = platform.system()
    if system == "Windows":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return 0
        return stat.ullTotalPhys

    if system == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, check=False, timeout=5,
            )
            return int(result.stdout.strip())
        except (OSError, ValueError, subprocess.SubprocessError):
            return 0

    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return 0


def _free_disk_bytes(path: Path) -> int:
    """Return free disk space for the volume containing path, or 0 on error."""
    if platform.system() == "Windows":
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(str(path), None, None, ctypes.byref(free_bytes)):
            return free_bytes.value
        return 0
    try:
        import os
        st = os.statvfs(path)
        return st.f_bavail * st.f_frsize
    except OSError:
        return 0


def hardware_meets_requirements(project_dir: Path) -> dict:
    """Check whether the machine meets the minimum requirements for local AI."""
    result = {
        "supported": True,
        "reasons": [],
        "ram_bytes": 0,
        "min_ram_bytes": MIN_RAM_BYTES,
        "free_disk_bytes": 0,
        "min_free_disk_bytes": MIN_FREE_DISK_BYTES,
    }
    arch = platform.machine().lower()
    if arch not in SUPPORTED_ARCHS:
        result["supported"] = False
        result["reasons"].append(f"architecture '{arch}' is not supported")
    total_ram = _total_memory_bytes()
    result["ram_bytes"] = total_ram
    if total_ram < MIN_RAM_BYTES:
        result["supported"] = False
        result["reasons"].append(
            f"insufficient RAM ({total_ram / (1024**3):.1f} GiB < {MIN_RAM_BYTES / (1024**3):.1f} GiB)"
        )
    free_disk = _free_disk_bytes(project_dir)
    result["free_disk_bytes"] = free_disk
    if free_disk < MIN_FREE_DISK_BYTES:
        result["supported"] = False
        result["reasons"].append(
            f"insufficient free disk space ({free_disk / (1024**3):.1f} GiB < {MIN_FREE_DISK_BYTES / (1024**3):.1f} GiB)"
        )
    return result


def remove_legacy_ollama_task() -> None:
    """Delete the Ollama logon task registered by older versions of this skill."""
    if platform.system() != "Windows":
        return
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", LEGACY_OLLAMA_TASK, "/F"],
            capture_output=True, text=True, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except OSError:
        pass


def _write_setup_marker(project: Path, report: dict) -> None:
    """Write a marker file so future installs know setup already completed."""
    marker = project / "state" / ".setup_completed.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "completed_at": datetime.now().isoformat(),
        "version": "2.0.0",
        "llm_model_id": report["llm_model"].get("model_id", ""),
        "llm_model_downloaded": report["llm_model"].get("downloaded", False),
        "hardware_supported": report["hardware"].get("supported", True),
        "skipped_reason": report["llm_model"].get("error", "") if report["llm_model"].get("skipped") else "",
    }
    marker.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run(command: list[str], cwd: Path = ROOT, check: bool = True, timeout: int | None = None):
    """Run a command and return its CompletedProcess."""
    if not JSON_MODE:
        print("[setup]", " ".join(command))
    kwargs = {"cwd": cwd, "check": check}
    if timeout is not None:
        kwargs["timeout"] = timeout
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if JSON_MODE:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return subprocess.run(command, **kwargs)


def package_manager() -> str:
    system = platform.system()
    if system == "Windows":
        return "winget" if shutil.which("winget") else ("choco" if shutil.which("choco") else "")
    if system == "Darwin":
        return "brew" if shutil.which("brew") else ""
    if system == "Linux":
        return next((name for name in ("apt-get", "dnf", "pacman", "zypper") if shutil.which(name)), "")
    return ""


def local_ai_environment_supported() -> bool:
    return platform.system() in {"Windows", "Darwin", "Linux"} and sys.version_info >= (3, 10)


def install_portaudio(manager: str, yes: bool = False) -> dict:
    """Install PortAudio via the platform package manager when possible."""
    result = {"installed": False, "manager": manager, "error": ""}
    commands = {
        "brew": ["brew", "install", "portaudio"],
        "apt-get": ["sudo", "apt-get", "install", "-y", "libportaudio2", "portaudio19-dev"],
        "dnf": ["sudo", "dnf", "install", "-y", "portaudio-devel"],
        "pacman": ["sudo", "pacman", "-S", "--noconfirm", "portaudio"],
        "zypper": ["sudo", "zypper", "install", "-y", "portaudio-devel"],
    }
    command = commands.get(manager)
    if not command:
        result["error"] = "no supported package manager found"
        return result
    try:
        run(command, check=False)
        result["installed"] = True
    except OSError as error:
        result["error"] = str(error)
    return result


def _venv_python(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _llm_model_status(venv: Path, project: Path) -> dict:
    """Query the configured LLM model state through the project's own code."""
    script = (
        "import sys, json; sys.path.insert(0, sys.argv[1]); "
        "from email_concierge import load_config, llm_model_downloaded, llm_model_path; "
        "cfg = load_config(); "
        "print(json.dumps({'model_id': cfg.get('llm_model_id', ''), "
        "'downloaded': llm_model_downloaded(cfg), 'path': str(llm_model_path(cfg))}))"
    )
    try:
        completed = subprocess.run(
            [str(venv), "-c", script, str(project)],
            capture_output=True, text=True, check=False, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        line = next(l for l in completed.stdout.splitlines() if l.startswith("{"))
        data = json.loads(line)
        return {
            "model_id": data.get("model_id", ""),
            "downloaded": bool(data.get("downloaded")),
            "path": data.get("path", ""),
            "error": "",
        }
    except (OSError, subprocess.SubprocessError, StopIteration, json.JSONDecodeError) as error:
        return {"model_id": "", "downloaded": False, "path": "", "error": f"could not query model status: {error}"}


def download_llm_model(venv: Path, project: Path) -> dict:
    """Download the configured OpenVINO LLM model using the venv interpreter."""
    status = _llm_model_status(venv, project)
    result = {
        "model_id": status.get("model_id", ""),
        "downloaded": False,
        "path": status.get("path", ""),
        "skipped": False,
        "error": status.get("error", ""),
    }
    if result["error"]:
        return result
    if status.get("downloaded"):
        if not JSON_MODE:
            print(f"[setup] Model already available: {result['model_id']}")
        result["downloaded"] = True
        return result

    if not result["model_id"]:
        result["error"] = "no llm_model_id configured"
        return result

    if not JSON_MODE:
        print(f"[setup] Downloading LLM model: {result['model_id']} (~2 GB, first time only)")
    script = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from email_concierge import load_config, download_llm_model; "
        "download_llm_model(load_config())"
    )
    kwargs = {"cwd": project, "check": False, "timeout": 3600}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if JSON_MODE:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    try:
        completed = subprocess.run([str(venv), "-c", script, str(project)], **kwargs)
    except subprocess.TimeoutExpired:
        result["error"] = "timeout after 3600s (download may still be in progress)"
        return result
    except OSError as error:
        result["error"] = str(error)
        return result

    final = _llm_model_status(venv, project)
    if final.get("error"):
        result["error"] = final["error"]
        return result
    result["downloaded"] = bool(final.get("downloaded"))
    result["path"] = final.get("path", result["path"])
    if not result["downloaded"]:
        tail = ""
        if JSON_MODE:
            tail = ((completed.stderr or "") + (completed.stdout or "")).strip()[-400:]
        result["error"] = tail or "model download failed"
    return result


def main() -> int:
    global JSON_MODE
    parser = argparse.ArgumentParser(description="Cross-platform Email Concierge setup")
    parser.add_argument("--project-dir", default=str(ROOT))
    parser.add_argument("--openvino", action="store_true", help="Install OpenVINO (enabled by default)")
    parser.add_argument("--no-openvino", action="store_true")
    parser.add_argument("--system-audio", action="store_true", help="Install PortAudio system library")
    parser.add_argument("--no-llm-model", action="store_true",
                        help="Skip downloading the local LLM model (for offline installs)")
    parser.add_argument("--yes", "-y", action="store_true", help="Run without interactive confirmation")
    parser.add_argument("--skip-system-deps", action="store_true",
                        help="Skip system package manager installs (useful inside Qoder)")
    parser.add_argument("--first-install", action="store_true",
                        help="First install mode: allow system package manager installs under explicit elevation")
    parser.add_argument("--json", action="store_true", help="Output structured result as JSON")
    args = parser.parse_args()
    JSON_MODE = args.json

    # When running without a TTY (e.g. inside Qoder), default to fully
    # automated behaviour and avoid system package manager prompts.
    # In first-install mode we are running under explicit elevation, so allow
    # system package manager installs to proceed.
    if not sys.stdin.isatty():
        args.yes = True
        if not args.first_install:
            args.skip_system_deps = True

    project = Path(args.project_dir).expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)

    report = {
        "project_dir": str(project),
        "platform": platform.system(),
        "python": sys.version.split()[0],
        "environment_supported": local_ai_environment_supported(),
        "venv_created": False,
        "core_dependencies": False,
        "openvino_dependencies": False,
        "system_audio": {"attempted": False, "installed": False, "error": ""},
        "llm_model": {"model_id": "", "downloaded": False, "path": "", "skipped": False, "error": ""},
        "hardware": {"supported": True, "reasons": []},
        "errors": [],
    }

    if not report["environment_supported"]:
        report["errors"].append("unsupported platform or Python version (< 3.10)")
        if args.json:
            print(json.dumps(report, ensure_ascii=False))
        return 1

    venv_dir = project / "venv"
    venv = _venv_python(venv_dir)
    if not venv.exists():
        try:
            run([sys.executable, "-m", "venv", str(venv_dir)])
            report["venv_created"] = True
        except (OSError, subprocess.CalledProcessError) as error:
            report["errors"].append(f"venv creation failed: {error}")
            if args.json:
                print(json.dumps(report, ensure_ascii=False))
            return 1

    try:
        run([str(venv), "-m", "pip", "install", "--upgrade", "pip"])
    except (OSError, subprocess.CalledProcessError) as error:
        report["errors"].append(f"pip upgrade failed: {error}")

    core_req = project / "requirements-core.txt"
    if not core_req.exists():
        core_req = project / "requirements.txt"
    try:
        run([str(venv), "-m", "pip", "install", "-r", str(core_req)])
        report["core_dependencies"] = True
    except (OSError, subprocess.CalledProcessError) as error:
        report["errors"].append(f"core dependency install failed: {error}")

    # OpenVINO GenAI powers local LLM inference (NPU > GPU > CPU) and
    # OpenVINO powers voice transcription. --no-openvino is an escape hatch
    # for constrained/offline environments.
    if not args.no_openvino and local_ai_environment_supported() and (project / "requirements-openvino.txt").exists():
        try:
            run([str(venv), "-m", "pip", "install", "-r", str(project / "requirements-openvino.txt")])
            report["openvino_dependencies"] = True
        except (OSError, subprocess.CalledProcessError) as error:
            report["errors"].append(f"openvino dependency install failed: {error}")

    if args.system_audio and not args.skip_system_deps:
        report["system_audio"]["attempted"] = True
        manager = package_manager()
        result = install_portaudio(manager, yes=args.yes)
        report["system_audio"].update(result)

    # Older versions registered an Ollama logon task; the skill no longer
    # uses Ollama, so remove it during migration (no-op when absent).
    remove_legacy_ollama_task()

    if not args.no_llm_model:
        hw = hardware_meets_requirements(project)
        report["hardware"] = hw
        if local_ai_environment_supported() and hw["supported"]:
            report["llm_model"] = download_llm_model(venv, project)
            if not report["llm_model"].get("downloaded") and not report["llm_model"].get("error"):
                report["llm_model"]["error"] = "model download failed"
        else:
            report["llm_model"]["skipped"] = True
            report["llm_model"]["error"] = "; ".join(hw["reasons"]) or "hardware does not meet requirements"
            if not local_ai_environment_supported():
                report["llm_model"]["error"] += "; unsupported platform or Python version"
    else:
        report["llm_model"]["skipped"] = True
        report["llm_model"]["error"] = "skipped (--no-llm-model)"

    if args.first_install:
        _write_setup_marker(project, report)

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(f"[setup] Ready: {venv} {project / 'email_concierge.py'} --diagnose --json")

    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
