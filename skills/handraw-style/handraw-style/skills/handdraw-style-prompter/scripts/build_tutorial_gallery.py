#!/usr/bin/env python3
"""Build the offline interactive prompt assembler and tutorials gallery page."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
GALLERY = SKILL / "gallery" / "tutorials.html"
STYLES_JSON = SKILL / "references" / "styles.json"
LAYOUTS_JSON = SKILL / "references" / "layouts.json"
COLORS_JSON = SKILL / "references" / "colors.json"
CHARACTERS_JSON = SKILL / "references" / "characters.json"
PROPS_JSON = SKILL / "references" / "props.json"
SCENES_JSON = SKILL / "references" / "scenes.json"
TONES_JSON = SKILL / "references" / "tones.json"

IMAGE_FALLBACK_SCRIPT = """<script>
(function() {
  function fixImg(img) {
    if (!img || img.__fixed) return;
    var src = img.getAttribute('src') || '';
    var idx = src.indexOf('images/');
    if (idx === -1) return;
    var sub = src.substring(idx);
    var step = parseInt(img.dataset.retry || '0', 10);
    var candidates = [
      '../../../../' + sub,
      '../../../' + sub,
      '../../' + sub,
      '../' + sub,
      './' + sub,
      '/' + sub,
      'https://img.handraw-style.com/' + sub,
      'https://raw.githubusercontent.com/yang0/handraw-style/master/' + sub
    ];
    while (step < candidates.length) {
      var nextSrc = candidates[step];
      step++;
      if (nextSrc !== src) {
        img.dataset.retry = step.toString();
        img.src = nextSrc;
        return;
      }
    }
    img.__fixed = true;
  }
  window.addEventListener('error', function(e) {
    if (e.target && e.target.tagName === 'IMG') {
      fixImg(e.target);
    }
  }, true);
  window.addEventListener('load', function(e) {
    if (e.target && e.target.tagName === 'IMG') {
      var card = e.target.closest('.style-card, .layout-card, .color-card, .asset-card, .picker-card');
      if (card && e.target.src) {
        card.dataset.image = e.target.src;
      }
    }
  }, true);
})();
</script>"""


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from build_color_gallery import CATEGORIES as COLOR_CATEGORIES

TUTORIALS = [
    {
        "id": "poster-mindset",
        "summary_zh": "手绘 skill 里面的信息图类型不够用怎么办？可以把信息图当做海报来设计，你只要告知 skill 你要呈现的信息和使用场景，剩下的一切就交给 skill 来处理就好。",
        "summary_en": "What if preset infographic types aren't enough? Treat infographics as posters. Just provide your info and scenario, and let the skill handle the rest.",
        "prompt_zh": "做一张《山系露营轻量化装包》海报，把装备按睡眠系统（帐篷/睡袋）、烹饪系统（炉头/钛杯）、照明系统（马灯）分类，标注总重量控制在 8kg 内，户外手绘工装风。",
        "prompt_en": "Design an Ultralight Mountain Camping Packing Guide poster categorizing sleeping, cooking, and lighting gear, marked under 8kg, in vintage outdoor workwear silkscreen style.",
    },
    {
        "id": "modes-rule",
        "summary_zh": "想为图片自动添加排版文字？输入提示词：切换为图文模式。AI 会自动在画风笔触与文字版式之间建立呼吸感，让文字原生参与构图，图文一体。",
        "summary_en": "Want to automatically add layout text to your image? Enter: Switch to graphic-text mode. AI will create breathing space between linework and typography, letting text integrate natively into the composition.",
        "prompt_zh": "切换到图文模式",
        "prompt_en": "Switch to graphic-text mode",
    },
]

COPY_ICON_SVG = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>'
    '</svg>'
)


def individual_image_path(number: str) -> str:
    cat = number.split("-")[0]
    return f"../../../images/individual/{cat}/{number}.webp"


def build_html() -> str:
    styles_raw = json.loads(STYLES_JSON.read_text(encoding="utf-8")) if STYLES_JSON.exists() else []
    layouts_raw = json.loads(LAYOUTS_JSON.read_text(encoding="utf-8")) if LAYOUTS_JSON.exists() else []
    colors_raw = json.loads(COLORS_JSON.read_text(encoding="utf-8")) if COLORS_JSON.exists() else []
    characters_raw = json.loads(CHARACTERS_JSON.read_text(encoding="utf-8")) if CHARACTERS_JSON.exists() else []
    props_raw = json.loads(PROPS_JSON.read_text(encoding="utf-8")) if PROPS_JSON.exists() else []
    scenes_raw = json.loads(SCENES_JSON.read_text(encoding="utf-8")) if SCENES_JSON.exists() else []
    tones_raw = json.loads(TONES_JSON.read_text(encoding="utf-8")) if TONES_JSON.exists() else []

    try:
        import custom_library_manager
        custom_library_manager.export_custom_assets_js()
    except Exception:
        pass

    def to_preset_asset(p: dict, category: str) -> dict:
        return {
            "id": str(p.get("id", "")),
            "name": str(p.get("name", "")),
            "name_en": str(p.get("name_en", p.get("name", ""))),
            "cat": category,
            "img": str(p.get("image", "")),
            "tags": p.get("tags", []),
            "is_custom": False,
        }

    # Static HTML strictly contains official presets only (never bake local custom assets into Git)
    assets_data = (
        [to_preset_asset(x, "characters") for x in characters_raw] +
        [to_preset_asset(x, "props") for x in props_raw] +
        [to_preset_asset(x, "scenes") for x in scenes_raw]
    )

    alias_file = SKILL / "references" / "style_alias_map.json"
    alias_map = json.loads(alias_file.read_text(encoding="utf-8")) if alias_file.exists() else {}
    new_to_legacy = alias_map.get("new_to_legacy", {})

    styles_data = [
        {
            "id": s["number"],
            "legacy_id": new_to_legacy.get(s["number"], ""),
            "name": s["generation_name"],
            "ref": s["reference"],
            "group": s["number"].split("-")[0],
            "group_name": s.get("group", ""),
            "img": individual_image_path(s["number"]),
        }
        for s in styles_raw
    ]

    layouts_data = [
        {
            "id": l["id"],
            "name": l["name"],
            "name_en": l.get("name_en", l["name"]),
            "cat": l.get("category", "social-card"),
            "img": l["image"],
        }
        for l in layouts_raw
    ]

    colors_data = [
        {
            "id": c["id"],
            "name": c["name_zh"],
            "name_en": c["name_en"],
            "cat": c.get("category", "all"),
            "cat_zh": c.get("category_zh", ""),
            "cat_en": c.get("category_en", ""),
            "img": c["image"],
        }
        for c in colors_raw
    ]

    tones_data = [
        {
            "id": t["id"],
            "name": t["name_zh"],
            "name_en": t.get("name_en", t["name_zh"]),
            "cat": t.get("category", "atmosphere"),
            "cat_zh": t.get("category_zh", ""),
            "cat_en": t.get("category_en", ""),
            "desc_zh": t.get("desc_zh", ""),
            "desc_en": t.get("desc_en", ""),
            "img": t["image"],
        }
        for t in tones_raw
    ]

    assets_json_str = json.dumps(assets_data, ensure_ascii=False, separators=(",", ":"))
    styles_json_str = json.dumps(styles_data, ensure_ascii=False, separators=(",", ":"))
    layouts_json_str = json.dumps(layouts_data, ensure_ascii=False, separators=(",", ":"))
    colors_json_str = json.dumps(colors_data, ensure_ascii=False, separators=(",", ":"))
    tones_json_str = json.dumps(tones_data, ensure_ascii=False, separators=(",", ":"))
    assets_count = len(assets_data)
    styles_count = len(styles_data)
    layouts_count = len(layouts_data)
    colors_count = len(colors_data)
    tones_count = len(tones_data)
    color_categories_data = [{"id": cid, "zh": czh, "en": cen} for cid, czh, cen in COLOR_CATEGORIES]
    color_categories_json_str = json.dumps(color_categories_data, ensure_ascii=False, separators=(",", ":"))

    cards = []
    for item in TUTORIALS:
        card_html = (
            f'<article class="tutorial-card">'
            f'<p class="card-summary" data-zh="{html.escape(item["summary_zh"])}" data-en="{html.escape(item["summary_en"])}">{html.escape(item["summary_zh"])}</p>'
            f'<div class="formula-box">'
            f'<button class="copy-btn" type="button" title="复制提示词" aria-label="复制提示词" data-prompt="{html.escape(item["prompt_zh"], quote=True)}">{COPY_ICON_SVG}</button>'
            f'<span class="formula-label" data-i18n="formulaLabel">示例提示词：</span>'
            f'<code class="formula-text" data-zh="{html.escape(item["prompt_zh"])}" data-en="{html.escape(item["prompt_en"])}">{html.escape(item["prompt_zh"])}</code>'
            f'</div>'
            f'</article>'
        )
        cards.append(card_html)
    cards_str = "\n".join(cards)

    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>手绘 Skill 提示词拼装器</title><style>
:root{{color:#24211e;background:#f7f5f0;font:16px/1.5 system-ui,"Microsoft YaHei",sans-serif}}
body{{margin:0}}
img{{max-width:100%;box-sizing:border-box}}
main{{max-width:1240px;margin:auto;padding:24px 30px 50px}}
.sticky-header{{position:sticky;top:0;z-index:100}}
.site-nav{{display:flex;align-items:center;gap:10px;margin:0;padding:12px 30px;border-bottom:1px solid #ded8cf;background:#fffdf9}}
.site-nav a{{border:1px solid #9e9185;border-radius:8px;background:#fff;color:#403a34;padding:7px 13px;text-decoration:none;font-weight:800;line-height:1.2;transition:background .15s,color .15s,border-color .15s}}
.site-nav a:hover{{border-color:#b74227;background:#fff0eb;color:#9f351f}}
.site-nav a[aria-current="page"]{{border-color:#b74227;background:#b74227;color:#fff;box-shadow:0 1px 3px #b7422744}}
.nav-right{{margin-left:auto;display:flex;align-items:center;gap:8px}}
.nav-ext{{display:inline-flex;align-items:center;font-weight:700}}
.nav-btn{{border:1px solid #9e9185;border-radius:8px;background:#fff;color:#403a34;padding:7px 13px;font:inherit;font-weight:700;line-height:1.2;cursor:pointer;transition:background .15s,color .15s,border-color .15s}}
.nav-btn:hover{{border-color:#b74227;background:#fff0eb;color:#9f351f}}
.nav-btn:focus-visible,.site-nav a:focus-visible{{outline:3px solid #d67d4d;outline-offset:3px}}

/* Assembler Studio */
.assembler-section{{margin-bottom:36px}}
.assembler-box{{background:#fff;border:1px solid #dcd5ca;border-radius:16px;padding:24px 26px;box-shadow:0 3px 12px rgba(0,0,0,0.04)}}
.assembler-header{{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:18px;border-bottom:1px solid #eee8df;padding-bottom:14px}}
.assembler-title-wrap{{display:flex;align-items:center;gap:10px}}
.assembler-title{{margin:0;font-size:22px;font-weight:800;color:#24211e}}
.assembler-sub{{margin:0;font-size:13.5px;color:#786f65}}

/* Steps & Sections Layout */
.assembler-steps{{display:flex;flex-direction:column;gap:16px}}
.step-card{{background:#faf8f5;border:1px solid #e5ded4;border-radius:14px;padding:16px 20px;transition:border-color .15s,box-shadow .15s}}
.step-card:hover{{border-color:#d5cbbe}}
.step-card.step-output-card{{background:#fffdfa;border:1px solid #dcd3c5;border-left:4px solid #b74227}}
.step-header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px 16px;margin-bottom:14px;border-bottom:1px solid #efe9df;padding-bottom:10px}}
.step-title-wrap{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.step-badge{{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:#b74227;color:#fff;font-size:13px;font-weight:800;line-height:1;flex-shrink:0;box-shadow:0 1px 3px rgba(183,66,39,0.25)}}
.step-title{{margin:0;font-size:15px;font-weight:800;color:#24211e;display:inline-flex;align-items:center;gap:6px}}
.step-title.output-title{{color:#b74227}}
.step-toolbar{{display:flex;align-items:center;gap:8px;margin-left:auto}}
.step-body{{display:flex;flex-direction:column;gap:12px}}

/* Mode & Density Controls */
.mode-row{{display:flex;align-items:center;gap:16px 28px;flex-wrap:wrap}}
.mode-item{{display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap}}
.mode-label{{font-size:14px;font-weight:750;color:#3b352f}}
.mode-group,.density-group{{display:inline-flex;align-items:center;gap:4px;background:#eee8df;padding:3px;border-radius:8px;border:1px solid #dcd5ca}}
.mode-btn,.density-btn{{border:1px solid transparent;background:transparent;color:#514a43;font:inherit;font-size:13px;font-weight:750;padding:5px 14px;border-radius:6px;cursor:pointer;line-height:1.3;transition:all .15s}}
.mode-btn:hover,.density-btn:hover{{color:#b74227;background:#ffffffa0}}
.mode-btn.is-active,.density-btn.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 3px rgba(183,66,39,0.3)}}

/* Form Fields */
.form-group{{display:flex;flex-direction:column;gap:5px}}
.form-label{{font-size:13.5px;font-weight:700;color:#3b352f;display:flex;align-items:center;gap:4px}}
.form-label .req{{color:#b74227}}
.text-input{{width:100%;box-sizing:border-box;border:1px solid #c9c1b6;border-radius:8px;padding:9px 12px;font:inherit;font-size:14px;background:#fffdfa;color:#24211e;transition:border-color .15s,box-shadow .15s}}
.text-input:focus{{outline:none;border-color:#b74227;box-shadow:0 0 0 3px rgba(183,66,39,0.15)}}
.text-area{{min-height:58px;line-height:1.5;resize:vertical;font-family:inherit;overflow-y:auto}}
.extra-fields-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.extra-fields-grid.single-col{{grid-template-columns:1fr}}
.extra-fields-grid[hidden]{{display:none!important}}


/* Aspect Ratio Selector */
.ratio-form-group{{display:flex;flex-direction:column;gap:8px}}
.selector-options-row{{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:12px;align-items:start}}
.selector-options-row>.form-label{{padding-top:5px;white-space:nowrap}}
.ratio-presets-row{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.ratio-preset-btn{{border:1px solid #dcd5ca;background:#faf8f5;color:#4a423a;padding:5px 12px;border-radius:18px;font:inherit;font-size:12.5px;font-weight:700;cursor:pointer;line-height:1.3;transition:all .15s}}
.ratio-preset-btn:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.ratio-preset-btn.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 3px rgba(183,66,39,0.25)}}
.ratio-input-wrap{{position:relative;display:inline-flex;align-items:center;max-width:380px;width:100%}}
.ratio-input{{padding-right:32px;font-size:13.5px}}
.ratio-clear-btn{{position:absolute;right:8px;top:50%;transform:translateY(-50%);border:0;background:transparent;color:#8c8276;font-size:18px;line-height:1;cursor:pointer;padding:2px 6px;border-radius:4px;transition:all .15s}}
.ratio-clear-btn:hover{{color:#b74227;background:#fff0eb}}

/* Mood Selector */
.mood-form-group{{display:flex;flex-direction:column;gap:8px}}
.mood-presets-row{{display:flex;flex-wrap:wrap;gap:7px;align-items:center}}
.mood-preset-btn,.shoot-type-preset-btn{{border:1px solid #dcd5ca;background:#faf8f5;color:#4a423a;padding:4px 11px;border-radius:16px;font:inherit;font-size:12.5px;font-weight:700;cursor:pointer;line-height:1.3;transition:all .15s}}
.mood-preset-btn:hover,.shoot-type-preset-btn:hover:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.mood-preset-btn.is-active,.shoot-type-preset-btn.is-active.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 3px rgba(183,66,39,0.25)}}

/* Slots Grid */
.fusion-checkbox-wrap{{display:inline-flex;align-items:center;gap:6px;margin-left:12px;padding:3px 10px;border-radius:16px;background:#eee8df;border:1px solid #dcd5ca;cursor:pointer;font-size:12.5px;font-weight:750;color:#514a43;user-select:none;transition:all .15s}}
.fusion-checkbox-wrap:hover{{background:#ede6dc;border-color:#b74227;color:#b74227}}
.fusion-checkbox-wrap.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 4px rgba(183,66,39,0.25)}}
.fusion-checkbox{{accent-color:#b74227;cursor:pointer;margin:0}}
/* Assets Module (Multi-Asset Tray) */
.assets-module{{margin-bottom:20px;padding-bottom:18px;border-bottom:1px dashed #ded8cf}}
.assets-module-header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:12px}}
.assets-header-left{{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px}}
.assets-module-title{{font-size:14.5px;font-weight:800;color:#24211e}}
.assets-module-desc{{font-size:12px;color:#8a8075}}
.assets-header-actions{{display:flex;align-items:center;gap:8px}}
.btn-clear-assets{{border:1px solid #ded8cf;background:#fff;color:#786f65;font:inherit;font-size:12px;font-weight:700;padding:4px 10px;border-radius:6px;cursor:pointer;transition:all .15s}}
.btn-clear-assets:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.btn-add-assets{{border:1px solid #b74227;background:#b74227;color:#fff;font:inherit;font-size:12.5px;font-weight:750;padding:5px 12px;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;transition:all .15s}}
.btn-add-assets:hover{{background:#cf4f33;border-color:#cf4f33}}
.assets-empty-trigger{{width:100%;min-height:76px;border:2px dashed #dcd5ca;border-radius:10px;background:#fffdfa;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer;color:#786f65;font:inherit;font-size:13.5px;font-weight:700;padding:16px 20px;transition:all .15s}}
.assets-empty-trigger:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.assets-tray-cards{{display:flex;flex-wrap:wrap;gap:12px;align-items:stretch}}
.asset-tray-card{{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #ded8cf;border-radius:10px;padding:8px 10px;box-shadow:0 1px 4px rgba(0,0,0,0.03);position:relative;transition:all .15s;max-width:280px;min-width:0;overflow:hidden;flex:0 0 auto}}
.asset-tray-card:hover{{border-color:#b74227;box-shadow:0 2px 8px rgba(183,66,39,0.08)}}
.asset-tray-thumb-wrap{{width:52px;height:52px;min-width:52px;max-width:52px;min-height:52px;max-height:52px;border-radius:6px;overflow:hidden;background:#eee;border:1px solid #ded8cf;flex-shrink:0;display:flex;align-items:center;justify-content:center}}
.asset-tray-thumb,.asset-tray-img{{width:52px;height:52px;min-width:52px;max-width:52px;min-height:52px;max-height:52px;border-radius:6px;object-fit:cover;background:#eee;border:1px solid #ded8cf;flex-shrink:0;display:block}}
.asset-tray-thumb-wrap .asset-tray-img{{border:none;border-radius:0;width:100%;height:100%}}
.asset-tray-info{{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1;overflow:hidden}}
.asset-tray-id-row{{display:flex;align-items:center;gap:6px}}
.asset-badge{{font-size:11px;font-weight:800;padding:1px 5px;border-radius:4px;letter-spacing:0.3px;white-space:nowrap}}
.asset-badge.is-char{{background:#fff0eb;color:#b74227;border:1px solid #fedcd3}}
.asset-badge.is-prop{{background:#fef6e9;color:#b36b00;border:1px solid #fde7c2}}
.asset-badge.is-scene{{background:#eef7ee;color:#2b772b;border:1px solid #d2ecd2}}
.asset-tray-name{{font-size:13px;font-weight:750;color:#24211e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.asset-remove-btn{{width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;border:1px solid transparent;border-radius:4px;background:transparent;color:#a0968a;cursor:pointer;font-size:16px;line-height:1;padding:0;transition:all .15s;flex-shrink:0}}
.asset-remove-btn:hover{{background:#fee;color:#d32f2f;border-color:#fcc}}
.asset-tray-more{{display:flex;align-items:center;justify-content:center;gap:6px;border:2px dashed #ded8cf;border-radius:10px;background:#faf8f5;color:#786f65;font:inherit;font-size:12.5px;font-weight:750;padding:0 16px;min-height:66px;cursor:pointer;transition:all .15s;white-space:nowrap}}
.asset-tray-more:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}

.slots-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:0}}
.slots-grid.is-fusion{{grid-template-columns:repeat(4,1fr)}}
.slots-grid.is-tone{{grid-template-columns:repeat(4,1fr)}}
.slots-grid.is-fusion.is-tone{{grid-template-columns:repeat(5,1fr)}}
@media(max-width:1200px){{.slots-grid.is-fusion.is-tone{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:1100px){{.slots-grid.is-tone,.slots-grid.is-fusion{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:860px){{.slots-grid,.slots-grid.is-fusion,.slots-grid.is-tone,.slots-grid.is-fusion.is-tone{{grid-template-columns:1fr}}}}
.picker-card.is-realistic .picker-card-name{{font-weight:750}}
.slot-card[hidden]{{display:none!important}}
.slot-card{{border:1px solid #ded8cf;border-radius:12px;background:#fff;padding:12px 14px;display:flex;flex-direction:column;gap:8px;transition:border-color .15s,box-shadow .15s,opacity .15s}}
.slot-card.has-value{{background:#fff;border-color:#b74227;box-shadow:0 2px 8px rgba(183,66,39,0.08)}}
.slot-card.is-disabled{{opacity:0.48;background:#f3efe8;border-color:#ded8cf;cursor:not-allowed}}
.slot-card.is-disabled *{{pointer-events:none}}
.slot-card.is-disabled .slot-trigger{{background:#ece7df;border-color:#d5cec4;color:#a0968a;cursor:not-allowed}}
.slot-card.is-disabled .slot-optional{{background:#e2ddd4;color:#8a8075}}
.slot-header{{display:flex;align-items:center;justify-content:space-between;font-size:13px;font-weight:750;color:#514a43}}
.slot-title{{display:flex;align-items:center;gap:5px}}
.slot-optional{{font-size:11px;font-weight:600;color:#8c8276;background:#eee8df;padding:1px 5px;border-radius:3px}}
.slot-trigger{{width:100%;min-height:92px;border:2px dashed #c9c1b6;border-radius:8px;background:#fffdfa;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;cursor:pointer;color:#786f65;font:inherit;font-size:13px;font-weight:650;transition:all .15s}}
.slot-trigger:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.slot-filled{{display:flex;align-items:center;gap:10px;min-height:92px;box-sizing:border-box;background:#fff;border-radius:8px}}
.slot-img-wrap{{position:relative;width:72px;height:72px;border-radius:6px;overflow:hidden;flex-shrink:0;background:#eee;border:1px solid #dcd5ca}}
.slot-img-wrap img{{width:100%;height:100%;object-fit:cover;display:block}}
.slot-count-badge{{position:absolute;top:4px;right:4px;background:#b74227;color:#fff;font-size:10px;font-weight:800;padding:1px 5px;border-radius:10px;line-height:1.2;box-shadow:0 1px 3px rgba(0,0,0,0.3);z-index:2}}
.slot-meta{{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0}}
.slot-code{{font-size:12px;font-weight:800;color:#b74227}}
.slot-name{{font-size:13px;font-weight:700;color:#24211e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.slot-name:empty{{display:none}}
.slot-actions{{display:flex;flex-direction:column;gap:5px;flex-shrink:0;align-items:flex-end}}
.btn-change{{border:1px solid #c9c1b6;background:#fff;color:#514a43;border-radius:5px;padding:3px 7px;font:inherit;font-size:11.5px;font-weight:700;cursor:pointer;line-height:1.2;transition:all .15s}}
.btn-change:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.btn-clear{{border:0;background:transparent;color:#8c8276;font-size:16px;line-height:1;cursor:pointer;padding:2px 4px;border-radius:4px;transition:all .15s}}
.btn-clear:hover{{color:#b74227;background:#fff0eb}}

/* Toolbar & Output */
.btn-tool{{border:1px solid #c9c1b6;border-radius:7px;background:#fff;color:#403a34;padding:5px 11px;font:inherit;font-size:12.5px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:5px;transition:all .15s}}
.btn-tool:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.btn-tool:focus-visible{{outline:2px solid #d67d4d;outline-offset:1px}}
.output-actions{{display:flex;align-items:center}}
.copy-main-btn{{border:0;border-radius:6px;background:#b74227;color:#fff;padding:6px 14px;font:inherit;font-size:13px;font-weight:750;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:background .15s,box-shadow .15s}}
.copy-main-btn:hover{{background:#cf4f33}}
.copy-main-btn.copied{{background:#2a854a}}
.assembled-text{{margin:0;font:14px/1.6 ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;color:#24211e;white-space:pre-wrap;word-break:break-word;background:#fff;border:1px solid #e5dfd5;border-radius:6px;padding:12px 14px}}

/* Modal Picker */
dialog.picker-modal{{width:min(94vw,860px);max-height:86vh;padding:20px;border:0;border-radius:14px;background:#fff;color:#24211e;box-shadow:0 20px 60px rgba(0,0,0,0.2);box-sizing:border-box}}
dialog::backdrop{{background:#000a}}
.modal-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.modal-title{{margin:0;font-size:17px;font-weight:800;color:#24211e}}
.modal-close-btn{{border:0;border-radius:6px;background:#ece7df;color:#514a43;padding:5px 9px;font:inherit;font-size:13px;font-weight:700;cursor:pointer;transition:all .15s}}
.modal-close-btn:hover{{background:#b74227;color:#fff}}
.modal-nav{{display:flex;gap:6px;align-items:center;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:8px;margin-bottom:10px}}
.modal-filter-btn{{border:1px solid #c9c1b6;background:#fff;color:#514a43;border-radius:6px;padding:4px 10px;font:inherit;font-size:12.5px;font-weight:700;white-space:nowrap;cursor:pointer;transition:all .15s}}
.modal-filter-btn:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.modal-filter-btn.is-active{{background:#b74227;color:#fff;border-color:#b74227}}
.modal-search-wrap{{margin-bottom:14px}}
.modal-search{{width:100%;box-sizing:border-box;border:1px solid #c9c1b6;border-radius:7px;padding:8px 12px;font:inherit;font-size:13.5px}}
.modal-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(115px,1fr));gap:10px;max-height:54vh;overflow-y:auto;padding-right:4px}}
.picker-card{{display:flex;flex-direction:column;box-sizing:border-box;padding:0;border:1px solid #ded8cf;border-radius:8px;background:#fff;cursor:pointer;overflow:hidden;text-align:left;position:relative;transition:transform .15s,box-shadow .15s,border-color .15s}}
.picker-card:hover{{transform:translateY(-2px);border-color:#b74227;box-shadow:0 4px 12px rgba(0,0,0,0.1)}}
.picker-card.is-selected{{border-color:#b74227;box-shadow:0 0 0 2px #b74227}}
.picker-card.is-selected .picker-card-check{{display:flex}}
.picker-card-check{{display:none;position:absolute;top:6px;right:6px;width:20px;height:20px;border-radius:50%;background:#2a854a;color:#fff;align-items:center;justify-content:center;font-size:11px;font-weight:900;box-shadow:0 1px 4px rgba(0,0,0,0.25);z-index:2}}
.picker-card-img{{width:100%;aspect-ratio:1/1;object-fit:cover;object-position:top;display:block;background:#eee}}
.picker-card-info{{padding:5px 6px;background:#fffdfa;display:flex;flex-direction:column;gap:1px}}
.picker-card-id{{font-size:10.5px;font-weight:800;color:#b74227}}
.picker-card-name{{font-size:11px;font-weight:700;color:#24211e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.2}}

.modal-footer{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid #eee8df}}
.modal-footer-info{{font-size:13px;font-weight:750;color:#514a43}}
.modal-footer-actions{{display:flex;align-items:center;gap:8px}}
.btn-modal-action{{border-radius:6px;padding:6px 14px;font:inherit;font-size:12.5px;font-weight:750;cursor:pointer;transition:all .15s}}
.btn-modal-clear{{border:1px solid #dcd5ca;background:#fff;color:#786f65}}
.btn-modal-clear:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.btn-modal-confirm{{border:1px solid #b74227;background:#b74227;color:#fff}}
.btn-modal-confirm:hover{{background:#cf4f33;border-color:#cf4f33}}

/* Retained Guides */
.guides-section{{margin-top:20px}}
.guides-title{{font-size:18px;font-weight:800;color:#24211e;margin:0 0 14px;display:flex;align-items:center;gap:6px}}
.tutorials-list{{display:flex;flex-direction:column;gap:16px}}
.tutorial-card{{border:1px solid #ded8cf;border-radius:14px;background:#fff;padding:18px 22px;box-shadow:0 2px 8px rgba(0,0,0,0.04);transition:transform .15s,box-shadow .15s}}
.tutorial-card:hover{{box-shadow:0 5px 16px rgba(0,0,0,0.07)}}
.card-summary{{margin:0 0 10px;font-size:14.5px;color:#2e2a25;line-height:1.6;font-weight:500}}
.formula-box{{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px 8px;padding:10px 14px;background:#f8f6f0;border-left:4px solid #b74227;border-radius:0 8px 8px 0;margin:0}}
.formula-label{{font-size:13px;font-weight:750;color:#b74227;white-space:nowrap;user-select:none}}
.formula-text{{font-size:13.5px;font-weight:600;color:#332e29;word-break:break-word;flex:1 1 auto}}
.copy-btn{{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;padding:0;border:1px solid #c9c1b6;border-radius:5px;background:#fff;color:#b74227;cursor:pointer;transition:all .15s;flex-shrink:0;align-self:center}}
.copy-btn:hover{{border-color:#b74227;background:#fff0eb;color:#9f351f}}
.copy-btn.copied{{border-color:#2a854a;background:#2a854a;color:#fff}}
[hidden]{{display:none!important}}

@media(max-width:860px){{
  .slots-grid{{grid-template-columns:1fr}}
  .extra-fields-grid{{grid-template-columns:1fr}}
}}
@media(max-width:760px){{
  main{{padding:16px 18px 40px}}
  .site-nav{{padding:10px 16px;flex-wrap:wrap;gap:8px}}
  .nav-right{{width:100%;justify-content:flex-start;gap:6px;margin-left:0}}
  .site-nav a,.nav-btn{{padding:6px 10px;font-size:13px}}
  .assembler-box{{padding:16px 18px}}
  .step-card{{padding:14px 16px}}
  .step-header{{flex-direction:column;align-items:flex-start;gap:10px}}
  .step-toolbar{{margin-left:0;width:100%;justify-content:flex-start}}
  .output-actions{{width:100%}}
  .copy-main-btn{{width:100%;justify-content:center}}
  .modal-grid{{grid-template-columns:repeat(auto-fill,minmax(95px,1fr))}}
}}
</style>
{IMAGE_FALLBACK_SCRIPT}
</head><body>
<header class="sticky-header">
<nav class="site-nav" aria-label="画廊导航"><a href="index.html" data-i18n="stylesNav">风格画廊</a><a href="layouts.html" data-i18n="layoutsNav">图型画廊</a><a href="colors.html" data-i18n="colorsNav">色彩画廊</a><a href="assets.html" data-i18n="assetsNav">自建图库</a><a href="tutorials.html" aria-current="page" data-i18n="tutorialsNav">提示词</a><div class="nav-right"><a class="nav-ext" href="https://github.com/yang0/handraw-style" target="_blank" rel="noopener noreferrer" title="GitHub 仓库"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a><a class="nav-ext" href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer" title="X (Twitter) @yang02010"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>X (@yang02010)</a><button class="nav-btn" id="lang-btn" type="button" aria-label="Switch Language">🌐 EN / 中</button></div></nav>
</header>
<main>
<!-- Prompt Assembler Studio -->
<section class="assembler-section">
  <div class="assembler-box">
    <div class="assembler-header">
      <div class="assembler-title-wrap">
        <h1 class="assembler-title" data-i18n="assemblerTitle">🛠️ 提示词拼装器</h1>
      </div>
      <p class="assembler-sub" data-i18n="assemblerSub">交互式点选图型、风格与色彩，实时拼装出图指令。</p>
    </div>

    <div class="assembler-steps">
      <!-- Step 1: 出图模式与留白 -->
      <section class="step-card">
        <div class="step-header">
          <div class="step-title-wrap">
            <span class="step-badge">1</span>
            <h2 class="step-title" data-i18n="step1Title">出图模式与留白</h2>
          </div>
        </div>
        <div class="step-body">
          <div class="mode-row">
            <div class="mode-item">
              <span class="mode-label" data-i18n="modeLabel">出图模式：</span>
              <div class="mode-group" role="radiogroup" aria-label="出图模式">
                <button type="button" class="mode-btn is-active" data-mode="pure" data-i18n="modePure">纯图</button>
                <button type="button" class="mode-btn" data-mode="graphic-text" data-i18n="modeGraphicText">图文</button>
                <button type="button" class="mode-btn" data-mode="poster" data-i18n="modePoster">海报</button>
                <button type="button" class="mode-btn" data-mode="article-illust" data-i18n="modeArticleIllust">文章插图</button>
                <button type="button" class="mode-btn" data-mode="article-cover" data-i18n="modeArticleCover">文章封面</button>
                <button type="button" class="mode-btn" data-mode="photo" data-i18n="modePhoto">摄影</button>
              </div>
            </div>
            <div class="mode-item">
              <span class="mode-label" data-i18n="whitespaceLabel">留白：</span>
              <div class="density-group" role="radiogroup" aria-label="留白">
                <button type="button" class="density-btn is-active" data-whitespace="normal" data-i18n="whitespaceNormal">正常</button>
                <button type="button" class="density-btn" data-whitespace="moderate" data-i18n="whitespaceModerate" title="【大量留白】">适中</button>
                <button type="button" class="density-btn" data-whitespace="high" data-i18n="whitespaceHigh" title="【大量留白，场景只显示必要部分，不要显示全】">多</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 2: 画面主题与内容 -->
      <section class="step-card">
        <div class="step-header">
          <div class="step-title-wrap">
            <span class="step-badge">2</span>
            <h2 class="step-title" data-i18n="step2Title">画面主题与内容</h2>
          </div>
        </div>
        <div class="step-body">
          <div class="form-group">
            <textarea id="input-theme" class="text-input text-area" rows="2" placeholder="输入画面主题，亦可输入本地文件或文件夹路径（如：秋天的第一杯奶茶 / 窗台晒太阳的猫咪，或 D:/path/to/...）..." aria-label="画面主题、文件或文件夹路径"></textarea>
          </div>

          <!-- Extra fields for poster mode only -->
          <div class="extra-fields-grid" id="poster-extra-fields" hidden>
            <div class="form-group">
              <label for="input-audience" class="form-label" data-i18n="audienceLabel">受众：</label>
              <input type="text" id="input-audience" class="text-input" placeholder="例如：年轻都市白领 / 露营爱好者 / 亲子家庭...">
            </div>
            <div class="form-group">
              <label for="input-channel" class="form-label" data-i18n="channelLabel">海报投放渠道：</label>
              <input type="text" id="input-channel" class="text-input" placeholder="例如：小红书 / 微信公众号封面 / 线下门店立牌...">
            </div>
          </div>

          <!-- Extra fields for photo mode only -->
          <div class="extra-fields-grid single-col" id="photo-extra-fields" hidden>
            <div class="form-group mood-form-group">
              <div class="selector-options-row">
                <label for="input-shoot-type" class="form-label" data-i18n="shootTypeLabel">拍摄类型：</label>
                <div class="mood-presets-row" role="group" aria-label="拍摄类型快捷预设">
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="情侣" data-type-en="Couple" data-i18n="shootTypeCouple">情侣</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="婚纱" data-type-en="Wedding" data-i18n="shootTypeWedding">婚纱</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="个人写真" data-type-en="Solo Portrait" data-i18n="shootTypeSolo">个人写真</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="亲子全家福" data-type-en="Family" data-i18n="shootTypeFamily">亲子全家福</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="古风汉服" data-type-en="Ancient Hanfu" data-i18n="shootTypeHanfu">古风汉服</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="新中式" data-type-en="New Chinese" data-i18n="shootTypeNewChinese">新中式</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="复古港风" data-type-en="Vintage HK" data-i18n="shootTypeVintageHK">复古港风</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="Cosplay" data-type-en="Cosplay" data-i18n="shootTypeCosplay">Cosplay</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="旅行抓拍" data-type-en="Travel Snapshot" data-i18n="shootTypeTravel">旅行抓拍</button>
                  <button type="button" class="shoot-type-preset-btn" data-type-zh="职场肖像" data-type-en="Professional Portrait" data-i18n="shootTypeCareer">职场肖像</button>
                </div>
              </div>
              <div class="ratio-input-wrap" style="max-width:100%">
                <input type="text" id="input-shoot-type" class="text-input ratio-input" placeholder="点选上方标签，或手动输入/修改拍摄类型...">
                <button type="button" id="btn-clear-shoot-type" class="ratio-clear-btn" title="清空拍摄类型" aria-label="清空拍摄类型" hidden>×</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 3: 画幅比例与情绪 -->
      <section class="step-card">
        <div class="step-header">
          <div class="step-title-wrap">
            <span class="step-badge">3</span>
            <h2 class="step-title" data-i18n="step3Title">画幅比例与情绪</h2>
          </div>
        </div>
        <div class="step-body">
          <!-- Ratio Selector Form Group -->
          <div class="form-group ratio-form-group">
            <div class="selector-options-row">
              <label for="input-ratio" class="form-label" data-i18n="ratioLabel">画幅比例：</label>
              <div class="ratio-presets-row" role="group" aria-label="画幅比例快捷预设">
                <button type="button" class="ratio-preset-btn is-active" data-ratio="3:4" data-i18n="presetXiaohongshu">小红书/公众号贴图 (3:4)</button>
                <button type="button" class="ratio-preset-btn" data-ratio="2.35:1" data-i18n="presetWechatCover">公众号封面 (2.35:1)</button>
                <button type="button" class="ratio-preset-btn" data-ratio="5:2" data-i18n="presetXCover">X文章封面 (5:2)</button>
                <button type="button" class="ratio-preset-btn" data-ratio="4:3" data-i18n="presetArticleIllust">文章插图 (4:3)</button>
                <button type="button" class="ratio-preset-btn" data-ratio="1:1" data-i18n="presetSquare">方块 (1:1)</button>
                <button type="button" class="ratio-preset-btn" data-ratio="9:16" data-i18n="presetVerticalStory">手机全屏 (9:16)</button>
              </div>
            </div>
            <div class="ratio-input-wrap">
              <input type="text" id="input-ratio" class="text-input ratio-input" value="3:4" placeholder="输入或点击上方预设，例如：3:4、5:2、1:1（可手填）">
              <button type="button" id="btn-clear-ratio" class="ratio-clear-btn" title="清空比例" aria-label="清空比例">×</button>
            </div>
          </div>

          <!-- Mood Selector Form Group -->
          <div class="form-group mood-form-group">
            <div class="selector-options-row">
              <label for="input-mood" class="form-label" data-i18n="moodLabel">情绪：</label>
              <div class="mood-presets-row" role="group" aria-label="情绪快捷预设">
                <button type="button" class="mood-preset-btn" data-mood-zh="治愈" data-mood-en="Healing" data-i18n="moodHealing">治愈</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="童趣" data-mood-en="Childlike" data-i18n="moodChildlike">童趣</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="松弛" data-mood-en="Relaxed" data-i18n="moodRelaxed">松弛</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="幽默" data-mood-en="Humorous" data-i18n="moodHumorous">幽默</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="诗意" data-mood-en="Poetic" data-i18n="moodPoetic">诗意</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="浪漫" data-mood-en="Romantic" data-i18n="moodRomantic">浪漫</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="活力" data-mood-en="Vibrant" data-i18n="moodVibrant">活力</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="微丧" data-mood-en="Melancholy" data-i18n="moodMelancholy">微丧</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="孤寂" data-mood-en="Solitary" data-i18n="moodSolitary">孤寂</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="紧张" data-mood-en="Tense" data-i18n="moodTense">紧张</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="庄严" data-mood-en="Solemn" data-i18n="moodSolemn">庄严</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="荒诞" data-mood-en="Absurd" data-i18n="moodAbsurd">荒诞</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="恐怖" data-mood-en="Eerie" data-i18n="moodEerie">恐怖</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="神秘" data-mood-en="Mysterious" data-i18n="moodMysterious">神秘</button>
                <button type="button" class="mood-preset-btn" data-mood-zh="激烈" data-mood-en="Intense" data-i18n="moodIntense">激烈</button>
              </div>
            </div>
            <div class="ratio-input-wrap">
              <input type="text" id="input-mood" class="text-input ratio-input" placeholder="输入或点选上方情绪（可多选，例如：治愈、松弛）">
              <button type="button" id="btn-clear-mood" class="ratio-clear-btn" title="清空情绪" aria-label="清空情绪" hidden>×</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 4: 画廊视觉元素搭配 -->
      <section class="step-card">
        <div class="step-header">
          <div class="step-title-wrap">
            <span class="step-badge">4</span>
            <h2 class="step-title" data-i18n="step4Title">视觉资产与风格搭配</h2>
            <label class="fusion-checkbox-wrap" id="fusion-checkbox-wrap">
              <input type="checkbox" id="checkbox-fusion" class="fusion-checkbox">
              <span class="fusion-checkbox-text" data-i18n="fusionCheckboxLabel">风格融合</span>
            </label>
            <label class="fusion-checkbox-wrap" id="tone-checkbox-wrap">
              <input type="checkbox" id="checkbox-tone" class="fusion-checkbox">
              <span class="fusion-checkbox-text" data-i18n="toneCheckboxLabel">影调</span>
            </label>
          </div>
          <div class="step-toolbar">
            <button type="button" id="btn-gacha" class="btn-tool" title="随机抽选图型、风格与色彩">
              <span>🎲</span>
              <span data-i18n="gachaBtn">智能随机抽卡</span>
            </button>
            <button type="button" id="btn-reset" class="btn-tool" title="清空全部已选">
              <span>🧹</span>
              <span data-i18n="resetBtn">一键清空</span>
            </button>
          </div>
        </div>
        <div class="step-body">
          <!-- Visual Benchmark Assets Module (Multi-Asset Tray) -->
          <div class="assets-module" id="assets-module">
            <div class="assets-module-header">
              <div class="assets-header-left">
                <span class="assets-module-title">👤 <span data-i18n="assetsTrayTitle">自建图库</span></span>
                <span class="assets-module-desc" data-i18n="assetsTrayDesc">可选 · 支持多选跨媒介参考图（垫图），出图时保持主体视觉绝对一致</span>
              </div>
              <div class="assets-header-actions">
                <button type="button" id="btn-clear-assets" class="btn-clear-assets" hidden data-i18n="clearAssetsBtn">清空已选资产</button>
                <button type="button" class="btn-add-assets" data-picker="asset">
                  <span>＋</span>
                  <span data-i18n="addAssetsBtn">添加自建资产</span>
                </button>
              </div>
            </div>

            <!-- Empty state: large dashed trigger -->
            <button type="button" id="assets-empty-trigger" class="assets-empty-trigger" data-picker="asset">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/></svg>
              <span data-i18n="assetsEmptyText">点击按图添加自建资产（支持同时多选角色 IP、道具 PR、场景 SCN 基准图）</span>
            </button>

            <!-- Filled tray: cards flow -->
            <div id="assets-tray-cards" class="assets-tray-cards" hidden></div>
          </div>

          <div class="slots-grid" id="slots-grid">
            <!-- Layout Slot -->
            <div class="slot-card" id="slot-layout">
              <div class="slot-header">
                <span class="slot-title">📐 <span data-i18n="slotLayout">图型</span></span>
                <span class="slot-optional" id="slot-layout-optional" data-i18n="optionalLayout">可选 ({layouts_count})</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="layout">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
                <span data-i18n="pickLayoutText">按图选择图型 ({layouts_count})</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap"><img src="" alt=""></div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="layout" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="layout" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>

            <!-- Single Style Slot (Default) -->
            <div class="slot-card" id="slot-style">
              <div class="slot-header">
                <span class="slot-title">🎨 <span data-i18n="slotStyle">风格</span></span>
                <span class="slot-optional" data-i18n="optionalStyle">可选 ({styles_count})</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="style">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 2a4.5 4.5 0 0 0 0 9 4.5 4.5 0 0 1 0 9 10 10 0 0 1 0-18z"/></svg>
                <span data-i18n="pickStyleText">按图选择风格</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap"><img src="" alt=""></div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="style" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="style" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>

            <!-- Fusion Character Style Slot (Hidden when not fusion) -->
            <div class="slot-card" id="slot-char-style" hidden>
              <div class="slot-header">
                <span class="slot-title">🎭 <span data-i18n="slotCharStyle">角色风格</span></span>
                <span class="slot-optional" data-i18n="optionalCharStyle">可选 ({styles_count})</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="char-style">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 2a4.5 4.5 0 0 0 0 9 4.5 4.5 0 0 1 0 9 10 10 0 0 1 0-18z"/></svg>
                <span data-i18n="pickCharStyleText">按图选择角色风格</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap"><img src="" alt=""></div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="char-style" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="char-style" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>

            <!-- Fusion Scene Style Slot (Hidden when not fusion) -->
            <div class="slot-card" id="slot-scene-style" hidden>
              <div class="slot-header">
                <span class="slot-title">🌄 <span data-i18n="slotSceneStyle">场景风格</span></span>
                <span class="slot-optional" data-i18n="optionalSceneStyle">可选 ({styles_count})</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="scene-style">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                <span data-i18n="pickSceneStyleText">按图选择场景风格</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap"><img src="" alt=""></div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="scene-style" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="scene-style" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>

            <!-- Theme Color Slot -->
            <div class="slot-card" id="slot-color">
              <div class="slot-header">
                <span class="slot-title">🌈 <span data-i18n="slotColor">主题色</span></span>
                <span class="slot-optional" data-i18n="optionalColor">可选 (36)</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="color">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 15h18"/></svg>
                <span data-i18n="pickColorText">按图选择色彩</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap"><img src="" alt=""></div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="color" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="color" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>

            <!-- Tone Slot (Hidden when not enabled) -->
            <div class="slot-card" id="slot-tone" hidden>
              <div class="slot-header">
                <span class="slot-title">💡 <span data-i18n="slotTone">影调</span></span>
                <span class="slot-optional" id="slot-tone-optional" data-i18n="optionalTone">可选 ({tones_count}) · 多选</span>
              </div>
              <button type="button" class="slot-trigger" data-picker="tone">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                <span data-i18n="pickToneText">按图选择影调 ({tones_count})</span>
              </button>
              <div class="slot-filled" hidden>
                <div class="slot-img-wrap">
                  <img src="" alt="">
                  <span class="slot-count-badge" id="slot-tone-badge" hidden>+1</span>
                </div>
                <div class="slot-meta">
                  <span class="slot-code"></span>
                  <span class="slot-name"></span>
                </div>
                <div class="slot-actions">
                  <button type="button" class="btn-change" data-picker="tone" data-i18n="changeBtn">更换</button>
                  <button type="button" class="btn-clear" data-clear="tone" title="清除选择" aria-label="清除选择">×</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 5: 拼装出图指令 -->
      <section class="step-card step-output-card">
        <div class="step-header">
          <div class="step-title-wrap">
            <span class="step-badge">5</span>
            <h2 class="step-title output-title" data-i18n="step5Title">拼装生成的出图指令</h2>
            <label class="fusion-checkbox-wrap" id="batch-checkbox-wrap">
              <input type="checkbox" id="checkbox-batch" class="fusion-checkbox">
              <span class="fusion-checkbox-text" data-i18n="batchCheckboxLabel">批量出图</span>
            </label>
            <label class="fusion-checkbox-wrap" id="mix-layouts-checkbox-wrap" hidden>
              <input type="checkbox" id="checkbox-mix-layouts" class="fusion-checkbox">
              <span class="fusion-checkbox-text" data-i18n="mixLayoutsCheckboxLabel">混合多种图型</span>
            </label>
          </div>
          <div class="output-actions">
            <button type="button" id="btn-copy-assembled" class="copy-main-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span id="copy-btn-text" data-i18n="copyPromptBtn">复制出图指令</span>
            </button>
          </div>
        </div>
        <div class="step-body">
          <pre class="assembled-text" id="assembled-text"></pre>
        </div>
      </section>
    </div>
  </div>
</section>

<!-- Retained Guides -->
<section class="guides-section">
  <h2 class="guides-title" data-i18n="guidesTitle">📖 实战思维与技巧说明</h2>
  <div class="tutorials-list" id="tutorials-list">{cards_str}</div>
</section>
</main>

<!-- Reusable Visual Picker Dialog -->
<dialog id="picker-dialog" class="picker-modal" aria-labelledby="picker-title">
  <div class="modal-header">
    <h3 id="picker-title" class="modal-title">选择</h3>
    <button type="button" class="modal-close-btn close" aria-label="关闭">关闭 ×</button>
  </div>
  <div class="modal-nav" id="picker-filters"></div>
  <div class="modal-search-wrap">
    <input type="search" id="picker-search" class="modal-search" placeholder="输入编号或名称过滤...">
  </div>
  <div class="modal-grid" id="picker-grid"></div>
  <div class="modal-footer" id="modal-asset-footer" hidden>
    <div class="modal-footer-info" id="modal-asset-summary">已选择 0 项资产</div>
    <div class="modal-footer-actions">
      <button type="button" id="btn-modal-clear-assets" class="btn-modal-action btn-modal-clear" data-i18n="modalAssetClearBtn">清空全部</button>
      <button type="button" id="btn-modal-confirm-assets" class="btn-modal-action btn-modal-confirm" data-i18n="modalAssetConfirmBtn">完成选择</button>
    </div>
  </div>
</dialog>



<script src="../../../images/custom/custom_assets.js" onerror="window.CUSTOM_ASSETS_DATA=null;"></script>
<script>
const OFFICIAL_ASSETS_DATA = {assets_json_str};
let ASSETS_DATA = [...OFFICIAL_ASSETS_DATA];
if (window.CUSTOM_ASSETS_DATA && typeof window.CUSTOM_ASSETS_DATA === 'object') {{
  ['characters', 'props', 'scenes'].forEach(cat => {{
    const list = window.CUSTOM_ASSETS_DATA[cat] || [];
    if (Array.isArray(list)) {{
      list.forEach(item => {{
        if (item && item.id && !ASSETS_DATA.some(x => x.id === item.id)) {{
          ASSETS_DATA.push({{
            id: item.id,
            name: item.name || item.id,
            name_en: item.name_en || item.name || item.id,
            cat: cat,
            img: item.image || '',
            tags: item.tags || ["自建资产"],
            is_custom: true
          }});
        }}
      }});
    }}
  }});
}}
const STYLES_DATA = {styles_json_str};
const LAYOUTS_DATA = {layouts_json_str};
const COLORS_DATA = {colors_json_str};
const COLOR_CATEGORIES = {color_categories_json_str};
const TONES_DATA = {tones_json_str};

const langBtn=document.querySelector('#lang-btn');
const inputTheme=document.querySelector('#input-theme'),themeLabelText=document.querySelector('#theme-label-text'),inputAudience=document.querySelector('#input-audience'),inputChannel=document.querySelector('#input-channel'),posterExtraFields=document.querySelector('#poster-extra-fields');
const inputShootType=document.querySelector('#input-shoot-type'),photoExtraFields=document.querySelector('#photo-extra-fields'),btnClearShootType=document.querySelector('#btn-clear-shoot-type');
const inputRatio=document.querySelector('#input-ratio'),btnClearRatio=document.querySelector('#btn-clear-ratio');
const inputMood=document.querySelector('#input-mood'),btnClearMood=document.querySelector('#btn-clear-mood');
const assembledText=document.querySelector('#assembled-text'),btnCopyAssembled=document.querySelector('#btn-copy-assembled'),copyBtnText=document.querySelector('#copy-btn-text');
const pickerDialog=document.querySelector('#picker-dialog'),pickerTitle=document.querySelector('#picker-title'),pickerFilters=document.querySelector('#picker-filters'),pickerSearch=document.querySelector('#picker-search'),pickerGrid=document.querySelector('#picker-grid');
const checkboxFusion=document.querySelector('#checkbox-fusion'),fusionWrap=document.querySelector('#fusion-checkbox-wrap');
const checkboxTone=document.querySelector('#checkbox-tone'),toneWrap=document.querySelector('#tone-checkbox-wrap'),slotTone=document.querySelector('#slot-tone');
const checkboxBatch=document.querySelector('#checkbox-batch'),batchWrap=document.querySelector('#batch-checkbox-wrap');
const checkboxMixLayouts=document.querySelector('#checkbox-mix-layouts'),mixLayoutsWrap=document.querySelector('#mix-layouts-checkbox-wrap');
const slotsGrid=document.querySelector('#slots-grid'),slotStyle=document.querySelector('#slot-style'),slotCharStyle=document.querySelector('#slot-char-style'),slotSceneStyle=document.querySelector('#slot-scene-style');
const modalAssetFooter=document.querySelector('#modal-asset-footer'),modalAssetSummary=document.querySelector('#modal-asset-summary');
const btnModalClearAssets=document.querySelector('#btn-modal-clear-assets'),btnModalConfirmAssets=document.querySelector('#btn-modal-confirm-assets');
const assetsTrayCards=document.querySelector('#assets-tray-cards'),assetsEmptyTrigger=document.querySelector('#assets-empty-trigger'),btnClearAssets=document.querySelector('#btn-clear-assets');

let currentMode = 'pure'; // 'pure' | 'graphic-text' | 'poster' | 'article-illust' | 'photo'
let currentWhitespace = 'normal'; // 'normal' | 'moderate' | 'high'
let selectedAssets = [];
let selectedLayout = null;
let selectedStyle = null;
let selectedCharStyle = null;
let selectedSceneStyle = null;
let selectedColor = null;
let selectedTones = [];
let currentPickerType = null;
let currentPickerFilter = 'all';
let isFusionActive = false;
let isToneActive = false;
let isBatchActive = false;
let isMixLayoutsActive = false;



const I18N = {{
  zh: {{
    pageTitle: "手绘 Skill 提示词拼装器",
    stylesNav: "风格画廊",
    layoutsNav: "图型画廊",
    colorsNav: "色彩画廊",
    assetsNav: "自建图库",
    tutorialsNav: "提示词",
    assemblerTitle: "🛠️ 提示词拼装器",
    assemblerSub: "交互式点选图型、风格与色彩，实时拼装出图指令。",
    fusionCheckboxLabel: "风格融合",
    toneCheckboxLabel: "影调",
    batchCheckboxLabel: "批量出图",
    mixLayoutsCheckboxLabel: "混合多种图型",
    step1Title: "出图模式与留白",
    step2Title: "画面主题与内容",
    step3Title: "画幅比例与情绪",
    step4Title: "视觉资产与风格搭配",
    step5Title: "拼装生成的出图指令",
    assetsTrayTitle: "自建图库",
    assetsTrayDesc: "可选 · 支持多选跨媒介参考图（垫图），出图时保持主体视觉绝对一致",
    assetsEmptyText: "点击按图添加自建资产（支持同时多选角色 IP、道具 PR、场景 SCN 基准图）",
    addAssetsBtn: "添加自建资产",
    clearAssetsBtn: "清空已选资产",
    modalAssetClearBtn: "清空全部",
    modalAssetConfirmBtn: "完成选择",
    modeLabel: "出图模式：",
    modePure: "纯图",
    modeGraphicText: "图文",
    modePoster: "海报",
    modeArticleIllust: "文章插图",
    modeArticleCover: "文章封面",
    modePhoto: "摄影",
    whitespaceLabel: "留白：",
    whitespaceNormal: "正常",
    whitespaceModerate: "适中",
    whitespaceHigh: "多",
    whitespaceModeratePrompt: "【大量留白】",
    whitespaceHighPrompt: "【大量留白，场景只显示必要部分，不要显示全】",
    themeLabel: "主题：",
    articlePathLabel: "文件或文件夹地址：",
    articleCoverPathLabel: "文件/文件夹地址或内容：",
    shootTypeLabel: "拍摄类型：",
    audienceLabel: "受众：",
    channelLabel: "海报投放渠道：",
    themePlaceholder: "输入画面主题，亦可输入本地文件或文件夹路径（例如：秋天的第一杯奶茶 / 窗台晒太阳的猫咪，或 D:\\\\path\\\\to\\\\...）...",
    themePhotoPlaceholder: "选填：输入特定主题或场景，亦可输入本地文件或文件夹路径（如：海边夕阳 / 90年代港风），不填由AI推荐...",
    articlePathPlaceholder: "请输入本地文件或文件夹绝对路径（支持单篇或批量配图，例如：D:\\\\path\\\\to\\\\article.md 或文件夹）...",
    articleCoverPathPlaceholder: "请输入本地文件或文件夹绝对路径（例如：D:\\\\path\\\\to\\\\article.md），或直接粘贴文章内容...",
    articleCoverFixedPrompt: "先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。",
    shootTypePlaceholder: "点选上方标签，或手动输入/修改拍摄类型...",
    shootTypeCouple: "情侣",
    shootTypeWedding: "婚纱",
    shootTypeSolo: "个人写真",
    shootTypeFamily: "亲子全家福",
    shootTypeHanfu: "古风汉服",
    shootTypeNewChinese: "新中式",
    shootTypeVintageHK: "复古港风",
    shootTypeCosplay: "Cosplay",
    shootTypeTravel: "旅行抓拍",
    shootTypeCareer: "职场肖像",
    audiencePlaceholder: "例如：年轻都市白领 / 露营爱好者 / 亲子家庭...",
    channelPlaceholder: "例如：小红书 / 微信公众号封面 / 线下门店立牌...",
    ratioLabel: "画幅比例：",
    ratioPlaceholder: "输入或点击上方预设，例如：3:4、5:2、1:1（可手填）",
    presetXiaohongshu: "小红书/公众号贴图 (3:4)",
    presetWechatCover: "公众号封面 (2.35:1)",
    presetXCover: "X文章封面 (5:2)",
    presetArticleIllust: "文章插图 (4:3)",
    presetSquare: "方块 (1:1)",
    presetVerticalStory: "手机全屏 (9:16)",
    moodLabel: "情绪：",
    moodPlaceholder: "输入或点选上方情绪（可多选，例如：治愈、松弛）",
    moodHealing: "治愈",
    moodRelaxed: "松弛",
    moodHumorous: "幽默",
    moodPoetic: "诗意",
    moodRomantic: "浪漫",
    moodVibrant: "活力",
    moodMelancholy: "微丧",
    moodChildlike: "童趣",
    moodSolitary: "孤寂",
    moodTense: "紧张",
    moodSolemn: "庄严",
    moodAbsurd: "荒诞",
    moodEerie: "恐怖",
    moodMysterious: "神秘",
    moodIntense: "激烈",
    slotAsset: "自建资产",
    slotLayout: "图型",
    slotStyle: "风格",
    slotCharStyle: "角色风格",
    slotSceneStyle: "场景风格",
    slotColor: "主题色",
    slotTone: "影调",
    optional: "可选",
    optionalAsset: "可选 ({assets_count})",
    optionalLayout: "可选 ({layouts_count})",
    optionalStyle: "可选 ({styles_count})",
    optionalCharStyle: "可选 ({styles_count})",
    optionalSceneStyle: "可选 ({styles_count})",
    optionalColor: "可选 (36)",
    optionalTone: "可选 ({tones_count}) · 多选",
    layoutNotApplicable: "不适用",
    pickAssetText: "按图选择自建资产",
    pickLayoutText: "按图选择图型 ({layouts_count})",
    pickStyleText: "按图选择风格 ({styles_count})",
    pickCharStyleText: "按图选择角色风格",
    pickSceneStyleText: "按图选择场景风格",
    pickColorText: "按图选择主题色 (36)",
    pickToneText: "按图选择影调 ({tones_count})",
    changeBtn: "更换",
    gachaBtn: "智能随机抽卡",
    resetBtn: "一键清空",
    outputTitle: "📋 拼装生成的出图指令：",
    copyPromptBtn: "复制出图指令",
    copied: "已复制！",
    guidesTitle: "📖 实战思维与技巧说明",
    formulaLabel: "示例提示词：",
    searchPlaceholder: "输入编号或名称过滤...",
    pickerTitleAsset: "选择视觉资产（角色 / 道具 / 场景）",
    pickerTitleLayout: "选择图型 ({layouts_count})",
    pickerTitleStyle: "选择视觉风格 ({styles_count})",
    pickerTitleCharStyle: "选择角色风格",
    pickerTitleSceneStyle: "选择场景风格",
    styleConflictAlert: "角色风格与场景风格必须不同，请选择不同的风格！",
    pickerTitleColor: "选择主题色 (36)",
    pickerTitleTone: "选择影调 ({tones_count} · 可多选)",
    modalToneCount: "已选择 {{count}} 项影调",
    filterToneKey: "明暗阶调",
    filterToneContrast: "反差过渡",
    filterToneAtmosphere: "氛围风格",
    filterAll: "全部",
    filterCharacters: "角色库",
    filterProps: "道具库",
    filterScenes: "场景库",
    filterSocialCard: "社媒卡 (SC)",
    filterInfographic: "信息图 (IG)",
    filterComicStoryboard: "漫画分镜 (SB)",
    filterIpCharacter: "IP设计 (IP)",
    filterEcommerce: "电商 (EC)",
    filterBlue: "经典蓝系",
    filterGreen: "清新绿系",
    filterRed: "古典红绿",
    filterPurple: "浪漫粉紫",
    filterWarm: "暖阳大地",
    filterNeutral: "中性色系",
    fallbackPrompt: "其他你帮我选择",
    themeEmptyText: "【输入主题】",
    articlePathEmptyText: "【输入文件或文件夹地址】",
    audienceEmptyText: "【输入受众】",
    channelEmptyText: "【输入海报投放渠道】",
    langBtn: "🌐 English"
  }},
  en: {{
    pageTitle: "Prompt Assembler | Handraw Style Prompter",
    stylesNav: "Styles",
    layoutsNav: "Layouts",
    colorsNav: "Colors",
    assetsNav: "Custom Library",
    tutorialsNav: "Prompts",
    assemblerTitle: "🛠️ Prompt Assembler",
    assemblerSub: "Visually select layout, style, and color to assemble prompt commands in real time.",
    fusionCheckboxLabel: "Style Fusion",
    toneCheckboxLabel: "Tone",
    batchCheckboxLabel: "Batch Generation",
    mixLayoutsCheckboxLabel: "Mix Multiple Layouts",
    step1Title: "Mode & Negative Space",
    step2Title: "Theme & Content",
    step3Title: "Aspect Ratio & Mood",
    step4Title: "Visual Assets & Style Composition",
    step5Title: "Generated Prompt Command",
    assetsTrayTitle: "Custom Library",
    assetsTrayDesc: "Optional · Multi-select reference images to maintain consistent character, prop, and scene appearance",
    assetsEmptyText: "Click to select visual benchmark assets (Multi-select characters, props, scenes)",
    addAssetsBtn: "Add Assets",
    clearAssetsBtn: "Clear Assets",
    modalAssetClearBtn: "Clear All",
    modalAssetConfirmBtn: "Done",
    modeLabel: "Mode:",
    modePure: "Image Only",
    modeGraphicText: "Graphic-Text",
    modePoster: "Poster",
    modeArticleIllust: "Article Illustration",
    modeArticleCover: "Article Cover",
    modePhoto: "Photography",
    whitespaceLabel: "Negative Space:",
    whitespaceNormal: "Normal",
    whitespaceModerate: "Moderate",
    whitespaceHigh: "Generous",
    whitespaceModeratePrompt: "[Generous negative space]",
    whitespaceHighPrompt: "[Generous negative space, scene shows only essential parts, do not show in full]",
    themeLabel: "Theme:",
    articlePathLabel: "File or Folder Path:",
    articleCoverPathLabel: "File / Folder Path or Text:",
    shootTypeLabel: "Shoot Type:",
    audienceLabel: "Audience:",
    channelLabel: "Distribution Channel:",
    themePlaceholder: "Enter theme, or local file/folder path (e.g. Autumn milk tea / Cat on windowsill, or D:\\\\path\\\\to\\\\dir)...",
    themePhotoPlaceholder: "Optional: Enter specific theme or setting, or local file/folder path (e.g. Sunset beach / Vintage cafe), or leave empty for AI recommendation...",
    articlePathPlaceholder: "Enter absolute local file or folder path (supports single or batch illustration, e.g. D:\\\\path\\\\to\\\\article.md or folder)...",
    articleCoverPathPlaceholder: "Enter absolute local file or folder path (e.g. D:\\\\path\\\\to\\\\article.md), or paste article text...",
    articleCoverFixedPrompt: "Design a visual metaphor first, then generate the image. Ensure the main title is bold and prominent, with few or no small text. Pick the rest of the design for me.",
    shootTypePlaceholder: "Click tags above, or type/edit shoot type...",
    shootTypeCouple: "Couple",
    shootTypeWedding: "Wedding",
    shootTypeSolo: "Solo Portrait",
    shootTypeFamily: "Family",
    shootTypeHanfu: "Ancient Hanfu",
    shootTypeNewChinese: "New Chinese",
    shootTypeVintageHK: "Vintage HK",
    shootTypeCosplay: "Cosplay",
    shootTypeTravel: "Travel Snapshot",
    shootTypeCareer: "Professional Portrait",
    audiencePlaceholder: "e.g. Young urban professionals / Campers / Families...",
    channelPlaceholder: "e.g. Instagram / RED / Store poster stand...",
    ratioLabel: "Aspect Ratio:",
    ratioPlaceholder: "Enter or click preset, e.g. 3:4, 5:2, 1:1 (customizable)",
    presetXiaohongshu: "RED / WeChat Sticker (3:4)",
    presetWechatCover: "WeChat Official Cover (2.35:1)",
    presetXCover: "X Article Cover (5:2)",
    presetArticleIllust: "Article Illustration (4:3)",
    presetSquare: "Square (1:1)",
    presetVerticalStory: "Full Screen (9:16)",
    moodLabel: "Mood:",
    moodPlaceholder: "Type or pick moods (e.g. Healing, Relaxed)",
    moodHealing: "Healing",
    moodRelaxed: "Relaxed",
    moodHumorous: "Humorous",
    moodPoetic: "Poetic",
    moodRomantic: "Romantic",
    moodVibrant: "Vibrant",
    moodMelancholy: "Melancholy",
    moodChildlike: "Childlike",
    moodSolitary: "Solitary",
    moodTense: "Tense",
    moodSolemn: "Solemn",
    moodAbsurd: "Absurd",
    moodEerie: "Eerie",
    moodMysterious: "Mysterious",
    moodIntense: "Intense",
    slotAsset: "Asset",
    slotLayout: "Layout",
    slotStyle: "Style",
    slotCharStyle: "Character Style",
    slotSceneStyle: "Scene Style",
    slotColor: "Theme Color",
    slotTone: "Tone",
    optional: "Optional",
    optionalAsset: "Optional ({assets_count})",
    optionalLayout: "Optional ({layouts_count})",
    optionalStyle: "Optional ({styles_count})",
    optionalCharStyle: "Optional ({styles_count})",
    optionalSceneStyle: "Optional ({styles_count})",
    optionalColor: "Optional (36)",
    optionalTone: "Optional ({tones_count}) · Multi",
    layoutNotApplicable: "N/A",
    pickAssetText: "Pick Custom Asset",
    pickLayoutText: "Pick Layout ({layouts_count})",
    pickStyleText: "Pick Style ({styles_count})",
    pickCharStyleText: "Pick Character Style",
    pickSceneStyleText: "Pick Scene Style",
    pickColorText: "Pick Theme Color (36)",
    pickToneText: "Pick Visual Tone ({tones_count})",
    changeBtn: "Change",
    gachaBtn: "Random Gacha",
    resetBtn: "Reset All",
    outputTitle: "📋 Assembled Generation Command:",
    copyPromptBtn: "Copy Command",
    copied: "Copied!",
    guidesTitle: "📖 Practical Guides & Principles",
    formulaLabel: "Example Prompt:",
    searchPlaceholder: "Search ID or name...",
    pickerTitleAsset: "Select Visual Asset (Character / Prop / Scene)",
    pickerTitleLayout: "Select Layout ({layouts_count})",
    pickerTitleStyle: "Select Visual Style ({styles_count})",
    pickerTitleCharStyle: "Select Character Style",
    pickerTitleSceneStyle: "Select Scene Style",
    styleConflictAlert: "Character style and scene style must be different!",
    pickerTitleColor: "Select Theme Color (36)",
    pickerTitleTone: "Select Tone ({tones_count} · Multi-select)",
    modalToneCount: "{{count}} Tone(s) Selected",
    filterToneKey: "Key & Exposure",
    filterToneContrast: "Contrast & Transition",
    filterToneAtmosphere: "Atmosphere & Style",
    filterAll: "All",
    filterCharacters: "Characters",
    filterProps: "Props",
    filterScenes: "Scenes",
    filterSocialCard: "Social Cards (SC)",
    filterInfographic: "Infographics (IG)",
    filterComicStoryboard: "Comic Storyboards (SB)",
    filterIpCharacter: "IP Design (IP)",
    filterEcommerce: "E-commerce (EC)",
    filterBlue: "Classic Blue",
    filterGreen: "Fresh Green",
    filterRed: "Classic Red & Vintage",
    filterPurple: "Romantic Pink & Purple",
    filterWarm: "Warm Sun & Earth",
    filterNeutral: "Classic Neutral Tones",
    fallbackPrompt: "pick the rest for me",
    themeEmptyText: "[Enter Theme]",
    articlePathEmptyText: "[Enter File or Folder Path]",
    audienceEmptyText: "[Enter Audience]",
    channelEmptyText: "[Enter Channel]",
    langBtn: "🌐 中文"
  }}
}};

let currentLang = localStorage.getItem('handdraw_lang') || ((navigator.language && navigator.language.startsWith('zh')) ? 'zh' : 'en');

function updateModalAssetCount() {{
  if (!modalAssetSummary) return;
  const count = selectedAssets.length;
  modalAssetSummary.textContent = currentLang === 'zh'
    ? `已选择 ${{count}} 项资产`
    : `Selected ${{count}} asset${{count === 1 ? '' : 's'}}`;
}}

function renderAssetsTray() {{
  if (!assetsTrayCards || !assetsEmptyTrigger) return;
  const isZh = currentLang === 'zh';
  if (selectedAssets.length === 0) {{
    assetsEmptyTrigger.hidden = false;
    assetsTrayCards.hidden = true;
    if (btnClearAssets) btnClearAssets.hidden = true;
    assetsTrayCards.innerHTML = '';
    return;
  }}

  assetsEmptyTrigger.hidden = true;
  assetsTrayCards.hidden = false;
  if (btnClearAssets) {{
    btnClearAssets.hidden = false;
    btnClearAssets.textContent = isZh ? `清空已选资产 (${{selectedAssets.length}})` : `Clear Assets (${{selectedAssets.length}})`;
  }}

  const cardsHtml = selectedAssets.map(item => {{
    let badgeCls = 'is-char';
    let badgeLabel = isZh ? `${{item.id}} 角色` : `${{item.id}} Character`;
    if (item.id.startsWith('PR-') || item.cat === 'props') {{
      badgeCls = 'is-prop';
      badgeLabel = isZh ? `${{item.id}} 道具` : `${{item.id}} Prop`;
    }} else if (item.id.startsWith('SCN-') || item.cat === 'scenes') {{
      badgeCls = 'is-scene';
      badgeLabel = isZh ? `${{item.id}} 场景` : `${{item.id}} Scene`;
    }}
    const displayName = !isZh && item.name_en ? item.name_en : item.name;
    const removeTitle = isZh ? '移除此资产' : 'Remove';
    return `
      <div class="asset-tray-card" data-asset-id="${{item.id}}">
        <div class="asset-tray-thumb-wrap">
          <img class="asset-tray-img" src="${{item.img}}" alt="${{displayName}}">
        </div>
        <div class="asset-tray-info">
          <span class="asset-badge ${{badgeCls}}">${{badgeLabel}}</span>
          <span class="asset-tray-name" title="${{displayName}}">${{displayName}}</span>
        </div>
        <button type="button" class="asset-remove-btn" data-remove-asset="${{item.id}}" title="${{removeTitle}}" aria-label="${{removeTitle}}">×</button>
      </div>
    `;
  }}).join('');

  const moreBtnHtml = `
    <button type="button" class="asset-tray-more" data-picker="asset">
      <span>＋</span>
      <span>${{isZh ? '添加更多' : 'Add More'}}</span>
    </button>
  `;

  assetsTrayCards.innerHTML = cardsHtml + moreBtnHtml;
}}

function updatePrompt() {{
  const isZh = currentLang === 'zh';
  const t = I18N[currentLang];

  const parts = [];

  // Prefix based on mode / fusion
  if (isFusionActive) {{
    parts.push(isZh ? '【风格融合设计】' : '[Style Fusion Design]');
    if (currentMode === 'poster') {{
      parts.push(isZh ? '海报模式' : 'Poster mode');
    }} else if (currentMode === 'graphic-text') {{
      parts.push(isZh ? '图文模式' : 'Graphic-text mode');
    }} else if (currentMode === 'article-illust') {{
      parts.push(isZh ? '文章插图模式' : 'Article illustration mode');
    }} else if (currentMode === 'article-cover') {{
      parts.push(isZh ? '文章封面模式' : 'Article cover mode');
    }} else if (currentMode === 'photo') {{
      parts.push(isZh ? '摄影写真模式，请先出3个方案供我挑选' : 'Photo portrait mode, please first propose 3 candidate directions for me to choose from');
    }}
  }} else {{
    if (currentMode === 'poster') {{
      parts.push(isZh ? '请帮我出海报提示词' : 'Please generate a poster prompt for me');
    }} else if (currentMode === 'graphic-text') {{
      parts.push(isZh ? '图文模式' : 'Graphic-text mode');
    }} else if (currentMode === 'article-illust') {{
      parts.push(isZh ? '文章插图模式' : 'Article illustration mode');
    }} else if (currentMode === 'article-cover') {{
      parts.push(isZh ? '请设计文章封面' : 'Please design an article cover');
    }} else if (currentMode === 'photo') {{
      parts.push(isZh ? '摄影写真模式，请先出3个方案供我挑选' : 'Photo portrait mode, please first propose 3 candidate directions for me to choose from');
    }}
  }}

  // Assets (Characters / Props / Scenes)
  if (selectedAssets && selectedAssets.length > 0) {{
    const charIds = [];
    const propIds = [];
    const sceneIds = [];
    selectedAssets.forEach(a => {{
      if (a.id.startsWith('PR-') || a.cat === 'props') {{
        propIds.push(a.id);
      }} else if (a.id.startsWith('SCN-') || a.cat === 'scenes') {{
        sceneIds.push(a.id);
      }} else {{
        charIds.push(a.id);
      }}
    }});
    const joinSep = isZh ? '、' : ', ';
    if (charIds.length > 0) {{
      parts.push(isZh ? `角色：${{charIds.join(joinSep)}}` : `Character: ${{charIds.join(joinSep)}}`);
    }}
    if (propIds.length > 0) {{
      parts.push(isZh ? `道具：${{propIds.join(joinSep)}}` : `Prop: ${{propIds.join(joinSep)}}`);
    }}
    if (sceneIds.length > 0) {{
      parts.push(isZh ? `场景：${{sceneIds.join(joinSep)}}` : `Scene: ${{sceneIds.join(joinSep)}}`);
    }}
  }}

  // Layout
  if (selectedLayout && currentMode !== 'article-illust' && currentMode !== 'article-cover') {{
    parts.push(isZh ? `图型：${{selectedLayout.id}}` : `Layout: ${{selectedLayout.id}}`);
  }}

  // Style(s)
  if (isFusionActive) {{
    if (selectedCharStyle) {{
      parts.push(isZh ? `角色风格：${{selectedCharStyle.id}}` : `Character style: ${{selectedCharStyle.id}}`);
    }}
    if (selectedSceneStyle) {{
      parts.push(isZh ? `场景风格：${{selectedSceneStyle.id}}` : `Scene style: ${{selectedSceneStyle.id}}`);
    }}
  }} else {{
    if (selectedStyle) {{
      parts.push(isZh ? `风格：${{selectedStyle.id}}` : `Style: ${{selectedStyle.id}}`);
    }}
  }}

  // Theme color
  if (selectedColor) {{
    parts.push(isZh ? `主题色：${{selectedColor.id}}` : `Theme color: ${{selectedColor.id}}`);
  }}

  // Tone(s)
  if (isToneActive && selectedTones && selectedTones.length > 0) {{
    const toneParts = selectedTones.map(t => isZh ? `${{t.name}} (${{t.id}})` : `${{t.name_en || t.name}} (${{t.id}})`);
    const sep = isZh ? '、' : ', ';
    parts.push(isZh ? `影调：${{toneParts.join(sep)}}` : `Tone: ${{toneParts.join(sep)}}`);
  }}

  // Aspect ratio (optional, default empty)
  const ratioVal = inputRatio ? inputRatio.value.trim() : '';
  if (ratioVal) {{
    parts.push(isZh ? `画幅比例：${{ratioVal}}` : `Aspect ratio: ${{ratioVal}}`);
  }}

  // Mood (optional, default empty)
  const moodVal = inputMood ? inputMood.value.trim() : '';
  if (moodVal) {{
    parts.push(isZh ? `情绪：${{moodVal}}` : `Mood: ${{moodVal}}`);
  }}

  // Whitespace (negative space)
  if (currentWhitespace === 'moderate') {{
    parts.push(t.whitespaceModeratePrompt);
  }} else if (currentWhitespace === 'high') {{
    parts.push(t.whitespaceHighPrompt);
  }}

  // Fallback: if style OR color is missing, inject "其他你帮我选择"
  const missingStyleOrColor = isFusionActive
    ? (!selectedCharStyle || !selectedSceneStyle || !selectedColor)
    : (!selectedStyle || !selectedColor);
  if (missingStyleOrColor) {{
    parts.push(t.fallbackPrompt);
  }}

  // Theme or Article File Path
  const themeVal = inputTheme.value.trim();
  if (currentMode === 'article-illust') {{
    const articleDisplay = themeVal || t.articlePathEmptyText;
    parts.push(isZh ? `文件或文章地址：${{articleDisplay}}` : `File or article path: ${{articleDisplay}}`);
  }} else if (currentMode === 'article-cover') {{
    const articleDisplay = themeVal || (isZh ? '【输入文件/文件夹地址或文章内容】' : '[Enter file/folder path or article text]');
    parts.push(isZh ? `文章：${{articleDisplay}}` : `Article: ${{articleDisplay}}`);
    let scenario = isZh ? '公众号文章封面' : 'WeChat Official Account Cover';
    if (ratioVal === '5:2' || ratioVal === '16:9') scenario = isZh ? 'X文章封面' : 'X Article Cover';
    else if (ratioVal === '3:4') scenario = isZh ? '小红书封面' : 'Xiaohongshu Cover';
    else if (ratioVal === '2.35:1' || ratioVal === '21:9') scenario = isZh ? '公众号文章封面' : 'WeChat Official Account Cover';
    parts.push(isZh ? `业务场景：${{scenario}}` : `Scenario: ${{scenario}}`);
  }} else if (currentMode === 'photo') {{
    const shootTypeVal = inputShootType ? inputShootType.value.trim() : '';
    if (shootTypeVal) {{
      parts.push(isZh ? `拍摄类型：${{shootTypeVal}}` : `Shoot type: ${{shootTypeVal}}`);
    }}
    if (themeVal) {{
      parts.push(isZh ? `主题：${{themeVal}}` : `Theme: ${{themeVal}}`);
    }}
  }} else {{
    const themeDisplay = themeVal || t.themeEmptyText;
    parts.push(isZh ? `主题：${{themeDisplay}}` : `Theme: ${{themeDisplay}}`);
  }}

  // Extra fields for poster mode
  if (currentMode === 'poster') {{
    const audienceVal = inputAudience.value.trim();
    const audienceDisplay = audienceVal || t.audienceEmptyText;
    parts.push(isZh ? `受众：${{audienceDisplay}}` : `Audience: ${{audienceDisplay}}`);

    const channelVal = inputChannel.value.trim();
    const channelDisplay = channelVal || t.channelEmptyText;
    parts.push(isZh ? `海报投放渠道：${{channelDisplay}}` : `Channel: ${{channelDisplay}}`);
  }}



  const delimiter = isZh ? '，' : ', ';
  let promptText = parts.join(delimiter);
  if (isBatchActive) {{
    promptText += isZh ? ' | 批量出图' : ' | Batch Generation';
    if (isMixLayoutsActive) {{
      promptText += isZh ? ' | 混合多种图型' : ' | Mix Multiple Layouts';
    }}
  }}
  assembledText.textContent = promptText;
}}

function updateSlotUI(type) {{
  if (type === 'asset') return;
  const slotEl = document.querySelector(`#slot-${{type}}`);
  if (!slotEl) return;
  const trigger = slotEl.querySelector('.slot-trigger');
  const filled = slotEl.querySelector('.slot-filled');
  const img = filled.querySelector('img');
  const code = filled.querySelector('.slot-code');
  const name = filled.querySelector('.slot-name');

  if (type === 'tone') {{
    const badge = slotEl.querySelector('#slot-tone-badge');
    if (selectedTones && selectedTones.length > 0) {{
      slotEl.classList.add('has-value');
      trigger.hidden = true;
      filled.hidden = false;
      const first = selectedTones[0];
      img.src = first.img;
      img.alt = first.name;
      if (selectedTones.length > 1) {{
        if (badge) {{
          badge.textContent = `+${{selectedTones.length - 1}}`;
          badge.hidden = false;
        }}
        code.textContent = selectedTones.map(t => t.id).join(', ');
        name.textContent = selectedTones.map(t => currentLang === 'en' ? (t.name_en || t.name) : t.name).join('、');
      }} else {{
        if (badge) badge.hidden = true;
        code.textContent = first.id;
        name.textContent = currentLang === 'en' ? (first.name_en || first.name) : first.name;
      }}
    }} else {{
      slotEl.classList.remove('has-value');
      trigger.hidden = false;
      filled.hidden = true;
      img.src = '';
      if (badge) badge.hidden = true;
      code.textContent = '';
      name.textContent = '';
    }}
    return;
  }}

  let item = null;
  if (type === 'layout') item = selectedLayout;
  if (type === 'style') item = selectedStyle;
  if (type === 'char-style') item = selectedCharStyle;
  if (type === 'scene-style') item = selectedSceneStyle;
  if (type === 'color') item = selectedColor;

  if (item) {{
    slotEl.classList.add('has-value');
    trigger.hidden = true;
    filled.hidden = false;
    img.src = item.img;
    img.alt = item.name;
    code.textContent = item.id ? ((type === 'style' || type === 'char-style' || type === 'scene-style') ? `#${{item.id}}` : item.id) : '';
    name.textContent = (type === 'style' || type === 'char-style' || type === 'scene-style') ? (currentLang === 'en' && item.name_en ? item.name_en : (item.ref ? item.ref.split('/')[0].trim() : item.name)) || '' : '';
  }} else {{
    slotEl.classList.remove('has-value');
    trigger.hidden = false;
    filled.hidden = true;
    img.src = '';
    code.textContent = '';
    name.textContent = '';
  }}
}}

function setMode(mode) {{
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {{
    btn.classList.toggle('is-active', btn.dataset.mode === mode);
  }});
  if (mode === 'poster') {{
    posterExtraFields.hidden = false;
  }} else {{
    posterExtraFields.hidden = true;
  }}
  if (photoExtraFields) {{
    photoExtraFields.hidden = (mode !== 'photo');
  }}

  const slotLayout = document.querySelector('#slot-layout');
  const optTag = document.querySelector('#slot-layout-optional');
  const isIllust = mode === 'article-illust';
  const isCover = mode === 'article-cover';
  const isArticleTask = isIllust || isCover;
  if (slotLayout) {{
    slotLayout.classList.toggle('is-disabled', isArticleTask);
    const triggerBtn = slotLayout.querySelector('.slot-trigger');
    if (triggerBtn) triggerBtn.disabled = isArticleTask;
    const changeBtn = slotLayout.querySelector('.btn-change');
    if (changeBtn) changeBtn.disabled = isArticleTask;
    const clearBtn = slotLayout.querySelector('.btn-clear');
    if (clearBtn) clearBtn.disabled = isArticleTask;
  }}
  if (optTag) {{
    optTag.textContent = isArticleTask ? I18N[currentLang].layoutNotApplicable : I18N[currentLang].optionalLayout;
  }}
  if (isArticleTask && selectedLayout) {{
    selectedLayout = null;
    updateSlotUI('layout');
  }}

  const defaultRatios = {{
    'pure': '3:4',
    'graphic-text': '3:4',
    'poster': '9:16',
    'article-illust': '4:3',
    'article-cover': '2.35:1',
    'photo': '3:4',
  }};
  const targetRatio = defaultRatios[mode];
  if (targetRatio && inputRatio) {{
    inputRatio.value = targetRatio;
    if (btnClearRatio) btnClearRatio.hidden = false;
    document.querySelectorAll('.ratio-preset-btn').forEach(b => {{
      b.classList.toggle('is-active', b.dataset.ratio === targetRatio);
    }});
  }}

  if (mode === 'article-illust') {{
    if (themeLabelText) themeLabelText.textContent = I18N[currentLang].articlePathLabel;
    if (inputTheme) inputTheme.placeholder = I18N[currentLang].articlePathPlaceholder;
  }} else if (mode === 'article-cover') {{
    if (themeLabelText) themeLabelText.textContent = I18N[currentLang].articleCoverPathLabel;
    if (inputTheme) inputTheme.placeholder = I18N[currentLang].articleCoverPathPlaceholder;
  }} else if (mode === 'photo') {{
    if (themeLabelText) themeLabelText.textContent = I18N[currentLang].themeLabel;
    if (inputTheme) inputTheme.placeholder = I18N[currentLang].themePhotoPlaceholder;
  }} else {{
    if (themeLabelText) themeLabelText.textContent = I18N[currentLang].themeLabel;
    if (inputTheme) inputTheme.placeholder = I18N[currentLang].themePlaceholder;
  }}
  if (inputShootType) inputShootType.placeholder = I18N[currentLang].shootTypePlaceholder;
  autoResizeTheme();
  updatePrompt();
}}

function setWhitespace(val) {{
  currentWhitespace = val;
  document.querySelectorAll('.density-btn').forEach(btn => {{
    btn.classList.toggle('is-active', btn.dataset.whitespace === val);
  }});
  updatePrompt();
}}

// Visual Picker Logic
function openPicker(type) {{
  if (type === 'layout' && (currentMode === 'article-illust' || currentMode === 'article-cover')) return;
  currentPickerType = type;
  currentPickerFilter = 'all';
  pickerSearch.value = '';
  pickerSearch.placeholder = I18N[currentLang].searchPlaceholder;

  if (modalAssetFooter) {{
    modalAssetFooter.hidden = !['asset', 'tone'].includes(type);
  }}

   if (type === 'asset') {{
    pickerTitle.textContent = I18N[currentLang].pickerTitleAsset;
    renderAssetFilters();
    updateModalAssetCount();
  }} else if (type === 'tone') {{
    pickerTitle.textContent = I18N[currentLang].pickerTitleTone;
    renderToneFilters();
    updateModalToneCount();
  }} else if (type === 'layout') {{
    pickerTitle.textContent = I18N[currentLang].pickerTitleLayout;
    renderLayoutFilters();
  }} else if (type === 'style' || type === 'char-style' || type === 'scene-style') {{
    pickerTitle.textContent = type === 'char-style' ? (I18N[currentLang].pickerTitleCharStyle || '选择角色风格') : (type === 'scene-style' ? (I18N[currentLang].pickerTitleSceneStyle || '选择场景风格') : I18N[currentLang].pickerTitleStyle);
    renderStyleFilters();
  }} else if (type === 'color') {{
    pickerTitle.textContent = I18N[currentLang].pickerTitleColor;
    renderColorFilters();
  }}
  renderPickerItems();
  pickerDialog.showModal();
}}

function renderToneFilters() {{
  const t = I18N[currentLang];
  const isZh = currentLang === 'zh';
  const groups = [
    {{ id: 'all', zh: t.filterAll, en: t.filterAll }},
    {{ id: 'key', zh: t.filterToneKey, en: t.filterToneKey }},
    {{ id: 'contrast', zh: t.filterToneContrast, en: t.filterToneContrast }},
    {{ id: 'atmosphere', zh: t.filterToneAtmosphere, en: t.filterToneAtmosphere }}
  ];
  pickerFilters.innerHTML = groups.map(g => {{
    const count = g.id === 'all' ? TONES_DATA.length : TONES_DATA.filter(x => x.cat === g.id).length;
    const label = isZh ? g.zh : g.en;
    const isActive = currentPickerFilter === g.id ? ' is-active' : '';
    return `<button type="button" class="modal-filter-btn${{isActive}}" data-filter="${{g.id}}">${{label}} (${{count}})</button>`;
  }}).join('');
  attachFilterEvents();
}}

function updateModalToneCount() {{
  if (!modalAssetSummary) return;
  const t = I18N[currentLang];
  const count = selectedTones.length;
  modalAssetSummary.textContent = (t.modalToneCount || (currentLang === 'zh' ? '已选择 {{count}} 项影调' : '{{count}} Tone(s) Selected')).replace('{{count}}', count);
}}

function renderAssetFilters() {{
  const t = I18N[currentLang];
  const charCount = ASSETS_DATA.filter(x => x.cat === 'characters').length;
  const propCount = ASSETS_DATA.filter(x => x.cat === 'props').length;
  const sceneCount = ASSETS_DATA.filter(x => x.cat === 'scenes').length;
  pickerFilters.innerHTML = `
    <button type="button" class="modal-filter-btn is-active" data-filter="all">${{t.filterAll}} (${{ASSETS_DATA.length}})</button>
    <button type="button" class="modal-filter-btn" data-filter="characters">${{t.filterCharacters}} (${{charCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="props">${{t.filterProps}} (${{propCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="scenes">${{t.filterScenes}} (${{sceneCount}})</button>
  `;
  attachFilterEvents();
}}

function renderLayoutFilters() {{
  const t = I18N[currentLang];
  const scCount = LAYOUTS_DATA.filter(x => x.cat === 'social-card').length;
  const igCount = LAYOUTS_DATA.filter(x => x.cat === 'infographic').length;
  const sbCount = LAYOUTS_DATA.filter(x => x.cat === 'comic-storyboard').length;
  const ipCount = LAYOUTS_DATA.filter(x => x.cat === 'ip-character').length;
  const ecCount = LAYOUTS_DATA.filter(x => x.cat === 'ecommerce').length;
  pickerFilters.innerHTML = `
    <button type="button" class="modal-filter-btn is-active" data-filter="all">${{t.filterAll}} (${{LAYOUTS_DATA.length}})</button>
    <button type="button" class="modal-filter-btn" data-filter="social-card">${{t.filterSocialCard}} (${{scCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="infographic">${{t.filterInfographic}} (${{igCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="comic-storyboard">${{t.filterComicStoryboard}} (${{sbCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="ip-character">${{t.filterIpCharacter}} (${{ipCount}})</button>
    <button type="button" class="modal-filter-btn" data-filter="ecommerce">${{t.filterEcommerce}} (${{ecCount}})</button>
  `;
  attachFilterEvents();
}}

function renderStyleFilters() {{
  const isZh = currentLang === 'zh';
  const groups = [
    {{ id: 'all', zh: '全部', en: 'All' }},
    {{ id: 'FA', zh: 'FA 国际社论', en: 'FA Editorial' }},
    {{ id: 'FB', zh: 'FB 经典绘本', en: 'FB Picture Books' }},
    {{ id: 'FC', zh: 'FC 现代平面', en: 'FC Modern Graphic' }},
    {{ id: 'FD', zh: 'FD 日本当代', en: 'FD Japanese' }},
    {{ id: 'FE', zh: 'FE 新国风非遗', en: 'FE Traditional' }},
    {{ id: 'FF', zh: 'FF 3D黏土纸雕', en: 'FF 3D & Paper' }},
    {{ id: 'FG', zh: 'FG 动漫和赛璐璐', en: 'FG Anime & Cel' }},
    {{ id: 'FH', zh: 'FH 先锋综合', en: 'FH Mixed Media' }},
    {{ id: 'FI', zh: 'FI 写实摄影', en: 'FI Photography' }}
  ];
  pickerFilters.innerHTML = groups.map(g => {{
    let count;
    if (g.id === 'all') {{
      count = STYLES_DATA.length + 1;
    }} else if (g.id === 'FI') {{
      count = STYLES_DATA.filter(x => x.group === 'FI').length + 1;
    }} else {{
      count = STYLES_DATA.filter(x => x.group === g.id).length;
    }}
    const label = isZh ? g.zh : g.en;
    const isActive = currentPickerFilter === g.id ? ' is-active' : '';
    return `<button type="button" class="modal-filter-btn${{isActive}}" data-filter="${{g.id}}">${{label}} (${{count}})</button>`;
  }}).join('');
  attachFilterEvents();
}}

function renderColorFilters() {{
  const isZh = currentLang === 'zh';
  pickerFilters.innerHTML = COLOR_CATEGORIES.map(cat => {{
    const count = cat.id === 'all' ? COLORS_DATA.length : COLORS_DATA.filter(x => x.cat === cat.id).length;
    const label = isZh ? cat.zh : cat.en;
    const isActive = currentPickerFilter === cat.id ? ' is-active' : '';
    return `<button type="button" class="modal-filter-btn${{isActive}}" data-filter="${{cat.id}}">${{label}} (${{count}})</button>`;
  }}).join('');
  attachFilterEvents();
}}

function attachFilterEvents() {{
  pickerFilters.querySelectorAll('.modal-filter-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      pickerFilters.querySelectorAll('.modal-filter-btn').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      currentPickerFilter = btn.dataset.filter;
      renderPickerItems();
    }});
  }});
}}

function renderPickerItems() {{
  const query = pickerSearch.value.trim().toLowerCase();
  let list = [];
  let selectedId = null;

   if (currentPickerType === 'asset') {{
    list = ASSETS_DATA;
  }} else if (currentPickerType === 'tone') {{
    list = TONES_DATA;
  }} else if (currentPickerType === 'layout') {{
    list = LAYOUTS_DATA;
    selectedId = selectedLayout ? selectedLayout.id : null;
  }} else if (currentPickerType === 'style' || currentPickerType === 'char-style' || currentPickerType === 'scene-style') {{
    list = STYLES_DATA;
    if (currentPickerType === 'style') selectedId = selectedStyle ? selectedStyle.id : null;
    else if (currentPickerType === 'char-style') selectedId = selectedCharStyle ? selectedCharStyle.id : null;
    else if (currentPickerType === 'scene-style') selectedId = selectedSceneStyle ? selectedSceneStyle.id : null;
  }} else if (currentPickerType === 'color') {{
    list = COLORS_DATA;
    selectedId = selectedColor ? selectedColor.id : null;
  }}

  const filtered = list.filter(item => {{
    // Category match
    if (currentPickerType === 'asset') {{
      if (currentPickerFilter !== 'all' && item.cat !== currentPickerFilter) return false;
    }} else if (currentPickerType === 'tone') {{
      if (currentPickerFilter !== 'all' && item.cat !== currentPickerFilter) return false;
    }} else if (currentPickerType === 'layout') {{
      if (currentPickerFilter !== 'all' && item.cat !== currentPickerFilter) return false;
    }} else if (currentPickerType === 'style' || currentPickerType === 'char-style' || currentPickerType === 'scene-style') {{
      if (currentPickerFilter !== 'all' && item.group !== currentPickerFilter) return false;
    }} else if (currentPickerType === 'color') {{
      if (currentPickerFilter !== 'all' && item.cat !== currentPickerFilter) return false;
    }}
    // Search match
    if (query) {{
      const q = query.toLowerCase();
      const idMatch = item.id && item.id.toLowerCase().includes(q);
      const legacyMatch = item.legacy_id && String(item.legacy_id).includes(q);
      const nameMatch = item.name && item.name.toLowerCase().includes(q);
      const nameEnMatch = item.name_en && item.name_en.toLowerCase().includes(q);
      const refMatch = item.ref && item.ref.toLowerCase().includes(q);
      const tagsMatch = item.tags && item.tags.some(t => String(t).toLowerCase().includes(q));
      const descMatch = (item.desc_zh && item.desc_zh.toLowerCase().includes(q)) || (item.desc_en && item.desc_en.toLowerCase().includes(q));
      const groupMatch = (item.group && item.group.toLowerCase().includes(q)) || (item.group_name && item.group_name.toLowerCase().includes(q));
      const fiMatch = item.group === 'FI' && ('写实'.includes(q) || q.includes('写实') || '摄影'.includes(q) || q.includes('摄影') || '实景'.includes(q) || q.includes('实景') || '真实'.includes(q) || q.includes('真实') || 'photo'.includes(q) || 'realistic'.includes(q));
      return idMatch || legacyMatch || nameMatch || nameEnMatch || refMatch || tagsMatch || descMatch || groupMatch || fiMatch;
    }}
    return true;
  }});

  pickerGrid.innerHTML = filtered.map(item => {{
    const displayName = currentLang === 'en' && item.name_en ? item.name_en : item.name;

    if (currentPickerType === 'asset') {{
      const isSel = selectedAssets.some(x => x.id === item.id);
      return `
        <button type="button" class="picker-card${{isSel ? ' is-selected' : ''}}" data-id="${{item.id}}">
          <img class="picker-card-img" src="${{item.img}}" alt="${{displayName}}">
          <span class="picker-card-check">✓</span>
          <div class="picker-card-info">
            <span class="picker-card-id">${{item.id}}</span>
            <span class="picker-card-name" title="${{displayName}}">${{displayName}}</span>
          </div>
        </button>
      `;
    }}

    if (currentPickerType === 'tone') {{
      const isSel = selectedTones.some(x => x.id === item.id);
      const desc = currentLang === 'en' && item.desc_en ? item.desc_en : item.desc_zh;
      return `
        <button type="button" class="picker-card${{isSel ? ' is-selected' : ''}}" data-id="${{item.id}}" title="${{desc || displayName}}">
          <img class="picker-card-img" src="${{item.img}}" alt="${{displayName}}">
          <span class="picker-card-check">✓</span>
          <div class="picker-card-info">
            <span class="picker-card-id">${{item.id}}</span>
            <span class="picker-card-name" title="${{displayName}}">${{displayName}}</span>
          </div>
        </button>
      `;
    }}

    const isSel = selectedId === item.id;
    const badge = (currentPickerType === 'style' || currentPickerType === 'char-style' || currentPickerType === 'scene-style') ? `#${{item.id}}` : item.id;
    const badgeHtml = badge ? `<span class="picker-card-id">${{badge}}</span>` : '';
    return `
      <button type="button" class="picker-card${{isSel ? ' is-selected' : ''}}" data-id="${{item.id}}">
        <img class="picker-card-img" src="${{item.img}}" alt="${{displayName}}">
        <div class="picker-card-info">
          ${{badgeHtml}}
          <span class="picker-card-name" title="${{displayName}}">${{displayName}}</span>
        </div>
      </button>
    `;
  }}).join('');

  pickerGrid.querySelectorAll('.picker-card').forEach(card => {{
    card.addEventListener('click', () => {{
      const id = card.dataset.id;
      const found = list.find(x => x.id === id);
      if (!found) return;


      if (currentPickerType === 'asset') {{
        const existIdx = selectedAssets.findIndex(x => x.id === found.id);
        if (existIdx >= 0) {{
          selectedAssets.splice(existIdx, 1);
          card.classList.remove('is-selected');
        }} else {{
          selectedAssets.push(found);
          card.classList.add('is-selected');
        }}
        updateModalAssetCount();
        renderAssetsTray();
        updatePrompt();
        return;
      }}

      if (currentPickerType === 'tone') {{
        const existIdx = selectedTones.findIndex(x => x.id === found.id);
        if (existIdx >= 0) {{
          selectedTones.splice(existIdx, 1);
          card.classList.remove('is-selected');
        }} else {{
          selectedTones.push(found);
          card.classList.add('is-selected');
        }}
        updateModalToneCount();
        updateSlotUI('tone');
        updatePrompt();
        return;
      }}

      if (currentPickerType === 'layout') selectedLayout = found;
      if (currentPickerType === 'color') selectedColor = found;
      if (currentPickerType === 'style') selectedStyle = found;
      if (currentPickerType === 'char-style') {{
        if (selectedSceneStyle && selectedSceneStyle.id === found.id) {{
          alert(I18N[currentLang].styleConflictAlert || (currentLang === 'zh' ? '角色风格与场景风格必须不同，请选择不同的风格！' : 'Character style and scene style must be different!'));
          return;
        }}
        selectedCharStyle = found;
      }}
      if (currentPickerType === 'scene-style') {{
        if (selectedCharStyle && selectedCharStyle.id === found.id) {{
          alert(I18N[currentLang].styleConflictAlert || (currentLang === 'zh' ? '角色风格与场景风格必须不同，请选择不同的风格！' : 'Character style and scene style must be different!'));
          return;
        }}
        selectedSceneStyle = found;
      }}
      updateSlotUI(currentPickerType);
      updatePrompt();
      pickerDialog.close();
    }});
  }});
}}

pickerSearch.addEventListener('input', renderPickerItems);
pickerDialog.querySelector('.close').addEventListener('click', () => pickerDialog.close());
pickerDialog.addEventListener('click', e => {{ if (e.target === pickerDialog) pickerDialog.close(); }});

if (btnModalClearAssets) {{
  btnModalClearAssets.addEventListener('click', () => {{
     if (currentPickerType === 'asset') {{
      selectedAssets = [];
      updateModalAssetCount();
      renderPickerItems();
      renderAssetsTray();
      updatePrompt();
    }} else if (currentPickerType === 'tone') {{
      selectedTones = [];
      updateModalToneCount();
      renderPickerItems();
      updateSlotUI('tone');
      updatePrompt();
    }}
  }});
}}

if (btnModalConfirmAssets) {{
  btnModalConfirmAssets.addEventListener('click', () => {{
    if (currentPickerType === 'tone') {{
      updateSlotUI('tone');
      updatePrompt();
    }}
    pickerDialog.close();
  }});
}}

// Triggers & Clears
document.addEventListener('click', e => {{
  const removeAssetBtn = e.target.closest('[data-remove-asset]');
  if (removeAssetBtn) {{
    const id = removeAssetBtn.dataset.removeAsset;
    selectedAssets = selectedAssets.filter(x => x.id !== id);
    renderAssetsTray();
    updatePrompt();
    if (pickerDialog.open && currentPickerType === 'asset') {{
      updateModalAssetCount();
      renderPickerItems();
    }}
    return;
  }}

  const clearAssetsBtn = e.target.closest('#btn-clear-assets');
  if (clearAssetsBtn) {{
    selectedAssets = [];
    renderAssetsTray();
    updatePrompt();
    if (pickerDialog.open && currentPickerType === 'asset') {{
      updateModalAssetCount();
      renderPickerItems();
    }}
    return;
  }}

  const trigger = e.target.closest('[data-picker]');
  if (trigger) {{
    if (trigger.dataset.picker === 'layout' && (currentMode === 'article-illust' || currentMode === 'article-cover')) return;
    openPicker(trigger.dataset.picker);
    return;
  }}
  const clearBtn = e.target.closest('[data-clear]');
  if (clearBtn) {{
    const type = clearBtn.dataset.clear;
    if (type === 'layout' && (currentMode === 'article-illust' || currentMode === 'article-cover')) return;
    if (type === 'layout') selectedLayout = null;
    if (type === 'style') selectedStyle = null;
    if (type === 'char-style') selectedCharStyle = null;
    if (type === 'scene-style') selectedSceneStyle = null;
    if (type === 'color') selectedColor = null;
    if (type === 'tone') selectedTones = [];
    updateSlotUI(type);
    updatePrompt();
    return;
  }}
}});

// Mode radio buttons
document.querySelectorAll('.mode-btn').forEach(btn => {{
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
}});

// Whitespace radio buttons
document.querySelectorAll('.density-btn').forEach(btn => {{
  btn.addEventListener('click', () => setWhitespace(btn.dataset.whitespace));
}});

// Inputs change
function autoResizeTheme() {{
  if (!inputTheme) return;
  inputTheme.style.height = 'auto';
  inputTheme.style.height = Math.max(inputTheme.scrollHeight, 58) + 'px';
}}

[inputAudience, inputChannel].forEach(el => {{
  if (el) el.addEventListener('input', updatePrompt);
}});
if (inputTheme) {{
  inputTheme.addEventListener('input', () => {{
    autoResizeTheme();
    updatePrompt();
  }});
}}

// Ratio Presets and Input handlers
document.querySelectorAll('.ratio-preset-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const ratio = btn.dataset.ratio;
    if (btn.classList.contains('is-active')) {{
      btn.classList.remove('is-active');
      if (inputRatio) inputRatio.value = '';
      if (btnClearRatio) btnClearRatio.hidden = true;
    }} else {{
      document.querySelectorAll('.ratio-preset-btn').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      if (inputRatio) inputRatio.value = ratio;
      if (btnClearRatio) btnClearRatio.hidden = false;
    }}
    updatePrompt();
  }});
}});

if (inputRatio) {{
  inputRatio.addEventListener('input', () => {{
    const val = inputRatio.value.trim();
    if (btnClearRatio) btnClearRatio.hidden = !val;
    document.querySelectorAll('.ratio-preset-btn').forEach(b => {{
      b.classList.toggle('is-active', b.dataset.ratio === val);
    }});
    updatePrompt();
  }});
}}

if (btnClearRatio) {{
  btnClearRatio.addEventListener('click', () => {{
    if (inputRatio) {{
      inputRatio.value = '';
      inputRatio.focus();
    }}
    btnClearRatio.hidden = true;
    document.querySelectorAll('.ratio-preset-btn').forEach(b => b.classList.remove('is-active'));
    updatePrompt();
  }});
}}

// Mood Presets and Input handlers (multi-select)
document.querySelectorAll('.mood-preset-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const tag = currentLang === 'zh' ? btn.dataset.moodZh : btn.dataset.moodEn;
    const isZh = currentLang === 'zh';
    const sep = isZh ? '、' : ', ';
    const rawVal = inputMood ? inputMood.value.trim() : '';
    let currentTags = rawVal ? rawVal.split(/[、,，/]+|\\s+/).map(s => s.trim()).filter(Boolean) : [];

    const idx = currentTags.findIndex(t =>
      t.toLowerCase() === tag.toLowerCase() ||
      (btn.dataset.moodZh && t === btn.dataset.moodZh) ||
      (btn.dataset.moodEn && t.toLowerCase() === btn.dataset.moodEn.toLowerCase())
    );

    if (idx >= 0) {{
      currentTags.splice(idx, 1);
      btn.classList.remove('is-active');
    }} else {{
      currentTags.push(tag);
      btn.classList.add('is-active');
    }}

    if (inputMood) {{
      inputMood.value = currentTags.join(sep);
      if (btnClearMood) btnClearMood.hidden = currentTags.length === 0;
    }}
    updatePrompt();
  }});
}});

if (inputMood) {{
  inputMood.addEventListener('input', () => {{
    const rawVal = inputMood.value.trim();
    if (btnClearMood) btnClearMood.hidden = !rawVal;
    const tokens = rawVal ? rawVal.split(/[、,，/]+|\\s+/).map(s => s.trim().toLowerCase()).filter(Boolean) : [];
    const tokenSet = new Set(tokens);
    document.querySelectorAll('.mood-preset-btn').forEach(b => {{
      const isMatch = tokenSet.has(b.dataset.moodZh.toLowerCase()) || tokenSet.has(b.dataset.moodEn.toLowerCase());
      b.classList.toggle('is-active', isMatch);
    }});
    updatePrompt();
  }});
}}

if (btnClearMood) {{
  btnClearMood.addEventListener('click', () => {{
    if (inputMood) {{
      inputMood.value = '';
      inputMood.focus();
    }}
    btnClearMood.hidden = true;
    document.querySelectorAll('.mood-preset-btn').forEach(b => b.classList.remove('is-active'));
    updatePrompt();
  }});
}}

// Shoot Type Presets and Input handlers (tag selection + manual input)
document.querySelectorAll('.shoot-type-preset-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const tag = currentLang === 'zh' ? btn.dataset.typeZh : btn.dataset.typeEn;
    const isZh = currentLang === 'zh';
    const sep = isZh ? '、' : ', ';
    const rawVal = inputShootType ? inputShootType.value.trim() : '';
    let currentTags = rawVal ? rawVal.split(/[、,，/]+|\\s+/).map(s => s.trim()).filter(Boolean) : [];

    const idx = currentTags.findIndex(t =>
      t.toLowerCase() === tag.toLowerCase() ||
      (btn.dataset.typeZh && t === btn.dataset.typeZh) ||
      (btn.dataset.typeEn && t.toLowerCase() === btn.dataset.typeEn.toLowerCase())
    );

    if (idx >= 0) {{
      currentTags.splice(idx, 1);
      btn.classList.remove('is-active');
    }} else {{
      currentTags.push(tag);
      btn.classList.add('is-active');
    }}

    if (inputShootType) {{
      inputShootType.value = currentTags.join(sep);
      if (btnClearShootType) btnClearShootType.hidden = currentTags.length === 0;
    }}
    updatePrompt();
  }});
}});

if (inputShootType) {{
  inputShootType.addEventListener('input', () => {{
    const rawVal = inputShootType.value.trim();
    if (btnClearShootType) btnClearShootType.hidden = !rawVal;
    const tokens = rawVal ? rawVal.split(/[、,，/]+|\\s+/).map(s => s.trim().toLowerCase()).filter(Boolean) : [];
    const tokenSet = new Set(tokens);
    document.querySelectorAll('.shoot-type-preset-btn').forEach(b => {{
      const isMatch = tokenSet.has(b.dataset.typeZh.toLowerCase()) || tokenSet.has(b.dataset.typeEn.toLowerCase());
      b.classList.toggle('is-active', isMatch);
    }});
    updatePrompt();
  }});
}}

if (btnClearShootType) {{
  btnClearShootType.addEventListener('click', () => {{
    if (inputShootType) {{
      inputShootType.value = '';
      inputShootType.focus();
    }}
    btnClearShootType.hidden = true;
    document.querySelectorAll('.shoot-type-preset-btn').forEach(b => b.classList.remove('is-active'));
    updatePrompt();
  }});
}}

// Fusion Checkbox Listener
if (checkboxFusion) {{
  checkboxFusion.addEventListener('change', () => {{
    isFusionActive = checkboxFusion.checked;
    if (fusionWrap) fusionWrap.classList.toggle('is-active', isFusionActive);
    if (slotsGrid) slotsGrid.classList.toggle('is-fusion', isFusionActive);
    if (slotStyle) slotStyle.hidden = isFusionActive;
    if (slotCharStyle) slotCharStyle.hidden = !isFusionActive;
    if (slotSceneStyle) slotSceneStyle.hidden = !isFusionActive;

    if (isFusionActive) {{
      if (selectedStyle && !selectedCharStyle) {{
        selectedCharStyle = selectedStyle;
        updateSlotUI('char-style');
      }}
    }}
    updatePrompt();
  }});
}}

// Tone Checkbox Listener
if (checkboxTone) {{
  checkboxTone.addEventListener('change', () => {{
    isToneActive = checkboxTone.checked;
    if (toneWrap) toneWrap.classList.toggle('is-active', isToneActive);
    if (slotsGrid) slotsGrid.classList.toggle('is-tone', isToneActive);
    if (slotTone) slotTone.hidden = !isToneActive;
    updateSlotUI('tone');
    updatePrompt();
  }});
}}

// Batch Generation Checkbox Listener
if (checkboxBatch) {{
  checkboxBatch.addEventListener('change', () => {{
    isBatchActive = checkboxBatch.checked;
    if (batchWrap) batchWrap.classList.toggle('is-active', isBatchActive);
    if (!isBatchActive) {{
      isMixLayoutsActive = false;
      if (checkboxMixLayouts) checkboxMixLayouts.checked = false;
      if (mixLayoutsWrap) {{
        mixLayoutsWrap.classList.remove('is-active');
        mixLayoutsWrap.hidden = true;
      }}
    }} else {{
      if (mixLayoutsWrap) mixLayoutsWrap.hidden = false;
    }}
    updatePrompt();
  }});
}}

// Mix Multiple Layouts Checkbox Listener
if (checkboxMixLayouts) {{
  checkboxMixLayouts.addEventListener('change', () => {{
    isMixLayoutsActive = checkboxMixLayouts.checked;
    if (mixLayoutsWrap) mixLayoutsWrap.classList.toggle('is-active', isMixLayoutsActive);
    updatePrompt();
  }});
}}

// Toolbar Actions: Gacha & Reset
document.querySelector('#btn-gacha').addEventListener('click', () => {{
  // Random layout (skip in article-illust and article-cover mode)
  if (currentMode !== 'article-illust' && currentMode !== 'article-cover') {{
    selectedLayout = LAYOUTS_DATA[Math.floor(Math.random() * LAYOUTS_DATA.length)];
  }} else {{
    selectedLayout = null;
  }}
  // Random color
  selectedColor = COLORS_DATA[Math.floor(Math.random() * COLORS_DATA.length)];

  if (isToneActive && TONES_DATA.length > 0) {{
    selectedTones = [TONES_DATA[Math.floor(Math.random() * TONES_DATA.length)]];
  }}

  if (isFusionActive) {{
    const pool = STYLES_DATA;
    selectedCharStyle = pool[Math.floor(Math.random() * pool.length)];
    const remain = pool.filter(x => x.id !== selectedCharStyle.id);
    selectedSceneStyle = remain[Math.floor(Math.random() * remain.length)];
    updateSlotUI('layout');
    updateSlotUI('char-style');
    updateSlotUI('scene-style');
    updateSlotUI('color');
    if (isToneActive) updateSlotUI('tone');
    updatePrompt();
    return;
  }}

  // Random style
  const stylePool = STYLES_DATA;
  selectedStyle = stylePool[Math.floor(Math.random() * stylePool.length)];

  updateSlotUI('layout');
  updateSlotUI('style');
  updateSlotUI('color');
  if (isToneActive) updateSlotUI('tone');
  updatePrompt();
}});

document.querySelector('#btn-reset').addEventListener('click', () => {{
  selectedAssets = [];
  selectedLayout = null;
  selectedStyle = null;
  selectedCharStyle = null;
  selectedSceneStyle = null;
  selectedColor = null;
  selectedTones = [];
  inputTheme.value = '';
  inputTheme.style.height = '';
  inputAudience.value = '';
  inputChannel.value = '';

  if (inputShootType) inputShootType.value = '';
  if (btnClearShootType) btnClearShootType.hidden = true;
  document.querySelectorAll('.shoot-type-preset-btn').forEach(b => b.classList.remove('is-active'));
  if (inputRatio) {{
    inputRatio.value = '';
    if (btnClearRatio) btnClearRatio.hidden = true;
    document.querySelectorAll('.ratio-preset-btn').forEach(b => b.classList.remove('is-active'));
  }}
  if (inputMood) {{
    inputMood.value = '';
    if (btnClearMood) btnClearMood.hidden = true;
    document.querySelectorAll('.mood-preset-btn').forEach(b => b.classList.remove('is-active'));
  }}
  isBatchActive = false;
  isMixLayoutsActive = false;
  if (checkboxBatch) checkboxBatch.checked = false;
  if (batchWrap) batchWrap.classList.remove('is-active');
  if (checkboxMixLayouts) checkboxMixLayouts.checked = false;
  if (mixLayoutsWrap) {{
    mixLayoutsWrap.classList.remove('is-active');
    mixLayoutsWrap.hidden = true;
  }}
  renderAssetsTray();
  updateSlotUI('layout');
  updateSlotUI('style');
  updateSlotUI('char-style');
  updateSlotUI('scene-style');
  updateSlotUI('color');
  updateSlotUI('tone');
  setWhitespace('normal');
  setMode('pure');
  try {{
    if (window.history && window.history.replaceState && window.location.search) {{
      window.history.replaceState({{}}, document.title, window.location.pathname);
    }}
  }} catch (e) {{}}
}});

// Copy Assembled Prompt
btnCopyAssembled.addEventListener('click', async () => {{
  const text = assembledText.textContent;
  if (!text) return;
  try {{
    await navigator.clipboard.writeText(text);
    copyBtnText.textContent = I18N[currentLang].copied;
    btnCopyAssembled.classList.add('copied');
    setTimeout(() => {{
      copyBtnText.textContent = I18N[currentLang].copyPromptBtn;
      btnCopyAssembled.classList.remove('copied');
    }}, 1500);
  }} catch (e) {{
    const area = document.createElement('textarea');
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand('copy');
    area.remove();
    copyBtnText.textContent = I18N[currentLang].copied;
    btnCopyAssembled.classList.add('copied');
    setTimeout(() => {{
      copyBtnText.textContent = I18N[currentLang].copyPromptBtn;
      btnCopyAssembled.classList.remove('copied');
    }}, 1500);
  }}
}});

// I18N handling
function applyLang(lang) {{
  currentLang = lang;
  localStorage.setItem('handdraw_lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  const t = I18N[lang];
  document.title = t.pageTitle;

  document.querySelectorAll('[data-i18n]').forEach(el => {{
    const key = el.dataset.i18n;
    if (t[key]) el.textContent = t[key];
  }});

  document.querySelectorAll('[data-zh][data-en]').forEach(el => {{
    el.textContent = lang === 'zh' ? el.dataset.zh : el.dataset.en;
  }});

  const optTag = document.querySelector('#slot-layout-optional');
  if (optTag && (currentMode === 'article-illust' || currentMode === 'article-cover')) {{
    optTag.textContent = t.layoutNotApplicable;
  }}

  const btnModerate = document.querySelector('.density-btn[data-whitespace="moderate"]');
  if (btnModerate) btnModerate.title = t.whitespaceModeratePrompt;
  const btnHigh = document.querySelector('.density-btn[data-whitespace="high"]');
  if (btnHigh) btnHigh.title = t.whitespaceHighPrompt;

  if (currentMode === 'article-illust') {{
    if (themeLabelText) themeLabelText.textContent = t.articlePathLabel;
    if (inputTheme) inputTheme.placeholder = t.articlePathPlaceholder;
  }} else if (currentMode === 'article-cover') {{
    if (themeLabelText) themeLabelText.textContent = t.articleCoverPathLabel;
    if (inputTheme) inputTheme.placeholder = t.articleCoverPathPlaceholder;
  }} else if (currentMode === 'photo') {{
    if (themeLabelText) themeLabelText.textContent = t.themeLabel;
    if (inputTheme) inputTheme.placeholder = t.themePhotoPlaceholder;
  }} else {{
    if (themeLabelText) themeLabelText.textContent = t.themeLabel;
    if (inputTheme) inputTheme.placeholder = t.themePlaceholder;
  }}
  if (inputShootType) inputShootType.placeholder = t.shootTypePlaceholder;
  inputAudience.placeholder = t.audiencePlaceholder;
  inputChannel.placeholder = t.channelPlaceholder;
  autoResizeTheme();
  if (inputRatio) inputRatio.placeholder = t.ratioPlaceholder;
  if (inputMood) inputMood.placeholder = t.moodPlaceholder;

  document.querySelectorAll('.copy-btn').forEach(btn => {{
    const box = btn.closest('.formula-box');
    if (box) {{
      const formula = box.querySelector('.formula-text');
      if (formula) btn.dataset.prompt = formula.dataset[lang];
    }}
  }});

  if (langBtn) langBtn.textContent = t.langBtn;
  renderAssetsTray();
  updateModalAssetCount();
  updateSlotUI('layout');
  updateSlotUI('style');
  updateSlotUI('char-style');
  updateSlotUI('scene-style');
  updateSlotUI('color');
  updateSlotUI('tone');
  updatePrompt();
  if (pickerDialog.open) {{
     if (currentPickerType === 'asset') {{
      pickerTitle.textContent = t.pickerTitleAsset;
      renderAssetFilters();
      updateModalAssetCount();
    }} else if (currentPickerType === 'tone') {{
      pickerTitle.textContent = t.pickerTitleTone;
      renderToneFilters();
      updateModalToneCount();
    }} else if (currentPickerType === 'layout') {{
      pickerTitle.textContent = t.pickerTitleLayout;
      renderLayoutFilters();
    }} else if (currentPickerType === 'style' || currentPickerType === 'char-style' || currentPickerType === 'scene-style') {{
      pickerTitle.textContent = currentPickerType === 'char-style' ? t.pickerTitleCharStyle : (currentPickerType === 'scene-style' ? t.pickerTitleSceneStyle : t.pickerTitleStyle);
      renderStyleFilters();
    }} else if (currentPickerType === 'color') {{
      pickerTitle.textContent = t.pickerTitleColor;
      renderColorFilters();
    }}
    renderPickerItems();
  }}
}}

if (langBtn) {{
  langBtn.addEventListener('click', () => applyLang(currentLang === 'zh' ? 'en' : 'zh'));
}}
setMode(currentMode);
applyLang(currentLang);

// URL Query Parameter Integration
const urlParams = new URLSearchParams(window.location.search);
const modeParam = urlParams.get('mode');
const assetParam = urlParams.get('asset');
const styleParam = urlParams.get('style');
const layoutParam = urlParams.get('layout');
const colorParam = urlParams.get('color');
const toneParam = urlParams.get('tone');

if (modeParam && ['pure', 'graphic-text', 'poster', 'article-illust', 'article-cover', 'photo'].includes(modeParam)) {{
  setMode(modeParam);
}}



if (assetParam) {{
  const tokens = assetParam.split(/[,，\\s]+/).map(s => s.trim().toUpperCase()).filter(Boolean);
  tokens.forEach(tok => {{
    const found = ASSETS_DATA.find(x => x.id.toUpperCase() === tok);
    if (found && !selectedAssets.some(x => x.id === found.id)) {{
      selectedAssets.push(found);
    }}
  }});
  renderAssetsTray();
}}
if (styleParam) {{
  const clean = styleParam.trim().replace(/^#/, '');
  const norm = clean.padStart(3, '0');
  const found = STYLES_DATA.find(x => x.id === norm || x.id.toUpperCase() === clean.toUpperCase() || String(x.legacy_id) === clean);
  if (found) {{
    selectedStyle = found;
  }}
}}
if (layoutParam) {{
  const norm = layoutParam.trim().toUpperCase();
  const found = LAYOUTS_DATA.find(x => x.id.toUpperCase() === norm);
  if (found) {{
    selectedLayout = found;
  }}
}}
if (colorParam) {{
  const norm = colorParam.trim().toUpperCase();
  const found = COLORS_DATA.find(x => x.id.toUpperCase() === norm);
  if (found) {{
    selectedColor = found;
  }}
}}
if (toneParam) {{
  const tokens = toneParam.split(/[,，\\s]+/).map(s => s.trim().toUpperCase()).filter(Boolean);
  tokens.forEach(tok => {{
    const found = TONES_DATA.find(x => x.id.toUpperCase() === tok);
    if (found && !selectedTones.some(x => x.id === found.id)) {{
      selectedTones.push(found);
    }}
  }});
  if (selectedTones.length > 0) {{
    isToneActive = true;
    if (checkboxTone) checkboxTone.checked = true;
    if (toneWrap) toneWrap.classList.add('is-active');
    if (slotsGrid) slotsGrid.classList.add('is-tone');
    if (slotTone) slotTone.hidden = false;
  }}
}}

const batchParam = urlParams.get('batch');
if (batchParam === '1' || batchParam === 'true') {{
  isBatchActive = true;
  if (checkboxBatch) checkboxBatch.checked = true;
  if (batchWrap) batchWrap.classList.add('is-active');
  if (mixLayoutsWrap) mixLayoutsWrap.hidden = false;
  const mixParam = urlParams.get('mix') || urlParams.get('mix_layouts');
  if (mixParam === '1' || mixParam === 'true') {{
    isMixLayoutsActive = true;
    if (checkboxMixLayouts) checkboxMixLayouts.checked = true;
    if (mixLayoutsWrap) mixLayoutsWrap.classList.add('is-active');
  }}
}}

if (assetParam || styleParam || layoutParam || colorParam || toneParam || modeParam || batchParam) {{
  renderAssetsTray();
  updateSlotUI('layout');
  updateSlotUI('style');
  updateSlotUI('char-style');
  updateSlotUI('scene-style');
  updateSlotUI('color');
  updateSlotUI('tone');
  updatePrompt();
  try {{
    if (window.history && window.history.replaceState && window.location.search) {{
      window.history.replaceState({{}}, document.title, window.location.pathname);
    }}
  }} catch (e) {{}}
}}

// Copy for retained tutorial cards
const COPY_ICON = '{COPY_ICON_SVG}';
const CHECK_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>';

document.querySelectorAll('.formula-box').forEach(box => {{
  const btn = box.querySelector('.copy-btn');
  const label = box.querySelector('.formula-label');
  const doCopy = async () => {{
    if (!btn) return;
    const prompt = btn.dataset.prompt;
    if (!prompt) return;
    try {{
      await navigator.clipboard.writeText(prompt);
      btn.innerHTML = CHECK_ICON;
      btn.classList.add('copied');
      setTimeout(() => {{
        btn.innerHTML = COPY_ICON;
        btn.classList.remove('copied');
      }}, 1500);
    }} catch (e) {{}}
  }};
  if (btn) btn.addEventListener('click', doCopy);
  if (label) {{
    label.style.cursor = 'pointer';
    label.addEventListener('click', doCopy);
  }}
}});

if (wechatBtn && wechatModal) {{
  wechatBtn.addEventListener('click', () => wechatModal.showModal());
  wechatModal.querySelectorAll('.close').forEach(btn => btn.addEventListener('click', () => wechatModal.close()));
  wechatModal.addEventListener('click', e => {{ if (e.target === wechatModal) wechatModal.close(); }});
}}
</script><script src="local-navigation.js" defer></script></body></html>'''


def main() -> None:
    GALLERY.write_text(build_html(), encoding="utf-8")
    print(f"Built interactive tutorials & prompt assembler gallery: {GALLERY}")


if __name__ == "__main__":
    main()
