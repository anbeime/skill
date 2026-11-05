#!/usr/bin/env python3
"""仓库不变量检查：Skill 说明、文档里引用的路径、随包字体与许可证、脚本语法、示例和标签配置。

只读，不渲染。渲染冒烟测试在 tests/ 里。
"""

import hashlib
import json
import py_compile
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "cy-carousel"
# SKILL.md / README.md 里用反引号或 Markdown 链接引用的仓库内路径，必须真实存在。
PATH_PREFIXES = ("scripts/", "references/", "examples/", "assets/", "tools/", "docs/", "tests/")
PATH_PATTERN = re.compile(r"(?:`|\]\()((?:%s)[^`)\s]*)" % "|".join(re.escape(p) for p in PATH_PREFIXES))
REQUIRED_FILES = ("SKILL.md", "README.md", "LICENSE", "requirements.txt", "CLAUDE.md", "docs/agent-workflow.md")


def check_skill(errors):
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append("SKILL.md 缺少 YAML frontmatter")
        return
    meta = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    if meta.get("name", "").strip() != SKILL_NAME:
        errors.append(f"SKILL.md 的 name 必须是 {SKILL_NAME}")
    if len(meta.get("description", "").strip()) < 20:
        errors.append("SKILL.md 的 description 过短或缺失")


def check_referenced_paths(errors):
    for doc in ("SKILL.md", "README.md", "CLAUDE.md", "docs/agent-workflow.md"):
        for raw in PATH_PATTERN.findall((ROOT / doc).read_text(encoding="utf-8")):
            path = raw.split("#", 1)[0].rstrip("/.,，。")
            if any(ch in path for ch in "*{<"):
                continue
            if not (ROOT / path).exists():
                errors.append(f"{doc} 引用的路径不存在：{path}")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_fonts(errors):
    fonts = ROOT / "assets/fonts"
    manifest = json.loads((fonts / "来源与许可证.json").read_text(encoding="utf-8"))
    listed = set()
    for entry in manifest:
        for key in ("font", "license"):
            path = fonts / entry[key]
            listed.add(path.name)
            if not path.is_file():
                errors.append(f"字体清单里的文件不存在：assets/fonts/{entry[key]}")
            elif sha256(path) != entry[f"{key}_sha256"]:
                errors.append(f"SHA256 与清单不符：assets/fonts/{entry[key]}")
    for path in fonts.glob("*.[ot]tf"):
        if path.name not in listed:
            errors.append(f"字体没有登记许可证：assets/fonts/{path.name}")


def check_python(errors):
    files = sorted(ROOT.glob("scripts/*.py")) + sorted(ROOT.glob("examples/*/*.py"))
    files += sorted(ROOT.glob("tools/*.py")) + sorted(ROOT.glob(".github/scripts/*.py"))
    with tempfile.TemporaryDirectory() as tmp:
        for i, path in enumerate(files):
            try:
                py_compile.compile(str(path), cfile=str(Path(tmp) / f"{i}.pyc"), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"语法错误：{path.relative_to(ROOT)}：{exc.msg.strip()}")


def check_examples(errors):
    examples = sorted(p for p in (ROOT / "examples").iterdir() if p.is_dir())
    if not examples:
        errors.append("examples/ 下没有样板")
    for folder in examples:
        for name in ("README.md", "全套预览.jpg"):
            if not (folder / name).is_file():
                errors.append(f"样板缺文件：{folder.relative_to(ROOT)}/{name}")


def check_labels(errors):
    labels = json.loads((ROOT / ".github/labels.json").read_text(encoding="utf-8"))
    names = [label["name"] for label in labels]
    if len(names) != len(set(names)):
        errors.append(".github/labels.json 有重名标签")
    for label in labels:
        if not re.fullmatch(r"[0-9a-f]{6}", label.get("color", "")):
            errors.append(f"标签颜色不是 6 位十六进制：{label['name']}")


def validate():
    errors = [f"缺少文件：{name}" for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if errors:
        return errors
    for check in (check_skill, check_referenced_paths, check_fonts, check_python, check_examples, check_labels):
        check(errors)
    return errors


def main():
    errors = validate()
    for error in errors:
        print(f"✗ {error}", file=sys.stderr)
    if errors:
        return 1
    print("✓ 仓库检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
