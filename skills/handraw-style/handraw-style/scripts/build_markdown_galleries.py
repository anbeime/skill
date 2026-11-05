#!/usr/bin/env python3
"""Generate bilingual STYLES.md and LAYOUTS.md for GitHub-native visual browsing."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "handdraw-style-prompter"
SOURCE_MD = ROOT / "styles_200_reorganized.md"
LAYOUTS_JSON = SKILL / "references" / "layouts.json"
COLORS_JSON = SKILL / "references" / "colors.json"

STYLES_JSON = SKILL / "references" / "styles.json"
ALIAS_MAP_FILE = SKILL / "references" / "style_alias_map.json"

STYLE_CATEGORIES = [
    ("FA", "国际社论幽默", "Editorial & Humor Doodle",
     "适合日常幽默、讽刺随笔、都市观察与生活吐槽。以松散线条、冷面幽默与鲜明人物轮廓为主要特征。",
     "Ideal for everyday humor, editorial satire, urban commentary, and deadpan comics. Features loose lines, deadpan humor, and distinctive character silhouettes."),
    ("FB", "经典绘本叙事", "Picture Book & Watercolor",
     "适合温情叙事、儿童插画、治愈绘本与水彩手账。以经典手绘质感、细腻笔触与叙事氛围为主要特征。",
     "Ideal for heartwarming narratives, children's picture books, healing watercolors, and illustrated journals. Features rich hand-drawn textures and storytelling atmosphere."),
    ("FC", "现代平面艺术", "Modern Graphic & Pop",
     "适合现代平面广告、波普艺术、时尚杂志与高饱和海报。以醒目色块、现代构成与矢量平面为主要特征。",
     "Ideal for modern graphic design, pop art, editorial fashion, and bold posters. Features clean vectors, dynamic color blocking, and contemporary graphic shapes."),
    ("FD", "日本当代插画", "Japanese Contemporary & Manga",
     "适合日系当代插画、轻小说插画、城市散策与唯美空气感。以日系干净线条、空气透视与独特人物形体为主要特征。",
     "Ideal for Japanese contemporary illustration, light novel art, city strolls, and atmospheric scenes. Features delicate line art, airy perspective, and stylized character silhouettes."),
    ("FE", "新国风与传统工艺", "Chinese Traditional & Folk Craft",
     "适合国潮国风、非遗工艺、传统节日与典雅东方题材。以工笔白描、重彩壁画、剪纸皮影与水墨丹青为主要特征。",
     "Ideal for Chinese aesthetics, intangible cultural heritage, traditional festivals, and oriental art. Features fine-brush gongbi, Dunhuang murals, folk papercuts, and ink wash painting."),
    ("FF", "3D黏土毛毡与纸雕", "3D Clay, Felt & Papercraft",
     "适合萌系手工、定格动画感、童趣立体与材质艺术。以手工黏土捏塑、针织毛毡、立体纸雕与真实微缩质感为主要特征。",
     "Ideal for handmade craft visuals, stop-motion animation textures, playful dimensional art, and papercraft. Features handcrafted clay sculptures, needle felt, and 3D paper reliefs."),
    ("FG", "动漫和赛璐璐", "Anime, Cel Animation & Retro Game",
     "适合热血动漫、复古赛璐璐、像素街机与漫改场景。以经典赛璐璐光影、清晰分镜线稿与黄金时代动漫质感为主要特征。",
     "Ideal for action anime, classic cel animation, retro pixel art, and manga adaptations. Features vintage cel shading, crisp dynamic lines, and golden-age anime nostalgia."),
    ("FH", "先锋实验与综合媒介", "Mixed Media & Impasto Arts",
     "适合实验艺术、先锋插画、综合材料拼贴与厚涂重彩。以肌理笔触、混合媒介、粗粝质感与强烈个性化表达为主要特征。",
     "Ideal for experimental visuals, avant-garde illustration, mixed-media collage, and heavy impasto. Features expressive brushwork, tactile mixed media, and bold creative statements."),
    ("FI", "写实摄影与视觉大片", "Realistic, Photography & Cinematic Styles",
     "适合品牌商摄、高级时尚大片、人文纪实摄影与电影大师视觉。以精准布光、电影级构图、光影层次与真实质感为主要特征。",
     "Ideal for brand commercial photography, haute couture fashion editorials, humanist documentary, and cinematic master visuals. Features precise lighting, cinematic framing, rich light-shadow dynamics, and authentic realism."),
]

LAYOUT_CATEGORIES = [
    ("social-card", "1. 社媒卡（19 种）", "1. Social Cards (19 Layouts)",
     "适合小红书、朋友圈、公众号配图及观点金句卡片。结构包含上下图文、文案主导、双格对照等。",
     "Ideal for Xiaohongshu, Instagram, newsletter hero images, and quote cards. Includes top-bottom split, text-driven cards, two-column contrasts, and sticky notes."),
    ("infographic", "2. 信息图（31 种）", "2. Infographics (31 Layouts)",
     "适合知识科普、对比清单、流程步骤及数据架构展示。结构包含金字塔层级、中心主图标注、多行多列对比等。",
     "Ideal for knowledge sharing, comparison charts, process workflows, and structured data visuals. Includes hierarchy pyramids, central icons, matrices, and multi-column comparison tables."),
    ("comic-storyboard", "3. 漫画分镜（68 种）", "3. Comic Storyboards (68 Layouts)",
     "适合多格叙事、剧情转折、条漫分镜及动态视觉表现。结构包含规则四格、起承转合、大格冲击、对角切割等专业分镜。",
     "Ideal for multi-panel narratives, webtoons, emotional storylines, and cinematic pacing. Includes standard 4-panel grids, dramatic wide-angle focus, diagonal cuts, and manga storyboards."),
    ("ip-character", "4. IP设计（1 种）", "4. IP Design (1 Layouts)",
     "适合 IP 形象设计、吉祥物定位卡、角色档案及形象规范展示。结构包含主形象大图、定位金句、受众画像与多视角展示。",
     "Ideal for IP character design, mascot positioning cards, character profiles, and specification guides. Includes hero character showcase, positioning slogans, audience profiles, and multi-angle views."),
]


def build_styles_md() -> None:
    styles = json.loads(STYLES_JSON.read_text(encoding="utf-8"))
    alias_data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8")) if ALIAS_MAP_FILE.exists() else {}
    new_to_legacy = alias_data.get("new_to_legacy", {})

    cols = 3
    first_style = styles[0]["number"]
    last_style = styles[-1]["number"]
    total_styles = len(styles)

    # 1. Chinese STYLES.md
    zh_lines = [
        '<p align="center">',
        '  <strong>中文</strong> | <a href="STYLES_en.md">English</a>',
        '</p>',
        '',
        f"# 手绘风格完整图鉴（{first_style}–{last_style} · 共 {total_styles} 种）",
        "",
        f"> 这里收录了本库全部 **{total_styles} 种手绘风格**的独立编号图鉴与核心提示词特征。每种风格均配有标准图样预览、分类编号、英文生图名称、风格参考来源与核心视觉特征，供在 GitHub 上直接图文浏览选款。详细对照表见 [styles_200_reorganized.md](styles_200_reorganized.md)。",
        "",
        "## 目录导航",
        "",
    ]
    for cat_id, title_zh, _, _, _ in STYLE_CATEGORIES:
        cat_styles = [s for s in styles if s["number"].startswith(f"{cat_id}-")]
        if cat_styles:
            r_start = cat_styles[0]["number"]
            r_end = cat_styles[-1]["number"]
            zh_lines.append(f"- [{cat_id} · {title_zh}（{r_start}–{r_end} · {len(cat_styles)} 种）](#group-{cat_id.lower()})")
    zh_lines.extend(["", "---", ""])

    for cat_id, title_zh, _, desc_zh, _ in STYLE_CATEGORIES:
        cat_styles = [s for s in styles if s["number"].startswith(f"{cat_id}-")]
        if not cat_styles:
            continue
        r_start = cat_styles[0]["number"]
        r_end = cat_styles[-1]["number"]
        zh_lines.append(f'<a id="group-{cat_id.lower()}"></a>')
        zh_lines.append(f"## {cat_id} · {title_zh}（{r_start}–{r_end} · {len(cat_styles)} 种）")
        zh_lines.append("")
        zh_lines.append(desc_zh)
        zh_lines.append("")
        zh_lines.append("| 效果预览 | 效果预览 | 效果预览 |")
        zh_lines.append("| :---: | :---: | :---: |")

        for i in range(0, len(cat_styles), cols):
            chunk = cat_styles[i:i + cols]
            row_cells = []
            for s in chunk:
                num = s["number"]
                cat = num.split("-")[0]
                legacy = new_to_legacy.get(num, "")
                legacy_str = f" <small>(#{legacy})</small>" if legacy else ""
                gen_name = s.get("generation_name", "")
                ref = s.get("reference", "")
                traits = s.get("traits", "").replace("|", "&#124;").replace("\n", "<br>")

                cell = f"<img src='images/individual/{cat}/{num}.webp' width='220' alt='{num} {gen_name}'><br>**{num}**{legacy_str} · {gen_name}"
                if ref:
                    cell += f"<br><sub>参考: {ref}</sub>"
                if traits:
                    cell += f"<br><details><summary>查看核心特征</summary><br>{traits}</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            zh_lines.append(f"| {' | '.join(row_cells)} |")

        zh_lines.append("")
        zh_lines.append("---")
        zh_lines.append("")

    archive_sheets = sorted([p.name for p in (ROOT / "images").glob("[A-I]_*.webp")])
    if archive_sheets:
        zh_lines.append("<details>")
        zh_lines.append("<summary>📦 拼图大表历史归档 (Contact Sheets Archive)</summary>")
        zh_lines.append("")
        for sheet in archive_sheets:
            label = sheet.replace(".webp", "").replace("_", " ")
            zh_lines.append(f"![{label}](images/{sheet})")
            zh_lines.append("")
        zh_lines.append("</details>")
        zh_lines.append("")

    (ROOT / "STYLES.md").write_text("\n".join(zh_lines).strip() + "\n", encoding="utf-8")
    print("Built STYLES.md")

    # 2. English STYLES_en.md
    en_lines = [
        '<p align="center">',
        '  <a href="STYLES.md">中文</a> | <strong>English</strong>',
        '</p>',
        '',
        f"# Hand-drawn Style Visual Gallery ({first_style}–{last_style} · {total_styles} Styles)",
        "",
        f"> Complete visual catalogue and prompt traits for all **{total_styles} hand-drawn illustration styles** ({first_style}–{last_style}). Each style includes image preview, classification ID, generation name, artistic reference, and core prompt traits for direct browsing on GitHub. For detailed generation names and prompt traits, see [styles_200_reorganized.md](styles_200_reorganized.md).",
        "",
        "## Table of Contents",
        "",
    ]
    for cat_id, _, title_en, _, _ in STYLE_CATEGORIES:
        cat_styles = [s for s in styles if s["number"].startswith(f"{cat_id}-")]
        if cat_styles:
            r_start = cat_styles[0]["number"]
            r_end = cat_styles[-1]["number"]
            en_lines.append(f"- [{cat_id} · {title_en} ({r_start}–{r_end} · {len(cat_styles)} Styles)](#group-{cat_id.lower()})")
    en_lines.extend(["", "---", ""])

    for cat_id, _, title_en, _, desc_en in STYLE_CATEGORIES:
        cat_styles = [s for s in styles if s["number"].startswith(f"{cat_id}-")]
        if not cat_styles:
            continue
        r_start = cat_styles[0]["number"]
        r_end = cat_styles[-1]["number"]
        en_lines.append(f'<a id="group-{cat_id.lower()}"></a>')
        en_lines.append(f"## {cat_id} · {title_en} ({r_start}–{r_end} · {len(cat_styles)} Styles)")
        en_lines.append("")
        en_lines.append(desc_en)
        en_lines.append("")
        en_lines.append("| Visual Preview | Visual Preview | Visual Preview |")
        en_lines.append("| :---: | :---: | :---: |")

        for i in range(0, len(cat_styles), cols):
            chunk = cat_styles[i:i + cols]
            row_cells = []
            for s in chunk:
                num = s["number"]
                cat = num.split("-")[0]
                legacy = new_to_legacy.get(num, "")
                legacy_str = f" <small>(#{legacy})</small>" if legacy else ""
                gen_name = s.get("generation_name", "")
                ref = s.get("reference", "")
                traits = s.get("traits", "").replace("|", "&#124;").replace("\n", "<br>")

                cell = f"<img src='images/individual/{cat}/{num}.webp' width='220' alt='{num} {gen_name}'><br>**{num}**{legacy_str} · {gen_name}"
                if ref:
                    cell += f"<br><sub>Ref: {ref}</sub>"
                if traits:
                    cell += f"<br><details><summary>View Traits</summary><br>{traits}</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            en_lines.append(f"| {' | '.join(row_cells)} |")

        en_lines.append("")
        en_lines.append("---")
        en_lines.append("")

    if archive_sheets:
        en_lines.append("<details>")
        en_lines.append("<summary>📦 Contact Sheets Archive</summary>")
        en_lines.append("")
        for sheet in archive_sheets:
            label = sheet.replace(".webp", "").replace("_", " ")
            en_lines.append(f"![{label}](images/{sheet})")
            en_lines.append("")
        en_lines.append("</details>")
        en_lines.append("")

    (ROOT / "STYLES_en.md").write_text("\n".join(en_lines).strip() + "\n", encoding="utf-8")
    print("Built STYLES_en.md")


def build_layouts_md() -> None:
    layouts = json.loads(LAYOUTS_JSON.read_text(encoding="utf-8"))
    anchor_map = {
        "social-card": "social-cards",
        "infographic": "infographics",
        "comic-storyboard": "comic-storyboards",
        "ip-character": "ip-characters",
        "ecommerce": "ecommerce",
    }
    cols = 3
    counts = {
        "social-card": sum(l["category"] == "social-card" for l in layouts),
        "infographic": sum(l["category"] == "infographic" for l in layouts),
        "comic-storyboard": sum(l["category"] == "comic-storyboard" for l in layouts),
        "ip-character": sum(l["category"] == "ip-character" for l in layouts),
        "ecommerce": sum(l["category"] == "ecommerce" for l in layouts),
    }
    categories = [
        ("social-card", f"1. 社媒卡（{counts['social-card']} 种）", f"1. Social Cards ({counts['social-card']} Layouts)",
         "适合小红书、朋友圈、公众号配图及观点金句卡片。结构包含上下图文、文案主导、双格对照等。",
         "Ideal for Xiaohongshu, Instagram, newsletter hero images, and quote cards. Includes top-bottom split, text-driven cards, two-column contrasts, and sticky notes."),
        ("infographic", f"2. 信息图（{counts['infographic']} 种）", f"2. Infographics ({counts['infographic']} Layouts)",
         "适合知识科普、对比清单、流程步骤及数据架构展示。结构包含金字塔层级、中心主图标注、多行多列对比等。",
         "Ideal for knowledge sharing, comparison charts, process workflows, and structured data visuals. Includes hierarchy pyramids, central icons, matrices, and multi-column comparison tables."),
        ("comic-storyboard", f"3. 漫画分镜（{counts['comic-storyboard']} 种）", f"3. Comic Storyboards ({counts['comic-storyboard']} Layouts)",
         "适合多格叙事、剧情转折、条漫分镜及动态视觉表现。结构包含规则四格、起承转合、大格冲击、对角切割等专业分镜。",
         "Ideal for multi-panel narratives, webtoons, emotional storylines, and cinematic pacing. Includes standard 4-panel grids, dramatic wide-angle focus, diagonal cuts, and manga storyboards."),
        ("ip-character", f"4. IP设计（{counts['ip-character']} 种）", f"4. IP Design ({counts['ip-character']} Layouts)",
         "适合 IP 形象设计、吉祥物定位卡、角色档案及形象规范展示。结构包含主形象大图、定位金句、受众画像与多视角展示。",
         "Ideal for IP character design, mascot positioning cards, character profiles, and specification guides. Includes hero character showcase, positioning slogans, audience profiles, and multi-angle views."),
        ("ecommerce", f"5. 电商（{counts['ecommerce']} 种）", f"5. E-commerce ({counts['ecommerce']} Layouts)",
         "适合电商商品展示、主图详情页、卖点拆解、使用场景及选购决策。结构包含单品主图、多视角、参数尺寸、材质解析与对比优势等。",
         "Ideal for e-commerce product showcases, PDP hero images, feature callouts, lifestyle scenarios, and buying guides. Includes single product hero, multi-angle views, specs, material breakdown, and comparative advantage."),
    ]

    # 1. Chinese LAYOUTS.md
    zh_lines = [
        '<p align="center">',
        '  <strong>中文</strong> | <a href="LAYOUTS_en.md">English</a>',
        '</p>',
        '',
        f"# 排版图型完整图鉴（{len(layouts)} 种）",
        "",
        f"> 这里收录了本库全部 **{len(layouts)} 种排版图型**（社媒卡、信息图、漫画分镜、IP设计、电商）的图片预览与排版提示词。在 AI 生图时直接指定图型编号（如 `SC-001`、`IG-003`、`SB-002`、`IP-001`、`EC-001`），即可精确控制画面的构图版式与排版层次。",
        "",
        "> 💡 **排版图型架构机制**：",
        "> - **确定性静态排版（纯文本直接拼接型）**：包括 `SC-001`~`SC-020`、`IG` 系列与 `SB` 系列等绝大多数图型，拓扑单一固定，模板直接拼接画风与主题；",
        "> - **高维动态解析型排版（Skill 级动态决策型）**：以 `SC-021`（自适应双拼照片转译）为代表，属于高维视觉语法系统，由 AI 助手充当设计总监先进行构图决策（越界破框/微缩浮岛/记忆图谱等）与背景净化编译，输出单义强约束提示词。",
        "",
        "## 目录导航",
        "",
        f"- [1. 社媒卡（{counts['social-card']} 种）](#social-cards)",
        f"- [2. 信息图（{counts['infographic']} 种）](#infographics)",
        f"- [3. 漫画分镜（{counts['comic-storyboard']} 种）](#comic-storyboards)",
        f"- [4. IP设计（{counts['ip-character']} 种）](#ip-characters)",
        f"- [5. 电商（{counts['ecommerce']} 种）](#ecommerce)",
        "",
        "---",
        "",
    ]

    for cat_id, cat_title_zh, _, cat_desc_zh, _ in categories:
        cat_layouts = [l for l in layouts if l["category"] == cat_id]
        anchor = anchor_map.get(cat_id, cat_id)
        zh_lines.append(f'<a id="{anchor}"></a>')
        zh_lines.append(f"## {cat_title_zh}")
        zh_lines.append("")
        zh_lines.append(cat_desc_zh)
        zh_lines.append("")
        zh_lines.append("| 效果预览 | 效果预览 | 效果预览 |")
        zh_lines.append("| :---: | :---: | :---: |")
        for i in range(0, len(cat_layouts), cols):
            chunk = cat_layouts[i:i + cols]
            row_cells = []
            for l in chunk:
                rel_img = str(l["image"]).replace("../../../", "")
                prompt_file = SKILL / "references" / l["prompt_file"]
                prompt_zh = ""
                if prompt_file.exists():
                    content = prompt_file.read_text(encoding="utf-8")
                    if "<!-- zh -->" in content:
                        zh_part = content.split("<!-- en -->")[0].replace("<!-- zh -->", "").strip()
                    else:
                        zh_part = content.strip()
                    prompt_zh = zh_part.replace("|", "&#124;").replace("\n", "<br>")
                name = l["name"]
                cell = f"<img src='{rel_img}' width='260' alt='{l['id']} {name}'><br>**{l['id']}** · {name}"
                if prompt_zh:
                    cell += f"<br><details><summary>查看排版提示词</summary><br>{prompt_zh}</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            zh_lines.append(f"| {' | '.join(row_cells)} |")
        zh_lines.append("")
        zh_lines.append("---")
        zh_lines.append("")

    (ROOT / "LAYOUTS.md").write_text("\n".join(zh_lines).strip() + "\n", encoding="utf-8")
    print("Built LAYOUTS.md")

    # 2. English LAYOUTS_en.md
    en_lines = [
        '<p align="center">',
        '  <a href="LAYOUTS.md">中文</a> | <strong>English</strong>',
        '</p>',
        '',
        f"# Layout Composition Visual Sheet ({len(layouts)} Layouts)",
        "",
        f"> Visual previews and layout prompts for all **{len(layouts)} layout compositions** (Social Cards, Infographics, Comic Storyboards, IP Design, E-commerce). Specify layout IDs (e.g. `SC-001`, `IG-003`, `SB-002`, `IP-001`, `EC-001`) during AI image generation to control compositions, text placements, and visual hierarchy.",
        "",
        "> 💡 **Layout Architecture Modes**:",
        "> - **Deterministic Static Layouts (Direct Template Concatenation)**: Covers most layouts (`SC-001`~`SC-020`, `IG` series, `SB` series) with fixed topologies directly assembled with chosen styles;",
        "> - **Dynamic Generative Frameworks (Skill-level Reasoning & Resolution)**: Exemplified by `SC-021` (Adaptive Split Photo-to-Art), functioning as an expressive visual syntax system where the AI assistant acts as Art Director to resolve specific composition mechanics (e.g. Boundary Break, Miniature Diorama, Memory Knolling) and enforce background purging before outputting singular, high-contrast prompts.",
        "",
        "## Table of Contents",
        "",
        f"- [1. Social Cards ({counts['social-card']} Layouts)](#social-cards)",
        f"- [2. Infographics ({counts['infographic']} Layouts)](#infographics)",
        f"- [3. Comic Storyboards ({counts['comic-storyboard']} Layouts)](#comic-storyboards)",
        f"- [4. IP Design ({counts['ip-character']} Layouts)](#ip-characters)",
        f"- [5. E-commerce ({counts['ecommerce']} Layouts)](#ecommerce)",
        "",
        "---",
        "",
    ]

    for cat_id, _, cat_title_en, _, cat_desc_en in categories:
        cat_layouts = [l for l in layouts if l["category"] == cat_id]
        anchor = anchor_map.get(cat_id, cat_id)
        en_lines.append(f'<a id="{anchor}"></a>')
        en_lines.append(f"## {cat_title_en}")
        en_lines.append("")
        en_lines.append(cat_desc_en)
        en_lines.append("")
        en_lines.append("| Preview | Preview | Preview |")
        en_lines.append("| :---: | :---: | :---: |")
        for i in range(0, len(cat_layouts), cols):
            chunk = cat_layouts[i:i + cols]
            row_cells = []
            for l in chunk:
                rel_img = str(l["image"]).replace("../../../", "")
                prompt_file = SKILL / "references" / l["prompt_file"]
                prompt_en = ""
                if prompt_file.exists():
                    content = prompt_file.read_text(encoding="utf-8")
                    if "<!-- en -->" in content:
                        en_part = content.split("<!-- en -->")[1].strip()
                    else:
                        en_part = ""
                    prompt_en = en_part.replace("|", "&#124;").replace("\n", "<br>")
                name_en = l.get("name_en") or l.get("name", "")
                cell = f"<img src='{rel_img}' width='260' alt='{l['id']} {name_en}'><br>**{l['id']}** · {name_en}"
                if prompt_en:
                    cell += f"<br><details><summary>View Layout Prompt</summary><br>{prompt_en}</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            en_lines.append(f"| {' | '.join(row_cells)} |")
        en_lines.append("")
        en_lines.append("---")
        en_lines.append("")

    (ROOT / "LAYOUTS_en.md").write_text("\n".join(en_lines).strip() + "\n", encoding="utf-8")
    print("Built LAYOUTS_en.md")


def build_colors_md() -> None:
    if not COLORS_JSON.exists():
        return
    colors = json.loads(COLORS_JSON.read_text(encoding="utf-8"))
    sheets = [
        (1, "经典蓝系（6 种）", "Classic Blue (6 Colors)", "沉静理性、跨越时光的纯粹蓝调，适合科技、思考、静夜与海洋题材。", "Calm, rational, and timeless pure blue tones, ideal for tech, reflection, nocturnal, and ocean themes."),
        (2, "清新绿系（6 种）", "Fresh Green (6 Colors)", "自然治愈、盛夏微风的清新绿意，适合生活方式、健康、植物与轻食题材。", "Natural, healing, and breezy green tones, ideal for lifestyle, wellness, flora, and food themes."),
        (3, "古典红绿（6 种）", "Classic Red & Vintage (6 Colors)", "历史沉淀、浓郁厚重的东方与古典艺术色，适合节庆、传统文化、复古与叙事题材。", "Historical and rich classical tones, ideal for festivals, heritage, vintage, and narrative themes."),
        (4, "浪漫粉紫（6 种）", "Romantic Pink & Purple (6 Colors)", "温柔优雅、热烈浪漫的情感色系，适合女性生活、诗意、美妆与自我表达题材。", "Gentle, elegant, and romantic palettes, ideal for feminine lifestyle, poetry, cosmetics, and self-expression."),
        (5, "暖阳大地（6 种）", "Warm Sun & Earth (6 Colors)", "温暖明媚、沉静质朴的大地色系，适合晨光、咖啡、穿搭、秋收与温馨日常题材。", "Warm, sunny, and grounded earth tones, ideal for morning light, coffee, autumn, and cozy daily life."),
        (6, "中性色系（6 种）", "Classic Neutral Tones (6 Colors)", "克制沉静、现代高级的黑白灰与中性色调，适合极简生活、建筑空间、沉思书房与质朴日常题材。", "Restrained, tranquil, and modern neutral tones across grey, black, cream, and taupe, ideal for minimalist lifestyle, architectural spaces, reflective studies, and serene daily life."),
    ]
    cols = 3

    # 1. Chinese COLORS.md
    zh_lines = [
        '<p align="center">',
        '  <strong>中文</strong> | <a href="COLORS_en.md">English</a>',
        '</p>',
        '',
        f"# 经典单色主题色完整图鉴（{len(colors)} 种）",
        "",
        f"> 这里收录了本库精选的 **{len(colors)} 种经典单色主题色**（涵盖经典蓝系、清新绿系、古典红绿、浪漫粉紫、暖阳大地、中性色系）。在 AI 生图时直接指定色彩编号（如 `C-01`、`C-10`、`C-15`、`C-31`）或色彩名称（如“克莱因蓝”、“鼠尾草绿”、“佩恩灰”），即可精确控制画面的主色调与情绪氛围。",
        "",
        "## 目录导航",
        "",
    ]
    for s_num, title_zh, _, _, _ in sheets:
        zh_lines.append(f"- [{s_num}. {title_zh}](#sheet-{s_num:02d})")
    zh_lines.extend(["", "---", ""])

    for s_num, title_zh, _, desc_zh, _ in sheets:
        s_colors = [c for c in colors if c["sheet"] == s_num]
        zh_lines.append(f'<a id="sheet-{s_num:02d}"></a>')
        zh_lines.append(f"## {s_num}. {title_zh}")
        zh_lines.append("")
        zh_lines.append(desc_zh)
        zh_lines.append("")
        zh_lines.append(f"![经典单色主题色库 {s_num:02d}](images/colors/sheet_{s_num:02d}.webp)")
        zh_lines.append("")
        zh_lines.append("| 效果预览 | 效果预览 | 效果预览 |")
        zh_lines.append("| :---: | :---: | :---: |")
        for i in range(0, len(s_colors), cols):
            chunk = s_colors[i:i + cols]
            row_cells = []
            for c in chunk:
                rel_img = str(c["image"]).replace("../../../", "")
                cell = f"<img src='{rel_img}' width='220' alt='{c['id']} {c['name_zh']}'><br>**{c['id']}** · {c['name_zh']}<br><small>{c['quote_zh']}</small><br><details><summary>查看色彩提示词</summary><br>`{c['prompt_zh']}`</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            zh_lines.append(f"| {' | '.join(row_cells)} |")
        zh_lines.append("")
        zh_lines.append("---")
        zh_lines.append("")

    (ROOT / "COLORS.md").write_text("\n".join(zh_lines).strip() + "\n", encoding="utf-8")
    print("Built COLORS.md")

    # 2. English COLORS_en.md
    en_lines = [
        '<p align="center">',
        '  <a href="COLORS.md">中文</a> | <strong>English</strong>',
        '</p>',
        '',
        f"# Classic Monochrome Colors Visual Sheet ({len(colors)} Colors)",
        "",
        f"> Visual previews and color prompts for all **{len(colors)} curated monochrome theme colors** (Classic Blue, Fresh Green, Vintage Red & Classical, Romantic Pink & Purple, Warm Sun & Earth, Classic Neutral Tones). Specify color IDs (e.g. `C-01`, `C-10`, `C-15`, `C-31`) or color names (e.g. 'Klein Blue', 'Sage Green', 'Payne\\'s Grey') during AI image generation to precisely control color palettes and visual moods.",
        "",
        "## Table of Contents",
        "",
    ]
    for s_num, _, title_en, _, _ in sheets:
        en_lines.append(f"- [{s_num}. {title_en}](#sheet-{s_num:02d})")
    en_lines.extend(["", "---", ""])

    for s_num, _, title_en, _, desc_en in sheets:
        s_colors = [c for c in colors if c["sheet"] == s_num]
        en_lines.append(f'<a id="sheet-{s_num:02d}"></a>')
        en_lines.append(f"## {s_num}. {title_en}")
        en_lines.append("")
        en_lines.append(desc_en)
        en_lines.append("")
        en_lines.append(f"![Classic Monochrome Library {s_num:02d}](images/colors/sheet_{s_num:02d}.webp)")
        en_lines.append("")
        en_lines.append("| Visual Preview | Visual Preview | Visual Preview |")
        en_lines.append("| :---: | :---: | :---: |")
        for i in range(0, len(s_colors), cols):
            chunk = s_colors[i:i + cols]
            row_cells = []
            for c in chunk:
                rel_img = str(c["image"]).replace("../../../", "")
                cell = f"<img src='{rel_img}' width='220' alt='{c['id']} {c['name_en']}'><br>**{c['id']}** · {c['name_en']}<br><small>{c['quote_en']}</small><br><details><summary>View Color Prompt</summary><br>`{c['prompt_en']}`</details>"
                row_cells.append(cell)
            while len(row_cells) < cols:
                row_cells.append("")
            en_lines.append(f"| {' | '.join(row_cells)} |")
        en_lines.append("")
        en_lines.append("---")
        en_lines.append("")

    (ROOT / "COLORS_en.md").write_text("\n".join(en_lines).strip() + "\n", encoding="utf-8")
    print("Built COLORS_en.md")


def main() -> None:
    build_styles_md()
    build_layouts_md()
    build_colors_md()


if __name__ == "__main__":
    main()
