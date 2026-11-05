#!/usr/bin/env python3
"""Validate source parsing, generated assets, and the deterministic prompt contract."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
from resolve_reference import resolve
from contact_sheet_registry import CAPACITY, STATE_FILE, parse_sheet, sheet_path
from layout_library import load_layouts
from style_asset_paths import bucket_name, grid_path, single_path

SKILL = Path(__file__).resolve().parents[1]
GRAPHIC_TEXT_SUFFIX = "【如果主题直白包含画面元素那就按主题出图，文案由你来升华，但是不要直接描述画面。 如果主题比较概念化，那么文案和主题尽量保持一致，如果文案较长由你提炼，由你先设计画面隐喻（人类和非人类都行）再出图   。    文字参与构图，图文一体】"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    python = [sys.executable, "-X", "utf8"]
    subprocess.run(python + [str(SKILL / "scripts" / "build_library.py")], check=True)
    subprocess.run(python + [str(SKILL / "scripts" / "build_layout_gallery.py")], check=True)
    subprocess.run(python + [str(SKILL / "scripts" / "build_color_gallery.py")], check=True)
    subprocess.run(python + [str(SKILL / "scripts" / "build_assets_gallery.py")], check=True)
    subprocess.run(python + [str(SKILL / "scripts" / "build_tutorial_gallery.py")], check=True)
    styles = json.loads((SKILL / "references" / "styles.json").read_text(encoding="utf-8"))
    attribution = json.loads((SKILL / "references" / "attribution.json").read_text(encoding="utf-8"))
    model_capabilities = json.loads((SKILL / "references" / "model_capabilities.json").read_text(encoding="utf-8"))
    alias_file = SKILL / "references" / "style_alias_map.json"
    if not alias_file.exists():
        fail("style_alias_map.json is missing")
    alias_data = json.loads(alias_file.read_text(encoding="utf-8"))
    legacy_to_new = alias_data.get("legacy_to_new", {})
    new_to_legacy = alias_data.get("new_to_legacy", {})
    if len(legacy_to_new) != len(styles) or len(new_to_legacy) != len(styles):
        fail("style_alias_map.json must cover every style bidirectionally")
    if set(new_to_legacy) != {item["number"] for item in styles} or any(new_to_legacy.get(value) != key for key, value in legacy_to_new.items()):
        fail("style aliases must resolve to the canonical style set and round-trip")

    total_styles = len(styles)
    if total_styles < 365:
        fail(f"expected at least the 365 baseline styles, got {total_styles}")

    CATEGORIES = ["FA", "FB", "FC", "FD", "FE", "FF", "FG", "FH", "FI"]
    cat_counts = {}
    import re
    for item in styles:
        num = item["number"]
        m = re.match(r"^([A-Za-z]{2})-(\d{3})$", num)
        if not m:
            fail(f"Invalid style ID format: {num}")
        cat, idx = m.group(1), int(m.group(2))
        if cat not in CATEGORIES:
            fail(f"Unknown category in style ID: {num}")
        expected_idx = cat_counts.get(cat, 0) + 1
        if idx != expected_idx:
            fail(f"Non-continuous style number in category {cat}: expected {cat}-{expected_idx:03}, got {num}")
        cat_counts[cat] = idx

    eighteen = next(item for item in styles if item["number"] == "FA-018")
    if eighteen["generation_name"] != "Minimal Deadpan Dialogue Cartoon":
        fail("FA-018 maps to the wrong generation name")
    if any(record.get("status") == "deceased" and not record.get("source") for record in attribution.values()):
        fail("a deceased attribution record has no verification source")
    if model_capabilities.get("default", {}).get("name_activation") != "unknown":
        fail("the model capability default must be unknown")
    if model_capabilities.get("default", {}).get("use_reference_image") is not True:
        fail("unknown model capability must use the image fallback")

    all_style_ids = set(item["number"] for item in styles)
    for model, profile in model_capabilities.get("models", {}).items():
        if profile.get("name_activation") not in {None, "strong", "weak", "none", "unknown"}:
            fail(f"invalid model capability for {model}")
        if profile.get("traits_activation") not in {None, "strong", "weak", "none", "unknown"}:
            fail(f"invalid traits capability for {model}")
        for number, entry in profile.get("styles", {}).items():
            if number not in all_style_ids and number not in legacy_to_new:
                fail(f"model capability references invalid style {number}")
            if entry.get("name_activation") not in {"strong", "weak", "none", "unknown"}:
                fail(f"invalid style capability for {model}/{number}")
            if entry.get("traits_activation") not in {None, "strong", "weak", "none", "unknown"}:
                fail(f"invalid traits style capability for {model}/{number}")

    unknown = resolve("unregistered-model", "FA-001")
    if unknown["name_activation"] != "unknown" or not unknown["use_reference_image"]:
        fail("unknown model must use reference image")
    if resolve("gpt-image-2", "FA-001")["use_reference_image"] is not False:
        fail("gpt-image-2 style FA-001 should use name activation")
    if resolve("gpt-image-2", "001")["use_reference_image"] is not False:
        fail("gpt-image-2 legacy style 001 resolution should match FA-001")

    style_011_res = resolve("gpt-image-2", "FA-011")
    if style_011_res["activation_source"] != "name+style" or style_011_res["use_reference_image"] is not False or style_011_res["prompt_traits"]:
        fail("style FA-011 must use author name activation only without reference image or traits")
    manual_name = resolve("gpt-image-2", "FG-009")
    if manual_name["activation_source"] != "name+style" or manual_name["use_reference_image"] or manual_name["prompt_traits"]:
        fail("text-defined name-only style must use name activation without an image or traits")
    if resolve("gpt-image-2", "FH-001")["activation_source"] != "name+style+traits" or resolve("gpt-image-2", "FH-001")["use_reference_image"] is not False:
        fail("gpt-image-2 style with positive traits should use name+traits activation")

    synthetic = {"default": model_capabilities["default"], "models": {
        "test-model": {"name_activation": "unknown", "traits_activation": "strong", "styles": {
            "FE-016": {"name_activation": "none", "traits_activation": "none"},
            "FA-002": {"name_activation": "strong"},
            "FA-022": {"name_activation": "none", "traits_activation": "none"},
        }},
    }}
    if resolve("test-model", "FE-016", synthetic)["use_reference_image"] is not True:
        fail("empty traits or insufficient capability must use reference image")
    if resolve("test-model", "FA-002", synthetic)["use_reference_image"] is not False:
        fail("strong capability must not use reference image")
    reference_with_traits = resolve("test-model", "FA-022", synthetic)
    if (reference_with_traits["activation_source"] != "name+style+traits+reference-image"
            or not reference_with_traits["use_reference_image"]
            or not reference_with_traits["prompt_traits"]):
        fail("reference fallback with traits must preserve traits and require the image")
    traits_case = resolve("gpt-image-2", "FA-022")
    if traits_case["activation_source"] != "name+style+traits" or not traits_case["prompt_traits"] or "避免" in traits_case["prompt_traits"]:
        fail("gpt-image-2 traits activation did not produce filtered positive traits")
    if resolve("gpt-image-2", "FE-016")["activation_source"] != "name+style+traits" or resolve("gpt-image-2", "FE-016")["use_reference_image"] is not False:
        fail("style FE-016 should use name+style+traits activation")
    if bucket_name("FA-001") != "FA" or bucket_name("FE-048") != "FE" or bucket_name("FF-001") != "FF":
        fail("style asset bucket calculation is incorrect")
    reference_217 = resolve("gpt-image-2", "FF-001")
    if (reference_217["activation_source"] != "name+style+traits+reference-image"
            or not reference_217["prompt_traits"]
            or reference_217["reference_path"] != str(grid_path("FF-001"))):
        fail("style FF-001 (217) must preserve traits and use its four-panel grid reference")
    if not grid_path("FF-001").exists():
        fail("style FF-001 four-panel grid is missing")
    for s_id in ["FG-007", "FG-008", "FG-009", "FG-010", "FB-033", "FE-060", "FE-061", "FE-062"]:
        reference = resolve("unregistered-model", s_id)
        if grid_path(s_id).exists() or reference["reference_path"] != str(single_path(s_id)):
            fail(f"single-image style {s_id} must not retain a redundant grid reference")
    fe_supplement = [s for s in styles if s["number"].startswith("FE-") and 32 <= int(s["number"].split("-")[1]) <= 47]
    if any(not item["traits"] for item in fe_supplement):
        fail("FE-032–FE-047 core visual traits must be populated")
    style_205 = next(item for item in styles if item["number"] == "FE-036")
    if not style_205["traits"] or "冷幽默" not in style_205["traits"]:
        fail("style FE-036 (old 205) core visual traits are missing")
    if any(item["number"].split("-")[0] not in CATEGORIES for item in styles):
        fail(f"all styles must belong to one of {len(CATEGORIES)} categories")
    individual = ROOT / "images" / "individual"
    expected_individual = [single_path(s["number"]) for s in styles]
    if not all(path.exists() for path in expected_individual):
        fail(f"category asset folders must cover all {total_styles} single webp images")
    if list(individual.glob("[0-9][0-9][0-9].webp")) or list(individual.glob("[0-9][0-9][0-9]_grid.webp")):
        fail("flat individual assets must be migrated into categorized folders")
    tweet_sheets = []
    for path in (ROOT / "images").glob("[GHI]_*.webp"):
        parsed = parse_sheet(path)
        if parsed:
            start, end = parsed
            if path.name.startswith("G_") and (start, end) != (201, 216):
                fail("G contact sheets may only cover 201–216")
            if path.name.startswith("H_") and not (217 <= start <= 331):
                fail("H contact sheets must be between 217 and 331")
            if path.name.startswith("I_") and start < 332:
                fail("I contact sheets must start at 332 or later")
            tweet_sheets.append((*parsed, path))
    tweet_sheets.sort()
    expected_tweet_numbers = list(range(201, total_styles + 1))
    listed_tweet_numbers = [number for start, end, _ in tweet_sheets for number in range(start, end + 1)]
    if listed_tweet_numbers != expected_tweet_numbers:
        fail("Tweet contact sheets must cover each 201+ style exactly once")
    if any(end - start + 1 != CAPACITY for start, end, p in tweet_sheets if not (p.name.startswith("H_329-331") or p == tweet_sheets[-1][2])):
        fail("only the final Tweet contact sheet may be incomplete")
    if not STATE_FILE.exists():
        fail("Tweet contact-sheet state is missing")
    sheet_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    last_start, last_end, last_path = tweet_sheets[-1]
    last_filled = last_end - last_start + 1
    expected_next_cell = last_filled + 1 if last_filled < CAPACITY else 1
    if (sheet_state.get("capacity") != CAPACITY or sheet_state.get("active_start") != last_start
            or sheet_state.get("filled") != last_filled or sheet_state.get("next_cell") != expected_next_cell
            or last_path != sheet_path(last_start, last_end)):
        fail("Tweet contact-sheet state does not match the active sheet")
    gallery = (SKILL / "gallery" / "index.html").read_text(encoding="utf-8")
    for cat in CATEGORIES:
        if f'data-group="{cat}"' not in gallery:
            fail(f"gallery does not classify style cards as {cat}")
    for sample_id in ["FA-001", "FB-001", "FC-001", "FD-001", "FE-001", "FF-001", "FG-001", "FH-001", "FI-001", "FC-029", "FG-009"]:
        if f'data-number="{sample_id}"' not in gallery:
            fail(f"gallery style cards missing {sample_id}")
    if '#FA-018' not in gallery:
        fail("gallery style card #FA-018 is missing")
    for token in [".gallery{--columns:14;--gap:8px", "masonry-column", "heights.indexOf(Math.min(...heights))", "ResizeObserver", 'class="style-card"', 'id="gallery"']:
        if token not in gallery:
            fail(f"gallery waterfall layout is missing {token}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "images/A_001-016.webp" not in readme:
        fail("README does not reference representative style preview image")
    if "styles_200_reorganized.md" not in readme:
        fail("README does not link to styles_200_reorganized.md")
    for category_preview in [
        "images/layouts/preview-social-cards.webp",
        "images/layouts/preview-infographics.webp",
        "images/layouts/preview-comic-storyboards.webp",
    ]:
        if category_preview not in readme:
            fail(f"README does not reference layout category preview {category_preview}")
        if not (ROOT / category_preview).is_file():
            fail(f"layout category preview image file is missing: {category_preview}")
    for layout_link in [
        "LAYOUTS.md#social-cards",
        "LAYOUTS.md#infographics",
        "LAYOUTS.md#comic-storyboards",
    ]:
        if layout_link not in readme:
            fail(f"README does not link to layout category {layout_link}")
    if "STYLES.md" not in readme:
        fail("README does not link to STYLES.md")
    if "LAYOUTS.md" not in readme:
        fail("README does not link to LAYOUTS.md")
    styles_md = (ROOT / "STYLES.md").read_text(encoding="utf-8")
    for _, _, path in tweet_sheets:
        if f"images/{path.name}" not in styles_md:
            fail(f"STYLES.md does not reference contact sheet {path.name}")
    prompt_example_tokens = [
        f"风格索引（{total_styles}）",
        'class="prompt-examples"',
        "1 · 出图",
        "2 · 切换图文模式",
        "3 · 海报提示词",
        "风格：FA-001，主题：吃冰淇淋的小姑娘",
        "切换为图文模式",
        "请帮我出海报提示词， 主题：秋分",
        "ui-monospace",
    ]
    if any(token not in gallery for token in prompt_example_tokens):
        fail("gallery count or range is stale")
    version_file = SKILL / "references" / "version.json"
    if not version_file.exists():
        fail("skills/handdraw-style-prompter/references/version.json is missing")
    version_data = json.loads(version_file.read_text(encoding="utf-8"))
    current_version = str(version_data.get("version", ""))
    if not current_version:
        fail("skills/handdraw-style-prompter/references/version.json must specify a version")
    update_tokens = [
        f'data-local-version="{current_version}"',
        "https://raw.githubusercontent.com/yang0/handraw-style/master/skills/handdraw-style-prompter/references/version.json",
        'id="update-status"',
        "checkRepositoryUpdate",
        "isNewerVersion",
        "发现风格库更新",
        "请更新skill https://github.com/yang0/handraw-style",
        "复制更新指令",
    ]
    for token in update_tokens:
        if token not in gallery:
            fail(f"gallery update detection is missing {token}")
    for token in ["本地与仓库均为", "本地版本较新", "未能检查仓库更新", 'id="search"', 'id="recent-styles"']:
        if token in gallery:
            fail(f"gallery must not show non-update status or search UI: {token}")
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for token in ["Style activation policy", "name_activation=strong", "model_capabilities.json", "referenced_image_paths", "Use the attached image only as a style reference", "The user's written theme is the sole source for the image content", "images/individual/{category}/{number}.webp", "FF-001_grid.webp"]:
        if token not in skill_text:
            fail(f"image-reference contract is missing {token}")
    for token in ["preserve the user's theme exactly", "Do not expand, paraphrase, interpret", "show the resolved reference image to the user outside the prompts", "Do not inject it into a `graphic-text` copyable prompt"]:
        if token not in skill_text:
            fail(f"graphic-text prompt contract is missing {token}")
    root_skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for token in ["Session initialization", "任何首次请求", "mcp__codex_app__open_in_codex", "target.type=\"browser\"", "dynamically resolve", "Never open `gallery/index.html` as `target.type=\"file\"`", "当前处于纯图模式，可切换为图文模式。", "Do not repeat the browser call or this first-session status notice", "fallback link"]:
        if token not in skill_text:
            fail(f"session initialization contract in nested SKILL.md is missing {token}")
        if token not in root_skill_text:
            fail(f"session initialization contract in root SKILL.md is missing {token}")
    for token in ['id="preview"', 'class="style-card"', 'dialog.showModal()', 'event.target===dialog']:
        if token not in gallery:
            fail(f"gallery preview interaction is missing {token}")
    result = subprocess.run(python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "18", "--theme", "秋天的第一杯奶茶"], capture_output=True, text=True, encoding="utf-8", check=True)
    for term in ["风格名称：Minimal Deadpan Dialogue Cartoon", "Style name: Minimal Deadpan Dialogue Cartoon", "秋天的第一杯奶茶"]:
        if term not in result.stdout:
            fail(f"prompt output is missing {term}")
    if "#FA-018" in result.stdout.split("中文提示词：")[1]:
        fail("copyable prompt must not contain style number or IDs")
    if "俏皮的手绘线条" in result.stdout or "playful hand-drawn linework" in result.stdout:
        fail("default prompt unexpectedly contains the fixed style anchor")
    if "参考作者/风格名称：Poorly Drawn Lines / Reza Farazmand。" not in result.stdout or "Reference author/style name: Poorly Drawn Lines / Reza Farazmand." not in result.stdout:
        fail("default prompt is missing the author/style name")
    if "当前处于纯图模式，可切换为图文模式。" not in result.stdout:
        fail("default prompt must identify pure-image mode and offer the graphic-text switch")
    graphic_theme = "世界就是个草台班子"
    graphic_text = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "FE-060", "--theme", graphic_theme, "--mode", "graphic-text"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    graphic_bytes = graphic_text.stdout.encode("utf-8")
    suffix_bytes = GRAPHIC_TEXT_SUFFIX.encode("utf-8")
    if graphic_bytes.count(suffix_bytes) != 2:
        fail("graphic-text prompt must preserve the exact suffix once in each language output")
    if "当前处于纯图模式，可切换为图文模式。" in graphic_text.stdout:
        fail("graphic-text prompt must not identify itself as pure-image mode")
    if graphic_text.stdout.count(graphic_theme) != 2:
        fail("graphic-text prompt must preserve the theme verbatim in both language outputs")
    if "临时拼装、摇摇欲坠" in graphic_text.stdout:
        fail("graphic-text prompt must not expand the theme into a scene description")
    graphic_reference = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "FF-001", "--theme", "动画人物", "--mode", "graphic-text"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    if str(grid_path("FF-001")) in graphic_reference.stdout or "参考图：请上传本地参考图" in graphic_reference.stdout or "所附图片仅用于参考画风" in graphic_reference.stdout:
        fail("graphic-text prompt must not expose reference paths or isolation guidance")
    if "核心风格特征：奇想风格化3D卡通美学" not in graphic_reference.stdout:
        fail("graphic-text prompt must retain required positive style traits")
    style_267 = subprocess.run(python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "FE-060", "--theme", "很小的难过"], capture_output=True, text=True, encoding="utf-8", check=True)
    if "核心风格特征：白底中国式极简手绘漫画" not in style_267.stdout or "Core style traits: 白底中国式极简手绘漫画" not in style_267.stdout:
        fail("style FE-060 prompt must include its positive core traits")
    if "参考图：请上传本地参考图" in style_267.stdout or "Reference image: upload local reference image" in style_267.stdout:
        fail("style FE-060 must not require a reference image when traits activation is strong")
    style_217 = subprocess.run(python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "FF-001", "--theme", "动画人物"], capture_output=True, text=True, encoding="utf-8", check=True)
    if ("核心风格特征：奇想风格化3D卡通美学" not in style_217.stdout
            or "参考图：请上传本地参考图" not in style_217.stdout
            or "所附图片仅用于参考画风" not in style_217.stdout):
        fail("reference-required prompt must include traits, local reference path, and isolation guidance")
    invalid = subprocess.run(python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "ZZ-999", "--theme", "x"], capture_output=True, text=True, encoding="utf-8")
    if invalid.returncode == 0 or "not found" not in (invalid.stderr + invalid.stdout):
        fail("out-of-range style does not fail clearly")
    blank_traits = subprocess.run(python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "269", "--theme", "海底世界", "--model", "unregistered-model"], capture_output=True, text=True, encoding="utf-8", check=True)
    if "参考作者/风格名称：社会主义现实主义宣传画。" not in blank_traits.stdout or "Reference author/style name: 社会主义现实主义宣传画." not in blank_traits.stdout:
        fail("blank-trait author/style anchor is missing")
    if "采用该风格的视觉方向" in blank_traits.stdout or "Faithfully render these visual traits" in blank_traits.stdout:
        fail("blank traits were turned into prompt constraints")
    if "参考图：请上传本地参考图" not in blank_traits.stdout or "Reference image: upload local reference image" not in blank_traits.stdout:
        fail("blank-trait reference fallback must provide local reference paths")
    layouts = load_layouts()
    if not {"SC-001", "SC-002", "SC-003", "SC-004", "SC-005", "SC-006", "SC-007", "SC-008", "SC-009", "SC-010", "SC-011", "SC-012", "SC-014", "SC-015", "SC-016", "SC-017", "SC-018", "SC-019", "SC-020", "IG-001", "IG-002", "IG-003", "IG-004", "IG-005", "IG-006", "IG-007", "IG-008", "IG-009"}.issubset({layout["id"] for layout in layouts}):
        fail("layout index does not contain the expected layout IDs")
    for layout in layouts:
        image_path = ROOT / str(layout["image"]).replace("../../../", "")
        if not image_path.is_file():
            fail(f"layout image is missing for {layout['id']}")
        if not layout["prompts"]["zh"] or not layout["prompts"]["en"]:
            fail(f"layout prompt is incomplete for {layout['id']}")
    layout_gallery = (SKILL / "gallery" / "layouts.html").read_text(encoding="utf-8")
    layouts_md = (ROOT / "LAYOUTS.md").read_text(encoding="utf-8")
    layouts_en_md = (ROOT / "LAYOUTS_en.md").read_text(encoding="utf-8")
    for layout in layouts:
        if f"**{layout['id']}**" not in layouts_md:
            fail(f"LAYOUTS.md is missing layout {layout['id']}")
        if f"**{layout['id']}**" not in layouts_en_md:
            fail(f"LAYOUTS_en.md is missing layout {layout['id']}")
    for layout in layouts:
        if layout_gallery.count(f'data-id="{layout["id"]}"') != 1:
            fail(f"layout gallery must contain exactly one card for {layout['id']}")
    for token in ["图型编号画廊", 'href="index.html"', 'href="layouts.html" aria-current="page"', "SC-001", "SC-002", "SC-004", "SC-005", "SC-006", "SC-007", "SC-008", "SC-009", "SC-010", "SC-011", "SC-012", "SC-014", "SC-015", "SC-016", "SC-017", "SC-018", "SC-019", "SC-020", "IG-001", "IG-002", "IG-003", "IG-004", "IG-005", "IG-006", "IG-007", "IG-008", "IG-009", f"信息图 <span>{sum(item['category'] == 'infographic' for item in layouts)}</span>", "复制排版提示词", "navigator.clipboard.writeText", "setCategory('social-card')", ".site-nav a{border:1px solid", "main{max-width:1440px;margin:auto;padding:18px 30px 30px}", ".gallery{--columns:4;--gap:18px", '[data-size="1x"] .gallery{--columns:8;--gap:10px}', "@media(max-width:1100px){.gallery{--columns:3}}", ".masonry-column{display:flex;flex-direction:column", "ResizeObserver", "requestAnimationFrame", "heights.indexOf(Math.min(...heights))", ".layout-card img{display:block;width:100%;height:auto}", 'class="layout-info"', ".layout-id{color:#b74227", ".layout-name{overflow:hidden", "@media(max-width:720px){main{padding:16px 20px 20px}", ".gallery{--columns:2;--gap:12px}", "@media(max-width:420px){.gallery{--columns:1}}"]:
        if token not in layout_gallery:
            fail(f"layout gallery is missing {token}")
    if "信息图 <span>0</span>" in layout_gallery or "id=\"empty\"" in layout_gallery:
        fail("empty infographic category must not be rendered")
    if "aspect-ratio:1;object-fit:cover" in layout_gallery:
        fail("layout gallery must not crop layout thumbnails")
    if "top:10px;left:10px" in layout_gallery:
        fail("layout ID must appear in the card information area, not over the image")
    if "column-width:220px" in layout_gallery or "display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr))" in layout_gallery:
        fail("layout gallery must use explicit responsive masonry columns")
    if '.site-nav a{border:1px solid' not in gallery or 'main{max-width:1440px;margin:auto;padding:18px 30px 30px}' not in gallery:
        fail("style gallery navigation or title spacing is stale")
    layout_zh = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--layout", "IG-007", "--theme", "秋天的第一杯奶茶"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    if "图型：粗体标题标签小图卡。" not in layout_zh.stdout or "自动使用图文模式" not in layout_zh.stdout or GRAPHIC_TEXT_SUFFIX not in layout_zh.stdout:
        fail("Chinese layout-only prompt is missing its layout contract or stacked graphic-text suffix")
    layout_en = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--layout", "IG-007", "--style", "18", "--theme", "Autumn's first milk tea"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    for term in ["Layout: Bold Headline Tag Cards.", "Theme: Autumn's first milk tea.", "Style name: Minimal Deadpan Dialogue Cartoon.", GRAPHIC_TEXT_SUFFIX]:
        if term not in layout_en.stdout:
            fail(f"English layout-and-style prompt is missing {term}")
    invalid_layout = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--layout", "SC-999", "--theme", "x"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if invalid_layout.returncode == 0 or "Unknown layout ID" not in (invalid_layout.stderr + invalid_layout.stdout):
        fail("unknown layout ID does not fail clearly")
    missing_selection = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--theme", "x"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if missing_selection.returncode == 0 or "Provide --style, --layout, or both" not in (missing_selection.stderr + missing_selection.stdout):
        fail("missing style/layout selection does not fail clearly")

    colors_file = SKILL / "references" / "colors.json"
    if not colors_file.exists():
        fail("colors.json is missing")
    colors = json.loads(colors_file.read_text(encoding="utf-8"))
    if len(colors) != 36:
        fail(f"colors.json must contain exactly 36 colors, got {len(colors)}")
    expected_color_ids = [f"C-{i:02d}" for i in range(1, 37)]
    if [c["id"] for c in colors] != expected_color_ids:
        fail("color IDs must be continuous C-01 to C-36")
    for c in colors:
        c_img = ROOT / str(c["image"]).replace("../../../", "")
        if not c_img.is_file():
            fail(f"color image is missing for {c['id']}: {c_img}")
        sheet_img = ROOT / str(c["sheet_image"]).replace("../../../", "")
        if not sheet_img.is_file():
            fail(f"color sheet image is missing for {c['id']}: {sheet_img}")
        for field in ("name_zh", "name_en", "quote_zh", "quote_en", "prompt_zh", "prompt_en"):
            if not c.get(field):
                fail(f"color {c['id']} missing field {field}")

    color_gallery = (SKILL / "gallery" / "colors.html").read_text(encoding="utf-8")
    for c in colors:
        if f'data-id="{c["id"]}"' not in color_gallery:
            fail(f"color gallery must contain card for {c['id']}")
    for token in ['href="index.html"', 'href="layouts.html"', 'href="colors.html" aria-current="page"', "copyText", "navigator.clipboard.writeText"]:
        if token not in color_gallery:
            fail(f"color gallery is missing {token}")

    colors_md = (ROOT / "COLORS.md").read_text(encoding="utf-8")
    colors_en_md = (ROOT / "COLORS_en.md").read_text(encoding="utf-8")
    for c in colors:
        if f"**{c['id']}**" not in colors_md:
            fail(f"COLORS.md is missing color {c['id']}")
        if f"**{c['id']}**" not in colors_en_md:
            fail(f"COLORS_en.md is missing color {c['id']}")
    if "COLORS.md" not in readme or "images/colors/sheet_01.webp" not in readme:
        fail("README.md must reference COLORS.md and images/colors/sheet_01.webp")
    readme_en = (ROOT / "README_en.md").read_text(encoding="utf-8")
    if "COLORS_en.md" not in readme_en or "images/colors/sheet_01.webp" not in readme_en:
        fail("README_en.md must reference COLORS_en.md and images/colors/sheet_01.webp")

    color_style_res = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--style", "18", "--color", "C-01", "--theme", "秋天的第一杯奶茶"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    if "主题色：克莱因蓝（Klein Blue）。" not in color_style_res.stdout or "Theme color: Klein Blue." not in color_style_res.stdout:
        fail("style-and-color prompt is missing expected theme color tokens")

    color_only_res = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--color", "C-01", "--theme", "秋天的第一杯奶茶"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    if "主题色：克莱因蓝（Klein Blue）。" not in color_only_res.stdout:
        fail("color-only prompt is missing expected theme color token")

    color_by_name = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--color", "克莱因蓝", "--theme", "秋天的第一杯奶茶"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    if "主题色：克莱因蓝（Klein Blue）。" not in color_by_name.stdout:
        fail("color by name prompt is missing expected theme color token")

    invalid_color = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--color", "C-999", "--theme", "x"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if invalid_color.returncode == 0 or "Unknown color ID" not in (invalid_color.stderr + invalid_color.stdout):
        fail("unknown color ID does not fail clearly")

    auto_res = subprocess.run(
        python + [str(SKILL / "scripts" / "prompt_style.py"), "--theme", "秋天的第一杯奶茶", "--auto"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    if "💡 推荐理由" not in auto_res.stdout or "Selected style:" not in auto_res.stdout or "Selected color:" not in auto_res.stdout:
        fail("auto recommendation output is missing expected banner, style, or color")

    tutorials_file = ROOT / "TUTORIALS.md"
    tutorials_en_file = ROOT / "TUTORIALS_en.md"
    if not tutorials_file.exists():
        fail("TUTORIALS.md is missing")
    if not tutorials_en_file.exists():
        fail("TUTORIALS_en.md is missing")
    tutorials_md = tutorials_file.read_text(encoding="utf-8")
    tutorials_en_md = tutorials_en_file.read_text(encoding="utf-8")
    if "TUTORIALS.md" not in readme:
        fail("README.md must reference TUTORIALS.md")
    if "TUTORIALS_en.md" not in readme_en:
        fail("README_en.md must reference TUTORIALS_en.md")
    for technique in ["技巧一：万能海报思维法", "技巧二：智能抽卡", "技巧三：精准组装法", "技巧四：图文模式"]:
        if technique not in tutorials_md:
            fail(f"TUTORIALS.md missing {technique}")
    for technique_en in [
        "Tip 1: The Universal Poster Mindset",
        "Tip 2: Style Gacha",
        "Tip 3: The Precise Assembly Method",
        "Tip 4: Graphic-Text Mode",
    ]:
        if technique_en not in tutorials_en_md:
            fail(f"TUTORIALS_en.md missing {technique_en}")

    tutorials_gallery_file = SKILL / "gallery" / "tutorials.html"
    if not tutorials_gallery_file.exists():
        fail("tutorials.html is missing")
    tutorial_gallery = tutorials_gallery_file.read_text(encoding="utf-8")
    for token in ['href="index.html"', 'href="layouts.html"', 'href="colors.html"', 'href="tutorials.html" aria-current="page"', "copy-btn", "navigator.clipboard.writeText", "tutorial-card", "formula-box", "tutorials-list"]:
        if token not in tutorial_gallery:
            fail(f"tutorial gallery is missing {token}")

    if 'href="tutorials.html"' not in gallery:
        fail("style gallery is missing link to tutorials.html")
    if 'href="tutorials.html"' not in layout_gallery:
        fail("layout gallery is missing link to tutorials.html")
    if 'href="tutorials.html"' not in color_gallery:
        fail("color gallery is missing link to tutorials.html")

    characters_file = SKILL / "references" / "characters.json"
    if not characters_file.exists():
        fail("characters.json is missing")
    characters = json.loads(characters_file.read_text(encoding="utf-8"))
    if not any(c["id"] == "CH-001" for c in characters):
        fail("CH-001 preset character is missing in characters.json")
    for c in characters:
        c_img = ROOT / str(c["image"]).replace("../../../", "")
        if not c_img.is_file():
            fail(f"character image is missing for {c['id']}: {c_img}")

    props_file = SKILL / "references" / "props.json"
    if not props_file.exists():
        fail("props.json is missing")
    scenes_file = SKILL / "references" / "scenes.json"
    if not scenes_file.exists():
        fail("scenes.json is missing")

    assets_gallery_file = SKILL / "gallery" / "assets.html"
    if not assets_gallery_file.exists():
        fail("assets.html is missing")
    assets_gallery = assets_gallery_file.read_text(encoding="utf-8")
    for token in ['href="index.html"', 'href="layouts.html"', 'href="colors.html"', 'href="assets.html" aria-current="page"', 'href="tutorials.html"', "CH-001", "IP-002", "init-notice-banner", "guide-steps-list", 'data-tab="characters"', 'data-tab="props"', 'data-tab="scenes"', "preview-dialog"]:
        if token not in assets_gallery:
            fail(f"assets gallery is missing {token}")
    if "select-dir-btn" in assets_gallery or "add-char-btn" in assets_gallery:
        fail("assets gallery should not contain directory selection or web import form")
    if 'src="../../../images/custom/custom_assets.js"' not in assets_gallery:
        fail("assets.html must load isolated custom_assets.js loader")
    if 'src="../../../images/custom/custom_assets.js"' not in tutorial_gallery:
        fail("tutorials.html must load isolated custom_assets.js loader")

    # Assert that no private local custom assets ever leak into git-tracked HTML files
    import re
    custom_leak_pattern = re.compile(r'\b(CH-00[2-9]|CH-0[1-9][0-9]|PR-\d{3}|SCN-\d{3})\b|images/custom/(characters|props|scenes)/')
    for html_file in [assets_gallery_file, tutorials_gallery_file]:
        html_text = html_file.read_text(encoding="utf-8")
        leaks = custom_leak_pattern.findall(html_text)
        if leaks:
            fail(f"Local custom asset leaked into git-tracked {html_file.name}: {leaks}")

    characters_redirect_file = SKILL / "gallery" / "characters.html"
    if not characters_redirect_file.exists():
        fail("characters.html redirect is missing")
    if 'url=assets.html' not in characters_redirect_file.read_text(encoding="utf-8"):
        fail("characters.html must redirect to assets.html")

    if 'href="assets.html"' not in gallery:
        fail("style gallery is missing link to assets.html")
    if 'href="assets.html"' not in layout_gallery:
        fail("layout gallery is missing link to assets.html")
    if 'href="assets.html"' not in color_gallery:
        fail("color gallery is missing link to assets.html")
    if 'href="assets.html"' not in tutorial_gallery:
        fail("tutorial gallery is missing link to assets.html")


    import yaml
    for sf in [
        ROOT / "SKILL.md",
        SKILL / "SKILL.md",
        ROOT / "skills" / "article-illustration-planner" / "SKILL.md",
        ROOT / "skills" / "poster-prompt-generator" / "SKILL.md",
        ROOT / "skills" / "article-cover-designer" / "SKILL.md",
        ROOT / "skills" / "style-fusion-prompter" / "SKILL.md",
        ROOT / "skills" / "custom-asset-manager" / "SKILL.md",
        ROOT / "skills" / "ip-designer" / "SKILL.md",
        ROOT / "skills" / "couple-photo-orchestrator" / "SKILL.md",
    ]:
        if sf.exists():
            content = sf.read_text(encoding="utf-8")
            if not content.startswith("---"):
                fail(f"{sf.name} does not start with YAML frontmatter delimiter '---'")
            parts = content.split("---", 2)
            if len(parts) < 3:
                fail(f"{sf.name} missing closing YAML frontmatter delimiter '---'")
            try:
                fm = yaml.safe_load(parts[1])
                if not isinstance(fm, dict) or "name" not in fm or "description" not in fm:
                    fail(f"{sf.name} frontmatter missing required name or description")
            except Exception as e:
                fail(f"YAML frontmatter error in {sf.name}: {e}")

    import re
    drive_leak_pattern = re.compile(r'(?<!https:)(?<!http:)\b[A-Za-z]:[\\/]|file:///[A-Za-z]:')
    git_files = subprocess.run(["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", check=True).stdout.splitlines()
    for rel_path in git_files:
        file_path = ROOT / rel_path
        if file_path.suffix in (".md", ".json", ".py", ".html", ".yaml", ".yml") and file_path.exists():
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), 1):
                if re.search(r'path[\\/]+to', line, re.I):
                    continue
                if drive_leak_pattern.search(line):
                    fail(f"Local drive path leaked in tracked file {rel_path}:{line_no}: {line.strip()[:100]}")

    print(f"PASS: {total_styles} styles, {len(layouts)} layouts, {len(colors)} colors, {len(characters)} preset characters, custom assets library (characters/props/scenes), tutorials section, gallery coverage, prompt contract, YAML frontmatter, path leak guard, and invalid-ID guards.")


if __name__ == "__main__":
    main()
