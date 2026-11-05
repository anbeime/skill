#!/usr/bin/env python3
"""Shared helpers for adding a numbered style to the local style library."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from contact_sheet_registry import append_style
from style_asset_paths import ALIAS_MAP_FILE, ROOT, asset_dir, bucket_name, grid_path, single_path


SKILL_DIR = ROOT / "skills" / "handdraw-style-prompter"
SOURCE_MD = ROOT / "styles_200_reorganized.md"
MODEL_CAP = SKILL_DIR / "references" / "model_capabilities.json"
BUILD_SCRIPT = SKILL_DIR / "scripts" / "build_library.py"
VALIDATE_SCRIPT = SKILL_DIR / "scripts" / "validate_library.py"
ACTIVATIONS = {"strong", "weak", "none", "unknown"}


def get_next_style_number() -> str:
    """Return the next contiguous three-digit library number."""
    if ALIAS_MAP_FILE.exists():
        try:
            alias_data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8"))
            legacy_nums = [int(k) for k in alias_data.get("legacy_to_new", {}).keys() if k.isdigit()]
            if legacy_nums:
                return f"{max(legacy_nums) + 1:03}"
        except Exception:
            pass
    rows = re.findall(r"^\|\s*(\d{3})\s*·", SOURCE_MD.read_text(encoding="utf-8"), re.MULTILINE)
    return f"{max((int(row) for row in rows), default=0) + 1:03}"


def create_4grid_image(image_paths: list[Path], output_path: Path) -> None:
    """Write a 1024px 2×2 reference grid from two to four source images."""
    if len(image_paths) < 2:
        raise ValueError("A reference grid requires at least two source images.")
    selected = list(image_paths[:4])
    selected.extend([selected[-1]] * (4 - len(selected)))
    canvas = Image.new("RGB", (1024, 1024), (255, 255, 255))
    for path, position in zip(selected, ((0, 0), (512, 0), (0, 512), (512, 512))):
        with Image.open(path) as image:
            canvas.paste(image.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS), position)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="WEBP", quality=90, method=6)


def create_numbered_tile(source_path: Path, number: str, output_path: Path, badge_label: str | None = None) -> None:
    """Write a clean 512px gallery tile without any number badge overlay."""
    with Image.open(source_path) as source:
        image = ImageOps.fit(source.convert("RGB"), (512, 512), Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="WEBP", quality=90, method=6)


def create_style_assets(number: str, source_images: list[Path], badge_label: str | None = None) -> dict[str, Path | None]:
    """Create per-style assets and append the resulting tile to the active sheet."""
    if not source_images:
        raise ValueError("At least one source image is required.")
    destination_dir = asset_dir(number)
    destination_dir.mkdir(parents=True, exist_ok=True)
    grid = grid_path(number)
    tile = single_path(number)
    if len(source_images) >= 2:
        create_4grid_image(source_images, grid)
    elif grid.exists():
        grid.unlink()
    create_numbered_tile(source_images[0], number, tile, badge_label)
    return {
        "directory": destination_dir,
        "grid": grid if len(source_images) >= 2 else None,
        "tile": tile,
        "sheet": append_style(int(number)),
    }


def update_markdown_source(number: str, source_name: str, generation_name: str, traits: str) -> None:
    content = SOURCE_MD.read_text(encoding="utf-8")
    if re.search(rf"^\|\s*{re.escape(number)}\s*·", content, re.MULTILINE):
        raise ValueError(f"Style #{number} already exists in styles_200_reorganized.md")
    content = re.sub(r"# \d+ 种人物 IP 手绘风格库", f"# {int(number)} 种人物 IP 手绘风格库", content, count=1)
    SOURCE_MD.write_text(content.rstrip() + f"\n\n| {number} · {source_name} | {generation_name} | {traits} |\n", encoding="utf-8")


def _sheet_lines(prefix: str) -> str:
    lines: list[str] = []
    for path in sorted((ROOT / "images").glob(f"{prefix}_*.webp")):
        match = re.match(rf"^{prefix}_(\d{{3}})(?:-(\d{{3}}))?\.webp$", path.name)
        if match:
            start, end = match.group(1), match.group(2) or match.group(1)
            label = f"{prefix} {start}–{end}" if start != end else f"{prefix} {start}"
            lines.append(f"![{label}](images/{path.name})")
    return "\n\n".join(lines)


def update_readme_and_skill(number: str) -> None:
    """Refresh mutable range labels and G/H board references."""
    num_str = str(number).zfill(3)
    num_int = int(number)

    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        content = re.sub(r"001–\d+ 种手绘风格", f"001–{num_str} 种手绘风格", content)
        content = re.sub(r"\b\d+ 种手绘插画风格体系", f"{num_int} 种手绘插画风格体系", content)
        content = re.sub(r"001–\d+ 完整风格拼图大表", f"001–{num_str} 完整风格拼图大表", content)
        content = re.sub(r"（\d+ 种风格 Markdown 详细表格", f"（{num_int} 种风格 Markdown 详细表格", content)
        content = re.sub(r"### G · 附件新增 / 中国当代插画补充（201–\d+）", "### G · 附件新增 / 中国当代插画补充（201–216）", content)
        content = re.sub(r"### H · 其他（217–\d+）", f"### H · 其他（217–{num_str}）", content)
        content = re.sub(r"全库\s*\d+\s*种(?:手绘风格|画风|风格)", f"全库 {num_int} 种手绘风格", content)
        content = re.sub(r"(\d+)\s*种手绘风格与", f"{num_int} 种手绘风格与", content)
        content = re.sub(r"001–\d+\s*检索", f"001–{num_str} 检索", content)
        content = re.sub(r"（\d+\s*种完整风格拼图大表", f"（{num_int} 种完整风格拼图大表", content)
        for prefix, title in (("G", "### G · 附件新增 / 中国当代插画补充"), ("H", "### H · 其他")):
            pattern = re.compile(rf"({re.escape(title)}[^\n]*\n\n)(?:!\[{prefix} [^\]]+\]\(images/{prefix}_[^)]+\.webp\)\n*\s*)+", re.MULTILINE)
            content = pattern.sub(r"\1" + _sheet_lines(prefix) + "\n\n", content)
        readme_path.write_text(content.strip() + "\n", encoding="utf-8")

    readme_en_path = ROOT / "README_en.md"
    if readme_en_path.exists():
        en_content = readme_en_path.read_text(encoding="utf-8")
        en_content = re.sub(r"\b\d+ distinct hand-drawn illustration styles\b", f"{num_int} distinct hand-drawn illustration styles", en_content)
        en_content = re.sub(r"`001`–`\d+`", f"`001`–`{num_str}`", en_content)
        en_content = re.sub(r"001–\d+", f"001–{num_str}", en_content)
        en_content = re.sub(r"\b\d+ systematically categorized", f"{num_int} systematically categorized", en_content)
        en_content = re.sub(r"for all \d+ styles", f"for all {num_int} styles", en_content)
        en_content = re.sub(r"all \d+ illustration styles", f"all {num_int} illustration styles", en_content)
        en_content = re.sub(r"from \d+ hand-drawn styles", f"from {num_int} hand-drawn styles", en_content)
        en_content = re.sub(r"\(001–\d+ Full Visual Contact Sheets\)", f"(001–{num_str} Full Visual Contact Sheets)", en_content)
        en_content = re.sub(r"\(\d+ Styles Table & Core Traits\)", f"({num_int} Styles Table & Core Traits)", en_content)
        en_content = re.sub(r"In addition to \d+ illustration styles", f"In addition to {num_int} illustration styles", en_content)
        en_content = re.sub(r"\(\d+\s*Styles Visual Contact Sheets", f"({num_int} Styles Visual Contact Sheets", en_content)
        readme_en_path.write_text(en_content.strip() + "\n", encoding="utf-8")

    skill_paths = list(ROOT.glob("skills/*/SKILL.md")) + list(ROOT.glob(".agents/skills/*/SKILL.md")) + [ROOT / "SKILL.md"]
    for path in set(skill_paths):
        if path.exists():
            content = path.read_text(encoding="utf-8")
            content = re.sub(r"001–\d+", f"001–{num_str}", content)
            content = re.sub(r"`001`–`\d+`", f"`001`–`{num_str}`", content)
            content = re.sub(r"#001–#\d+", f"#001–#{num_str}", content)
            content = re.sub(r"`#001`–`#\d+`", f"`#001`–`#{num_str}`", content)
            content = re.sub(r"全库\s*\d+\s*种(画风|手绘风格|插画风格|风格)", lambda m: f"全库 {num_int} 种{m.group(1)}", content)
            content = re.sub(r"(\d+)\s*种(画风|手绘风格|插画风格|风格)", lambda m: f"{num_int} 种{m.group(2)}", content)
            path.write_text(content, encoding="utf-8")

    prompt_style_path = SKILL_DIR / "scripts" / "prompt_style.py"
    if prompt_style_path.exists():
        content = prompt_style_path.read_text(encoding="utf-8")
        content = re.sub(r"\b\d+ styles\b", f"{num_int} styles", content)
        prompt_style_path.write_text(content, encoding="utf-8")


def update_readme_and_skill_layouts(total: int = None, counts: dict = None) -> None:
    """Synchronize layout totals and category counts across README and SKILL files."""
    layouts_json = ROOT / "skills" / "handdraw-style-prompter" / "references" / "layouts.json"
    if layouts_json.exists():
        data = json.loads(layouts_json.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else list(data.values())
        if total is None:
            total = len(items)
        if counts is None:
            counts = {}
            for it in items:
                prefix = (it.get("id") or "").split("-")[0]
                counts[prefix] = counts.get(prefix, 0) + 1

    if not total:
        return

    sc_count = counts.get("SC", 23) if counts else 23
    ig_count = counts.get("IG", 35) if counts else 35
    sb_count = counts.get("SB", 71) if counts else 71
    ip_count = counts.get("IP", 13) if counts else 13
    ec_count = counts.get("EC", 24) if counts else 24

    readme_path = ROOT / "README.md"
    if readme_path.exists():
        c = readme_path.read_text(encoding="utf-8")
        c = re.sub(r"\*\*\d+\s*种排版图型\*\*", f"**{total} 种排版图型**", c)
        c = re.sub(r"与\s*\d+\s*种排版效果大图", f"与 {total} 种排版效果大图", c)
        c = re.sub(r"全部\s*\d+\s*种排版与提示词", f"全部 {total} 种排版与提示词", c)
        c = re.sub(r"\*\*\d+\s*种排版图型\*\*：\d+ 种社媒卡、\d+ 种数据信息图、\d+ 种漫画分镜、\d+ 种IP设计、\d+ 种电商图型",
                   f"**{total} 种排版图型**：{sc_count} 种社媒卡、{ig_count} 种数据信息图、{sb_count} 种漫画分镜、{ip_count} 种IP设计、{ec_count} 种电商图型", c)
        readme_path.write_text(c, encoding="utf-8")

    readme_en_path = ROOT / "README_en.md"
    if readme_en_path.exists():
        c = readme_en_path.read_text(encoding="utf-8")
        c = re.sub(r"\*\*\d+\s*composition layout patterns\*\*", f"**{total} composition layout patterns**", c)
        c = re.sub(r"and\s*\d+\s*layouts", f"and {total} layouts", c)
        c = re.sub(r"Browse All\s*\d+\s*Layouts", f"Browse All {total} Layouts", c)
        c = re.sub(r"\*\*\d+\s*Layout Compositions\*\*:\s*\d+ Social Cards,\s*\d+ Infographics,\s*\d+ Comic Storyboards,\s*\d+ IP Design,\s*\d+ E-commerce",
                   f"**{total} Layout Compositions**: {sc_count} Social Cards, {ig_count} Infographics, {sb_count} Comic Storyboards, {ip_count} IP Design, {ec_count} E-commerce", c)
        readme_en_path.write_text(c, encoding="utf-8")

    skill_paths = list(ROOT.glob("skills/*/SKILL.md")) + list(ROOT.glob(".agents/skills/*/SKILL.md")) + [ROOT / "SKILL.md"]
    for path in set(skill_paths):
        if path.exists():
            c = path.read_text(encoding="utf-8")
            c = re.sub(r"全部\s*\d+\s*种排版图型", f"全部 {total} 种排版图型", c)
            c = re.sub(r"协同\s*\d+\s*种排版图型", f"协同 {total} 种排版图型", c)
            c = re.sub(r"图型（\d+\s*种）", f"图型（{total} 种）", c)
            c = re.sub(r"\d+\s*种图型版式编号", f"{total} 种图型版式编号", c)
            path.write_text(c, encoding="utf-8")



def update_manifest(number: str) -> None:
    """Keep the human-readable package manifest aligned with the current range."""
    path = ROOT / "MANIFEST.md"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"当前 \d+ 风格表", f"当前 {int(number)} 风格表", content)
    boards = [f"- `{entry.name}`" for entry in sorted((ROOT / "images").glob("[A-H]_*.webp"))]
    content = re.sub(r"(## 已收录图片\n\n).*?(\n\n## 单张图片)", r"\1" + "\n".join(boards) + r"\2", content, flags=re.DOTALL)
    bucket = bucket_name(number)
    content = re.sub(r"images/individual/201-400/201\.webp`–`images/individual/\d{3}-\d{3}/\d{3}\.webp`：201–\d+ 的编号单图",
                     f"images/individual/201-400/201.webp`–`images/individual/{bucket}/{number}.webp`：201–{number} 的编号单图", content)
    content = re.sub(r"H：217–\d+，完整（其他）", f"H：217–{number}，完整（其他）", content)
    content = re.sub(r"单图总数：\d+ 张", f"单图总数：{int(number)} 张", content)
    content = re.sub(r"风格编号覆盖：001–\d+", f"风格编号覆盖：001–{number}", content)
    path.write_text(content, encoding="utf-8")


def update_model_capabilities(number: str, *, name_activation: str, traits_activation: str) -> None:
    if name_activation not in ACTIVATIONS or traits_activation not in ACTIVATIONS:
        raise ValueError("Unsupported model activation value.")
    data = json.loads(MODEL_CAP.read_text(encoding="utf-8"))
    styles = data["models"]["gpt-image-2"].setdefault("styles", {})
    styles[number] = {"name_activation": name_activation, "traits_activation": traits_activation}
    MODEL_CAP.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rebuild_and_validate() -> None:
    python = [sys.executable, "-X", "utf8"]
    subprocess.run(python + [str(BUILD_SCRIPT)], check=True)
    subprocess.run(python + [str(VALIDATE_SCRIPT)], check=True)
