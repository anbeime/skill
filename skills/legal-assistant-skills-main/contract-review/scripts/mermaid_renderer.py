#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render Mermaid flowcharts to image files via mermaid-cli (mmdc).
"""

from __future__ import annotations

import shutil
import subprocess
import json
import os
import tempfile
import re
from pathlib import Path
from typing import Optional, Tuple


def normalize_mermaid_code(code: str) -> str:
    """
    Normalize Mermaid code by stripping code fences and ensuring a trailing newline.
    """
    cleaned = code.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            cleaned = "\n".join(lines[1:-1]).strip()
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned


def write_mermaid_file(code: str, output_dir: Path, filename: str) -> Path:
    """
    Write Mermaid code to a .mmd file in output_dir.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mmd_path = output_dir / filename
    mmd_path.write_text(code, encoding="utf-8")
    return mmd_path


def render_mermaid_file(
    mmd_path: Path,
    image_path: Path,
    theme: str = "default",
    background_color: str = "white",
    mmdc_path: Optional[str] = None,
    scale: float = 2,
    width: Optional[int] = None,
    height: Optional[int] = None,
    puppeteer_config_path: Optional[str] = None,
) -> None:
    """
    Render a Mermaid .mmd file to an image using mermaid-cli (mmdc).
    """
    mmdc_path = mmdc_path or shutil.which("mmdc")
    if not mmdc_path:
        raise FileNotFoundError(
            "mmdc not found in PATH. Install @mermaid-js/mermaid-cli to render Mermaid."
        )

    def build_cmd(input_path: Path, config_path: Optional[Path]) -> list[str]:
        cmd = [mmdc_path, "-i", str(input_path), "-o", str(image_path)]
        if theme:
            cmd += ["-t", theme]
        if background_color:
            cmd += ["-b", background_color]
        if scale and scale != 1:
            cmd += ["-s", str(scale)]
        if width:
            cmd += ["-w", str(width)]
        if height:
            cmd += ["-H", str(height)]
        if config_path:
            cmd += ["-p", str(config_path)]
        return cmd

    config_path = Path(puppeteer_config_path) if puppeteer_config_path else None
    created_config = False
    temp_user_data_dir: Optional[Path] = None
    last_error: Optional[subprocess.CalledProcessError] = None

    try:
        try:
            subprocess.run(build_cmd(mmd_path, config_path), check=True)
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc

        if config_path is None:
            chrome_path = os.environ.get("PUPPETEER_EXECUTABLE_PATH") or _find_chrome_executable()
            if not chrome_path:
                raise last_error
            config_path, temp_user_data_dir = _write_puppeteer_config(chrome_path)
            created_config = True

        try:
            subprocess.run(build_cmd(mmd_path, config_path), check=True)
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc

        try:
            original = mmd_path.read_text(encoding="utf-8")
        except Exception:
            raise last_error

        sanitized = _sanitize_mermaid_code_for_render(original)
        if sanitized == original:
            raise last_error

        sanitized_path = _write_temp_mmd(sanitized, mmd_path)
        try:
            subprocess.run(build_cmd(sanitized_path, config_path), check=True)
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc
            raise last_error
        finally:
            try:
                sanitized_path.unlink(missing_ok=True)
            except Exception:
                pass
    finally:
        if created_config:
            try:
                config_path.unlink(missing_ok=True)
            except Exception:
                pass
            if temp_user_data_dir:
                shutil.rmtree(temp_user_data_dir, ignore_errors=True)


def render_mermaid_code(
    code: str,
    output_dir: Path,
    mmd_filename: str,
    image_filename: str,
    theme: str = "default",
    background_color: str = "white",
    scale: float = 2,
    width: Optional[int] = None,
    height: Optional[int] = None,
    puppeteer_config_path: Optional[str] = None,
) -> Tuple[Path, Path]:
    """
    Write Mermaid code to .mmd and render to image.
    """
    normalized = normalize_mermaid_code(code)
    mmd_path = write_mermaid_file(normalized, output_dir, mmd_filename)
    image_path = Path(output_dir) / image_filename
    render_mermaid_file(
        mmd_path,
        image_path,
        theme=theme,
        background_color=background_color,
        scale=scale,
        width=width,
        height=height,
        puppeteer_config_path=puppeteer_config_path,
    )
    return mmd_path, image_path


def _find_chrome_executable() -> Optional[str]:
    """
    Best-effort Chrome/Chromium detection for Puppeteer fallback.
    """
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def _write_puppeteer_config(executable_path: str) -> tuple[Path, Path]:
    """
    Write a temporary Puppeteer config with safer sandbox args.
    """
    user_data_dir = Path(tempfile.mkdtemp(prefix="puppeteer-user-data-"))
    payload = {
        "executablePath": executable_path,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-crashpad",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={user_data_dir}",
        ],
    }
    handle, path = tempfile.mkstemp(prefix="puppeteer-", suffix=".json")
    os.close(handle)
    config_path = Path(path)
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    return config_path, user_data_dir


def _sanitize_mermaid_code_for_render(code: str) -> str:
    if "%" not in code and "％" not in code:
        return code
    replacement = "百分比" if _contains_cjk(code) else "percent"
    sanitized = code.replace("％", replacement).replace("%", replacement)
    sanitized = re.sub(r"(?<=\\d),(?=\\d)", "", sanitized)
    sanitized = sanitized.replace("(", " ").replace(")", " ")
    sanitized = re.sub(r"\\s{2,}", " ", sanitized)
    return sanitized


def _contains_cjk(text: str) -> bool:
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def _write_temp_mmd(code: str, source_path: Path) -> Path:
    handle, path = tempfile.mkstemp(
        prefix=f"{source_path.stem}-sanitized-",
        suffix=source_path.suffix,
    )
    os.close(handle)
    temp_path = Path(path)
    temp_path.write_text(code, encoding="utf-8")
    return temp_path
