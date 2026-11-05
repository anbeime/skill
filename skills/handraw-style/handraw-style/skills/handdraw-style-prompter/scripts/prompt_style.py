#!/usr/bin/env python3
"""Create a deterministic bilingual prompt draft from a validated style number."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from layout_library import detect_language, resolve_layout
from resolve_reference import resolve

SKILL = Path(__file__).resolve().parents[1]

REFERENCE_ISOLATION_ZH = (
    "所附图片仅用于参考画风。只提取参考图的风格特征，例如线条、笔触、媒介、材质、色彩倾向和整体视觉语言；"
    "不要使用、复制或延续参考图中的任何主体、人物、动物、服装、道具、动作、姿态、场景、背景、构图、布局、文字或故事。"
    "最终画面内容完全以用户提供的主题为准。"
)
REFERENCE_ISOLATION_EN = (
    "Use the attached image only as a style reference. Extract only its stylistic qualities, such as linework, brushwork, medium, "
    "material texture, color tendencies, and overall visual language. Do not use, copy, or carry over any subject, person, animal, "
    "clothing, prop, action, pose, setting, background, composition, layout, text, or story from the reference image. "
    "The user's written theme is the sole source for the image content."
)
GRAPHIC_TEXT_SUFFIX = "【如果主题直白包含画面元素那就按主题出图，文案由你来升华，但是不要直接描述画面。 如果主题比较概念化，那么文案和主题尽量保持一致，如果文案较长由你提炼，由你先设计画面隐喻（人类和非人类都行）再出图   。    文字参与构图，图文一体】"
REDRAW_INSTRUCTION_ZH = "【请只提取人物的五官特征和姿态，场景轮廓，在画风上严格按 选择的风格重新画，不要在原照片上加质感。】"
REDRAW_INSTRUCTION_EN = "[Extract only the character's facial features and posture, and the scene contours. Strictly redraw from scratch according to the selected style; do not add texture or filters onto the original photo.]"


def resolve_single_color(query_str: str, colors_list: list[dict]) -> dict[str, str]:
    q = query_str.strip().lower()
    is_id_pattern = q.startswith("c-")
    q_num = q.replace("c-", "").lstrip("0") if is_id_pattern else ""
    for c in colors_list:
        cid = c["id"].lower()
        c_num = cid.replace("c-", "").lstrip("0")
        if q == cid or (q_num and q_num == c_num) or q in c["name_zh"].lower() or q in c["name_en"].lower():
            return c
    if is_id_pattern:
        raise ValueError(f"Unknown color ID: {query_str}. Use a listed C-01 to C-36 identifier or color name.")
    name = query_str.strip()
    return {
        "id": "",
        "name_zh": name,
        "name_en": name,
        "prompt_zh": f"主题色：{name}。",
        "prompt_en": f"Theme color: {name}."
    }


def resolve_color(query_str: str) -> dict[str, str]:
    colors_file = SKILL / "references" / "colors.json"
    colors_list = json.loads(colors_file.read_text(encoding="utf-8")) if colors_file.exists() else []
    import re
    tokens = [t.strip() for t in re.split(r'[,+、/]+', query_str) if t.strip()]
    if len(tokens) <= 1:
        return resolve_single_color(query_str, colors_list)

    resolved = [resolve_single_color(t, colors_list) for t in tokens]
    c_ids = [r["id"] for r in resolved if r.get("id")]
    id_str = " + ".join(c_ids) if c_ids else ""
    zh_names = [f"{r['name_zh']}（{r['name_en']}）" if r.get('name_en') else r['name_zh'] for r in resolved]
    en_names = [r['name_en'] for r in resolved]

    if len(resolved) == 2:
        prompt_zh = f"主题色：主色为{resolved[0]['name_zh']}（{resolved[0]['name_en']}），点缀色为{resolved[1]['name_zh']}（{resolved[1]['name_en']}）。"
        prompt_en = f"Theme color: {resolved[0]['name_en']} as primary tone, accented with {resolved[1]['name_en']}."
    else:
        prompt_zh = f"主题色：{' 搭配 '.join(zh_names)}。"
        prompt_en = f"Theme color: {' paired with '.join(en_names)}."

    return {
        "id": id_str,
        "name_zh": " 搭配 ".join(r["name_zh"] for r in resolved),
        "name_en": " + ".join(en_names),
        "prompt_zh": prompt_zh,
        "prompt_en": prompt_en,
    }


def resolve_style_entry(style_input: str, styles: list[dict]) -> tuple[dict, str]:
    import re
    alias_file = SKILL / "references" / "style_alias_map.json"
    alias_map = json.loads(alias_file.read_text(encoding="utf-8")) if alias_file.exists() else {}
    legacy_to_new = alias_map.get("legacy_to_new", {})

    style_clean = str(style_input).strip()
    if style_clean.isdigit():
        num_str = f"{int(style_clean):03}"
        canonical = legacy_to_new.get(num_str, num_str)
    else:
        m = re.match(r"^([A-Za-z]{2})[-_]?(\d+)$", style_clean)
        if m:
            canonical = f"{m.group(1).upper()}-{int(m.group(2)):03}"
        else:
            canonical = style_clean.upper()

    s_obj = next((s for s in styles if s["number"] == canonical), None)
    if not s_obj and canonical in legacy_to_new:
        canonical = legacy_to_new[canonical]
        s_obj = next((s for s in styles if s["number"] == canonical), None)

    if not s_obj:
        raise ValueError(f"Style '{style_input}' not found. Use a valid ID like FA-001 or legacy number 001-365.")
    return s_obj, canonical


def recommend_combination(theme: str, user_style: str | None, user_color: str | None) -> tuple[str, str, str]:
    """
    Dynamic whole-library recommendation engine across all 368 styles and 36 theme colors.
    Note: In AI agent workflows (Codex, Antigravity, Claude Code), the LLM dynamically reasons
    and evaluates styles and colors at runtime. This function provides a robust, non-hardcoded
    heuristic scoring fallback for offline and CLI usage.
    """
    import re
    t = theme.lower().strip()
    styles_file = SKILL / "references" / "styles.json"
    styles = json.loads(styles_file.read_text(encoding="utf-8")) if styles_file.exists() else []
    colors_file = SKILL / "references" / "colors.json"
    colors = json.loads(colors_file.read_text(encoding="utf-8")) if colors_file.exists() else []

    ngrams = [t[i:i+n] for n in (2, 3, 4) for i in range(len(t)-n+1)]
    words = re.findall(r'[a-zA-Z0-9]+|[\u4e00-\u9fa5]', t)

    # 1. Dynamically resolve style from full 368 styles library
    if user_style:
        try:
            s_obj, final_style = resolve_style_entry(user_style, styles)
        except ValueError:
            s_obj = styles[0]
            final_style = s_obj["number"]
    else:
        scored_styles = []
        for s in styles:
            score = 0
            text_name = (s["generation_name"] + " " + s["reference"]).lower()
            text_traits = s["traits"].lower()
            text_group = s.get("group", "").lower()
            if t in text_name or t in text_traits:
                score += 25
            for ng in ngrams:
                if ng in text_name:
                    score += 8
                if ng in text_traits:
                    score += 4
                if ng in text_group:
                    score += 2
            for w in words:
                if len(w) > 1:
                    if w in text_name:
                        score += 6
                    if w in text_traits:
                        score += 3
            scored_styles.append((score, s))
        scored_styles.sort(key=lambda x: x[0], reverse=True)
        if scored_styles and scored_styles[0][0] > 0:
            s_obj = scored_styles[0][1]
        else:
            idx = sum(ord(c) * (i + 1) for i, c in enumerate(t)) % len(styles) if styles else 0
            s_obj = styles[idx] if styles else {"number": "001", "generation_name": "Style", "reference": "Artist", "traits": ""}
        final_style = s_obj["number"]

    # 2. Dynamically resolve color from full 36 colors library
    if user_color:
        final_color = user_color
        color_desc = user_color
    else:
        style_text = (s_obj["traits"] + " " + s_obj["generation_name"] + " " + s_obj.get("group", "")).lower()
        scored_colors = []
        for c in colors:
            c_score = 0
            c_haystack = (c["name_zh"] + " " + c["name_en"] + " " + c.get("category_zh", "") + " " + c.get("quote_zh", "")).lower()
            for ng in ngrams:
                if ng in c_haystack:
                    c_score += 10
            for w in words:
                if len(w) > 1 and w in c_haystack:
                    c_score += 6
            for trait_word in ["蓝", "绿", "红", "橙", "黄", "紫", "粉", "黑", "白", "灰", "金", "墨", "暖", "冷", "自然", "科技", "幽默"]:
                if trait_word in style_text and trait_word in c_haystack:
                    c_score += 5
            scored_colors.append((c_score, c))
        scored_colors.sort(key=lambda x: x[0], reverse=True)
        primary = scored_colors[0][1] if (scored_colors and scored_colors[0][0] > 0) else (colors[sum(ord(c) for c in t) % len(colors)] if colors else {"id": "C-01", "name_zh": "克莱因蓝"})

        accent = None
        for sc, c in scored_colors[1:]:
            if c.get("category") != primary.get("category"):
                accent = c
                break
        if not accent and colors:
            accent = colors[(colors.index(primary) + 7) % len(colors)]

        if accent and accent["id"] != primary["id"]:
            final_color = f"{primary['id']} + {accent['id']}"
            color_desc = f"{primary['name_zh']} ({primary['id']}) + {accent['name_zh']} ({accent['id']})"
        else:
            final_color = primary["id"]
            color_desc = f"{primary['name_zh']} ({primary['id']})"

    s_name = s_obj.get("generation_name", "")
    s_ref = s_obj.get("reference", "")
    first_trait = s_obj.get("traits", "").split("；")[0].split("。")[0]

    if user_style and user_color:
        rationale = f"已采用您指定的手绘风格 #{user_style} 与主题色 {user_color}。"
    elif user_style:
        rationale = f"已采用您指定的手绘风格 #{user_style}（{s_ref} · {s_name}），基于主题意境为您全库动态匹配推荐主题色 {color_desc}。"
    elif user_color:
        rationale = f"已采用您指定的主题色 {user_color}，基于主题意境为您全库动态匹配推荐手绘风格 #{final_style}（{s_ref} · {s_name}）。"
    else:
        rationale = f"基于「{theme}」的主题意境，全库动态匹配手绘风格 #{final_style}（{s_ref} · {s_name}），搭配主题色 {color_desc}。以{first_trait}契合画面的视觉与情绪诉求。"

    return final_style, final_color, rationale


def main() -> None:
    styles = json.loads((SKILL / "references" / "styles.json").read_text(encoding="utf-8"))
    max_num = len(styles)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", help=f"Optional style number from 001 to {max_num:03}")
    parser.add_argument("--layout", help="Optional layout ID")
    parser.add_argument("--color", help="Optional color ID  or color name.")
    parser.add_argument("--auto", "--recommend", action="store_true", help="Automatically recommend an optimal style and theme color combination based on theme semantics.")
    parser.add_argument("--theme", default="", help="Optional theme description; defaults to placeholder if omitted.")
    parser.add_argument("--ratio")
    parser.add_argument("--subject")
    parser.add_argument("--text")
    parser.add_argument("--model", default="gpt-image-2", help="Model capability profile; defaults to gpt-image-2.")
    parser.add_argument("--mode", choices=("pure-image", "graphic-text"), default="pure-image")
    parser.add_argument("--redraw", action="store_true", help="Append photo-to-art redraw instruction to prevent photo filters.")
    parser.add_argument("--language", choices=("auto", "zh", "en"), default="auto")
    args = parser.parse_args()

    if not args.theme:
        args.theme = "【请在此输入画面主题，或在生图模型中垫入你的照片】" if args.language != "en" else "[Enter theme here, or attach your photo in the image AI]"

    recommendation_banner = None
    if args.auto:
        rec_s, rec_c, rationale = recommend_combination(args.theme, args.style, args.color)
        if not args.style:
            args.style = rec_s
        if not args.color:
            args.color = rec_c
        recommendation_banner = rationale
    elif not args.style and not args.layout and not args.color:
        raise SystemExit("Provide --style, --layout, or both (or --color, or use --auto).")
    if args.color:
        try:
            color_info = resolve_color(args.color)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        color_info = None
    selected = None
    number = None
    if args.style:
        try:
            selected, number = resolve_style_entry(args.style, styles)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    extra_zh = "；".join(filter(None, [f"画幅：{args.ratio}" if args.ratio else "", f"主体限制：{args.subject}" if args.subject else "", f"文字要求：{args.text}" if args.text else ""]))
    extra_en = "; ".join(filter(None, [f"aspect ratio: {args.ratio}" if args.ratio else "", f"subject constraints: {args.subject}" if args.subject else "", f"text requirement: {args.text}" if args.text else ""]))
    if args.layout:
        try:
            layout = resolve_layout(args.layout)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        language = detect_language(args.theme) if args.language == "auto" else args.language
        layout_prompt = layout["prompts"][language]
        if language == "zh":
            parts = [
                f"图型：{layout['name']}。",
                f"主题：{args.theme}。",
                f"排版要求：{layout_prompt}",
            ]
        else:
            layout_name = layout.get("name_en") or layout["name"]
            parts = [
                f"Layout: {layout_name}.",
                f"Theme: {args.theme}.",
                f"Layout instructions: {layout_prompt}",
            ]
        is_ecommerce = layout.get("category") == "ecommerce" or layout["id"].startswith("EC-")
        if color_info:
            color_prompt = color_info["prompt_zh"] if language == "zh" else color_info["prompt_en"]
            parts.insert(1, color_prompt)
        # For e-commerce layouts, do not stitch style by default; only include if user explicitly passed --style
        if selected and number and (not is_ecommerce or args.style):
            decision = resolve(args.model, number)
            traits = decision["prompt_traits"]
            if language == "zh":
                parts.append(f"风格名称：{selected['generation_name']}。参考作者/风格名称：{selected['reference']}。")
                if traits:
                    parts.append(f"核心风格特征：{traits}。")
            else:
                parts.append(f"Style name: {selected['generation_name']}. Reference author/style name: {selected['reference']}.")
                if traits:
                    parts.append(f"Core style traits: {traits}.")
        if args.redraw:
            if language == "zh":
                parts.append(REDRAW_INSTRUCTION_ZH)
            else:
                parts.append(REDRAW_INSTRUCTION_EN)
        if language == "zh":
            if extra_zh:
                parts.append(f"；{extra_zh}")
            if not is_ecommerce:
                parts.append(GRAPHIC_TEXT_SUFFIX)
        else:
            if extra_en:
                parts.append(f"{extra_en}.")
            if not is_ecommerce:
                parts.append(GRAPHIC_TEXT_SUFFIX)
        if recommendation_banner:
            print(f"💡 推荐理由：{recommendation_banner}")
        print(f"Selected layout: {layout['id']} · {layout['name']}")
        if color_info:
            c_label = f"{color_info['id']} · " if color_info.get("id") else ""
            print(f"Selected color: {c_label}{color_info['name_zh']} ({color_info['name_en']})")
        if selected and number and (not is_ecommerce or args.style):
            print(f"Selected style: #{number} · {selected['generation_name']}")
        print("\nPrompt:")
        print("".join(parts) if language == "zh" else " ".join(parts))
        if not is_ecommerce:
            print("\n已自动使用图文模式。" if language == "zh" else "\nThe selected layout automatically uses graphic-text mode.")
        return

    graphic_text_suffix = GRAPHIC_TEXT_SUFFIX if args.mode == "graphic-text" else ""
    zh_extra = f"；{extra_zh}" if extra_zh else ""
    en_extra = f" {extra_en}." if extra_en else ""
    redraw_zh = REDRAW_INSTRUCTION_ZH if args.redraw else ""
    redraw_en = f" {REDRAW_INSTRUCTION_EN}" if args.redraw else ""

    if not selected and color_info:
        c_label = f"{color_info['id']} · " if color_info.get("id") else ""
        print(f"Selected color: {c_label}{color_info['name_zh']} ({color_info['name_en']})")
        print("\n中文提示词：")
        print(f"{color_info['prompt_zh']}主题：{args.theme}。{zh_extra}{redraw_zh}{graphic_text_suffix}")
        print("\nEnglish prompt:")
        print(f"{color_info['prompt_en']} Theme: {args.theme}.{en_extra}{redraw_en}{graphic_text_suffix}")
        print("\nPaste either prompt into an image AI; this skill does not generate an image.")
        if args.mode == "pure-image":
            print("当前处于纯图模式，可切换为图文模式。")
        return

    assert selected is not None and number is not None
    if recommendation_banner:
        print(f"💡 推荐理由：{recommendation_banner}")
    print(f"Selected style: #{number} · {selected['generation_name']}")
    if color_info:
        c_label = f"{color_info['id']} · " if color_info.get("id") else ""
        print(f"Selected color: {c_label}{color_info['name_zh']} ({color_info['name_en']})")
    print("\n中文提示词：")
    reference_zh = f"参考作者/风格名称：{selected['reference']}。"
    reference_en = f" Reference author/style name: {selected['reference']}."
    decision = resolve(args.model, number)
    traits = decision["prompt_traits"]
    traits_zh = f"核心风格特征：{traits}。" if traits else ""
    traits_en = f" Core style traits: {traits}." if traits else ""
    reference_image_zh = ""
    reference_image_en = ""
    if decision["use_reference_image"] and args.mode == "pure-image":
        if decision.get("reference_path"):
            reference_image_zh = f"参考图：请上传本地参考图 {decision['reference_path']}。{REFERENCE_ISOLATION_ZH}"
            reference_image_en = f" Reference image: upload local reference image {decision['reference_path']}. {REFERENCE_ISOLATION_EN}"
        else:
            reference_image_zh = f"参考图：{REFERENCE_ISOLATION_ZH}"
            reference_image_en = f" Reference image: {REFERENCE_ISOLATION_EN}"
    color_zh = f"{color_info['prompt_zh']}" if color_info else ""
    color_en = f" {color_info['prompt_en']}" if color_info else ""
    print(f"风格名称：{selected['generation_name']}。{color_zh}主题：{args.theme}。{reference_zh}{traits_zh}{reference_image_zh}{zh_extra}{redraw_zh}{graphic_text_suffix}")
    print("\nEnglish prompt:")
    print(f"Style name: {selected['generation_name']}.{color_en} Theme: {args.theme}.{reference_en}{traits_en}{reference_image_en}{en_extra}{redraw_en}{graphic_text_suffix}")
    print("\nPaste either prompt into an image AI; this skill does not generate an image.")
    if args.mode == "pure-image":
        print("当前处于纯图模式，可切换为图文模式。")


if __name__ == "__main__":
    main()
