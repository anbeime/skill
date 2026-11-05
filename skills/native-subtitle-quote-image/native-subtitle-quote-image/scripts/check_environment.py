#!/usr/bin/env python3
"""检查视频字幕拼图的原生、脚本与 URL 模式所需组件，不执行安装。"""

import argparse
import importlib
import importlib.util
import json
import locale
import shutil
import subprocess
import sys
from pathlib import Path


CJK_FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def command_version(command, args=("--version",)):
    path = shutil.which(command)
    if not path:
        return None, None
    try:
        proc = subprocess.run(
            [path, *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return path, "无法读取版本"
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    return path, output[0] if output else "版本未知"


def module_version(name):
    if importlib.util.find_spec(name) is None:
        return None
    module = importlib.import_module(name)
    return getattr(module, "__version__", "已安装")


def add(rows, component, status, purpose, detail="", required="core"):
    rows.append(
        {
            "component": component,
            "status": status,
            "purpose": purpose,
            "detail": detail,
            "required": required,
        }
    )


def utf8_default():
    if sys.flags.utf8_mode:
        return True
    return locale.getpreferredencoding(False).lower().replace("-", "") == "utf8"


def inspect_environment():
    rows = []
    python_ok = sys.version_info >= (3, 10)
    add(
        rows,
        "Python 3.10+",
        "ok" if python_ok else "missing",
        "运行 Skill 脚本",
        sys.version.split()[0],
    )

    if not utf8_default():
        add(
            rows,
            "UTF-8 encoding",
            "optional",
            "文本读写：默认编码非 UTF-8 时中文路径与输出可能乱码",
            f"当前默认编码 {locale.getpreferredencoding(False)}；"
            "建议设置 PYTHONUTF8=1（cmd: set PYTHONUTF8=1）",
            required="optional",
        )

    pillow = module_version("PIL")
    add(
        rows,
        "Pillow",
        "ok" if pillow else "missing",
        "裁图、拼图、导出 JPG",
        str(pillow or "未安装"),
    )

    ffmpeg_detail = ""
    imageio = module_version("imageio_ffmpeg")
    if imageio:
        try:
            imageio_module = importlib.import_module("imageio_ffmpeg")
            ffmpeg_detail = f"imageio-ffmpeg {imageio}: {imageio_module.get_ffmpeg_exe()}"
        except Exception as exc:  # pragma: no cover - platform-specific failure
            ffmpeg_detail = f"imageio-ffmpeg 已安装但不可用: {exc}"
            imageio = None
    system_ffmpeg, ffmpeg_version = command_version("ffmpeg", ("-version",))
    ffmpeg_ok = bool(imageio or system_ffmpeg)
    if system_ffmpeg:
        system_detail = f"system: {system_ffmpeg} ({ffmpeg_version})"
        ffmpeg_detail = f"{ffmpeg_detail}; {system_detail}" if ffmpeg_detail else system_detail
    add(
        rows,
        "FFmpeg provider",
        "ok" if ffmpeg_ok else "missing",
        "读取视频并精确取帧",
        ffmpeg_detail or "请安装 imageio-ffmpeg 或 FFmpeg 可执行文件",
    )

    cjk_font = next(
        (candidate for candidate in CJK_FONT_CANDIDATES if Path(candidate).is_file()),
        None,
    )
    add(
        rows,
        "CJK font",
        "ok" if cjk_font else "missing",
        "脚本字幕模式：绘制中文、日文或韩文台词",
        cjk_font or "未找到常见 CJK 字体；可安装 Noto Sans CJK 或用 --font 指定",
        required="script",
    )

    ytdlp_path, ytdlp_version = command_version("yt-dlp")
    add(
        rows,
        "yt-dlp",
        "ok" if ytdlp_path else "missing",
        "URL 模式：读取元数据、字幕轨和下载视频",
        f"{ytdlp_version} ({ytdlp_path})" if ytdlp_path else "本地视频模式不需要",
        required="url",
    )

    runtimes = []
    for label, command in (
        ("Deno", "deno"),
        ("Node.js", "node"),
        ("QuickJS", "qjs"),
        ("Bun (deprecated)", "bun"),
    ):
        path, version = command_version(command)
        if path:
            runtimes.append((label, command, path, version))
    if runtimes:
        label, command, path, version = runtimes[0]
        if command == "deno":
            detail = f"{label} {version} ({path})；yt-dlp 默认启用"
        elif command == "bun":
            detail = (
                f"{label} {version} ({path})；调用 yt-dlp 时添加 "
                "--js-runtimes bun；官方已将 Bun 支持标记为弃用"
            )
        else:
            detail = (
                f"{label} {version} ({path})；调用 yt-dlp 时添加 "
                f"--js-runtimes {command}"
            )
        add(
            rows,
            "JavaScript runtime",
            "ok",
            "URL 模式：完整解析 YouTube",
            detail,
            required="url",
        )
    else:
        add(
            rows,
            "JavaScript runtime",
            "missing",
            "URL 模式：完整解析 YouTube",
            "推荐 Deno；也可使用 Node.js 或 QuickJS；Bun 支持已弃用",
            required="url",
        )

    whisper_cli, whisper_version = command_version("whisper")
    whisper_module = module_version("faster_whisper") or module_version("whisper")
    whisper_ok = bool(whisper_cli or whisper_module)
    whisper_detail = "未安装；只有来源没有可用时间轴时才需要"
    if whisper_cli:
        whisper_detail = f"CLI {whisper_version} ({whisper_cli})"
    elif whisper_module:
        whisper_detail = f"Python module {whisper_module}"
    add(
        rows,
        "Whisper / speech-to-text",
        "optional" if not whisper_ok else "ok",
        "可选：没有字幕轨时生成带时间戳文字稿",
        whisper_detail,
        required="optional",
    )
    return rows


def is_blocking(row, url_mode, script_mode):
    if row["status"] != "missing":
        return False
    return (
        row["required"] == "core"
        or (url_mode and row["required"] == "url")
        or (script_mode and row["required"] == "script")
    )


def print_human(rows, url_mode, script_mode):
    labels = {"ok": "可用", "missing": "缺失", "optional": "可选"}
    widths = (26, 8, 38)
    print(f"{'组件':<{widths[0]}} {'状态':<{widths[1]}} 用途")
    print("-" * 92)
    for row in rows:
        print(
            f"{row['component']:<{widths[0]}} "
            f"{labels[row['status']]:<{widths[1]}} "
            f"{row['purpose']}"
        )
        if row["detail"]:
            print(f"  {row['detail']}")

    blocking = [row for row in rows if is_blocking(row, url_mode, script_mode)]
    source = "URL" if url_mode else "本地视频"
    subtitle = "脚本字幕" if script_mode else "原生字幕"
    mode = f"{source} + {subtitle}模式"
    if blocking:
        print(f"\n{mode}尚不可用，缺少: " + ", ".join(row["component"] for row in blocking))
    else:
        print(f"\n{mode}环境检查通过。")
    if url_mode:
        print(
            "提示：若 YouTube 返回登录或机器人验证，不要退回本地模式；"
            "先取得用户授权，再在该 URL 的 yt-dlp 命令中添加 "
            "--cookies-from-browser chrome。"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url-mode",
        action="store_true",
        help="把 yt-dlp 和 JavaScript runtime 也作为必需组件检查",
    )
    parser.add_argument(
        "--script-mode",
        action="store_true",
        help="把绘制中文台词所需的 CJK 字体也作为必需组件检查",
    )
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    rows = inspect_environment()
    blocking = [
        row
        for row in rows
        if is_blocking(row, args.url_mode, args.script_mode)
    ]
    if args.json:
        print(
            json.dumps(
                {
                    "mode": "url" if args.url_mode else "local",
                    "script_mode": args.script_mode,
                    "ok": not blocking,
                    "components": rows,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_human(rows, args.url_mode, args.script_mode)
    raise SystemExit(1 if blocking else 0)


if __name__ == "__main__":
    main()
