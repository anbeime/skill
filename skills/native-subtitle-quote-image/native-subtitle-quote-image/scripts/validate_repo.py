#!/usr/bin/env python3
"""Validate repository packaging invariants without external dependencies."""

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "native-subtitle-quote-image"
SKILL_FILE = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
RENDERER = SKILL_DIR / "scripts" / "native_subtitle_stitch.py"
ENV_CHECK = SKILL_DIR / "scripts" / "check_environment.py"
UPDATE_CHECK = SKILL_DIR / "scripts" / "check_update.py"
VERSION_FILE = SKILL_DIR / "VERSION"
README = ROOT / "README.md"
README_EN = ROOT / "README_EN.md"
README_KO = ROOT / "README_KO.md"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
EXPECTED_NAME = "native-subtitle-quote-image"
EXPECTED_VERSION = "2.10.3"


def main():
    errors = []
    required = [
        ROOT / "LICENSE",
        README,
        README_EN,
        README_KO,
        ROOT / "assets" / "native-subtitle-quote-image-icon.png",
        ROOT / "examples" / "gallery-manifest.json",
        ROOT / "assets" / "banner-zh.jpg",
        ROOT / "assets" / "banner-en.jpg",
        ROOT / "assets" / "banner-ko.jpg",
        PLUGIN,
        SKILL_FILE,
        VERSION_FILE,
        OPENAI_YAML,
        SKILL_DIR / "requirements.txt",
        RENDERER,
        ENV_CHECK,
        UPDATE_CHECK,
        SKILL_DIR / "references" / "yt-dlp-and-transcripts.md",
        SKILL_DIR / "references" / "end-to-end-workflow.md",
        SKILL_DIR / "references" / "visual-style.md",
        SKILL_DIR / "references" / "troubleshooting.md",
        ROOT / ".github" / "workflows" / "validate.yml",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"缺少文件: {path.relative_to(ROOT)}")

    try:
        plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"plugin.json 无法解析: {exc}")
        plugin = {}
    if plugin.get("name") != EXPECTED_NAME:
        errors.append("plugin.json name 与 Skill 目录不一致")
    if plugin.get("version") != EXPECTED_VERSION:
        errors.append(
            f"plugin.json version 应为 {EXPECTED_VERSION}，实际为 {plugin.get('version')}"
        )
    if plugin.get("skills") != "./skills/":
        errors.append("plugin.json skills 必须指向 ./skills/")

    if VERSION_FILE.is_file():
        skill_version = VERSION_FILE.read_text(encoding="utf-8").strip()
        if skill_version != EXPECTED_VERSION:
            errors.append(
                f"Skill VERSION 应为 {EXPECTED_VERSION}，实际为 {skill_version}"
            )

    skill_text = SKILL_FILE.read_text(encoding="utf-8") if SKILL_FILE.is_file() else ""
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, flags=re.DOTALL)
    if not frontmatter:
        errors.append("SKILL.md 缺少有效 YAML frontmatter")
    else:
        header = frontmatter.group(1)
        if not re.search(rf"^name:\s*{re.escape(EXPECTED_NAME)}\s*$", header, re.MULTILINE):
            errors.append("SKILL.md name 不正确")
        if not re.search(r"^description:\s*\S.+$", header, re.MULTILINE):
            errors.append("SKILL.md description 不能为空")

    yaml_text = OPENAI_YAML.read_text(encoding="utf-8") if OPENAI_YAML.is_file() else ""
    if f"${EXPECTED_NAME}" not in yaml_text:
        errors.append("agents/openai.yaml default_prompt 未引用当前 Skill")

    for reference in (
        "references/yt-dlp-and-transcripts.md",
        "references/end-to-end-workflow.md",
        "references/visual-style.md",
        "references/troubleshooting.md",
    ):
        if reference not in skill_text:
            errors.append(f"SKILL.md 未链接参考文件: {reference}")

    public_docs = [
        README,
        README_EN,
        README_KO,
        ROOT / "examples" / "README.md",
        SKILL_FILE,
        SKILL_DIR / "references" / "yt-dlp-and-transcripts.md",
        SKILL_DIR / "references" / "end-to-end-workflow.md",
        SKILL_DIR / "references" / "visual-style.md",
        SKILL_DIR / "references" / "troubleshooting.md",
    ]
    for document in public_docs:
        text = document.read_text(encoding="utf-8") if document.is_file() else ""
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            clean_target = target.split("#", 1)[0]
            if not clean_target or clean_target.startswith(
                ("http://", "https://", "mailto:", "#")
            ):
                continue
            linked = (document.parent / clean_target).resolve()
            if not linked.exists():
                errors.append(
                    f"{document.relative_to(ROOT)} 链接不存在: {target}"
                )

    readme_text = README.read_text(encoding="utf-8") if README.is_file() else ""
    for readme in (README, README_EN, README_KO):
        text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        for source in re.findall(r'<img\s+[^>]*src="([^"]+)"', text):
            if source.startswith(("http://", "https://")):
                continue
            if not (ROOT / source).is_file():
                errors.append(f"{readme.name} 图片不存在: {source}")
    readme_languages = {README: "zh", README_EN: "en", README_KO: "ko"}
    readme_images = {}
    for readme, lang in readme_languages.items():
        text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        shown = set(re.findall(r"examples/gallery/[^\"')\s]+", text))
        readme_images[lang] = shown
        for source in sorted(shown):
            if not source.startswith(f"examples/gallery/{lang}/"):
                errors.append(f"{readme.name} 只能展示 {lang} 字幕案例: {source}")

    manifest_path = ROOT / "examples" / "gallery-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"gallery-manifest.json 无法解析: {exc}")
        manifest = {}
    manifest_images = {lang: set() for lang in readme_languages.values()}
    for example in manifest.get("examples", []):
        lang = example.get("language")
        manifest_images.setdefault(lang, set()).add(f"examples/{example.get('image')}")
        if example.get("script") and not example["script"].startswith(f"scripts/{lang}/"):
            errors.append(f"案例脚本不在对应语言目录: {example.get('id')}")
        image_path = ROOT / "examples" / str(example.get("image", ""))
        if image_path.is_file() and hashlib.sha256(image_path.read_bytes()).hexdigest() != example.get("sha256"):
            errors.append(f"案例图片 SHA-256 与 manifest 不一致: {example.get('id')}")
        if lang not in readme_languages.values():
            errors.append(f"案例语言无效: {example.get('id')}")
        if not str(example.get("image", "")).startswith(f"gallery/{lang}/"):
            errors.append(f"案例图片不在对应语言目录: {example.get('id')}")
        for key in ("image", "script"):
            if example.get(key) and not (ROOT / "examples" / example[key]).is_file():
                errors.append(f"案例文件不存在: {example[key]}")

    for lang, images in manifest_images.items():
        if len(images) != 3:
            errors.append(f"{lang} 案例应为 3 张，实际 {len(images)} 张")
        if readme_images.get(lang, set()) != images:
            errors.append(f"{lang} README 展示的案例与 manifest 不一致")
    listed = {path for images in manifest_images.values() for path in images}
    for image in sorted((ROOT / "examples" / "gallery").rglob("*.jpg")):
        relative = image.relative_to(ROOT).as_posix()
        if relative not in listed:
            errors.append(f"案例图片未登记在 manifest: {relative}")

    if "~/.codex/skills" not in readme_text:
        errors.append("README 缺少 Codex 默认 Skill 安装目录")
    for document in (README, README_EN, README_KO, SKILL_FILE):
        text = document.read_text(encoding="utf-8") if document.is_file() else ""
        if "render-script" not in text:
            errors.append(f"{document.relative_to(ROOT)} 未说明脚本字幕模式")

    for script in (RENDERER, ENV_CHECK, UPDATE_CHECK):
        if script.is_file():
            try:
                compile(script.read_text(encoding="utf-8"), str(script), "exec")
            except SyntaxError as exc:
                errors.append(f"脚本语法错误 {script.relative_to(ROOT)}: {exc}")

    public_text_files = [
        *public_docs,
        OPENAI_YAML,
        RENDERER,
        ENV_CHECK,
        UPDATE_CHECK,
        VERSION_FILE,
        PLUGIN,
    ]
    for path in public_text_files:
        if path.is_file() and "/Users/" in path.read_text(encoding="utf-8"):
            errors.append(f"包含本机绝对路径: {path.relative_to(ROOT)}")

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Repository is valid: {EXPECTED_NAME} v{EXPECTED_VERSION}")


if __name__ == "__main__":
    main()
