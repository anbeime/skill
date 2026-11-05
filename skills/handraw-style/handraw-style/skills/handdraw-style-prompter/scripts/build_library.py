#!/usr/bin/env python3
"""Build derived style JSON and an offline number-searchable adaptive waterfall gallery."""
from __future__ import annotations

from gallery_thumbnails import write_thumbnail_fallback

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "styles_200_reorganized.md"
STYLE_JSON = SKILL / "references" / "styles.json"
GALLERY = SKILL / "gallery" / "index.html"
ROW = re.compile(r"^\|\s*([A-Za-z]{2}-\d{3})\s*·\s*([^|]+)\|\s*([^|]+)\|\s*(.*)\|\s*$")
HEADING = re.compile(r"^##\s+([A-Za-z]{2})\s+(.+)$")
IMAGE = re.compile(r"^([A-Za-z]{2})_(\d{3})(?:-(\d{3}))?\.webp$")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/yang0/handraw-style/master/skills/handdraw-style-prompter/references/version.json"
VERSION_FILE = SKILL / "references" / "version.json"
ALIAS_MAP_FILE = SKILL / "references" / "style_alias_map.json"
UPDATE_COMMAND = "请更新skill https://github.com/yang0/handraw-style"

IMAGE_FALLBACK_SCRIPT = """<script>
(function() {
  function fixImg(img) {
    if (!img || img.__fixed) return;
    var src = img.getAttribute('src') || '';
    var idx = src.indexOf('images/');
    if (idx === -1) return;
    if (location.protocol === 'file:') {
      var key = src.substring(idx + 'images/'.length);
      var thumbnail = window.handrawThumbnails?.[key];
      if (thumbnail) {
        img.src = thumbnail;
        return;
      }
    }
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
      var card = e.target.closest('.style-card, .layout-card, .color-card, .asset-card');
      if (card && e.target.src) {
        card.dataset.image = e.target.src;
      }
    }
  }, true);
})();
</script>"""

GROUPS = (
    ("all", "全部", "All"),
    ("FA", "国际社论", "Editorial Humor"),
    ("FB", "经典绘本", "Picture Books"),
    ("FC", "现代平面", "Modern Graphic"),
    ("FD", "日本当代", "Japanese Contemporary"),
    ("FE", "新国风非遗", "Chinese Traditional"),
    ("FF", "3D黏土纸雕", "3D Clay & Paper"),
    ("FG", "动漫和赛璐璐", "Anime & Cel"),
    ("FH", "先锋综合", "Mixed Media"),
    ("FI", "写实摄影", "Realistic Photography"),
)

GROUP_LABELS = {
    "FA": ("国际社论幽默", "Editorial & Humor Doodle"),
    "FB": ("经典绘本叙事", "Picture Book & Watercolor"),
    "FC": ("现代平面艺术", "Modern Graphic & Pop"),
    "FD": ("日本当代插画", "Japanese Contemporary & Manga"),
    "FE": ("新国风与传统工艺", "Chinese Traditional & Folk Craft"),
    "FF": ("3D黏土毛毡与纸雕", "3D Clay, Felt & Papercraft"),
    "FG": ("动漫和赛璐璐", "Anime, Cel Animation & Retro Game"),
    "FH": ("先锋实验与综合媒介", "Mixed Media & Impasto Arts"),
    "FI": ("写实摄影与视觉大片", "Realistic, Photography & Cinematic Styles"),
}


def load_version() -> str:
    if VERSION_FILE.exists():
        try:
            data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            return str(data.get("version", "1.0.0"))
        except Exception:
            pass
    return "1.0.0"


def parse_styles() -> list[dict[str, str]]:
    group = ""
    items: list[dict[str, str]] = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        heading = HEADING.match(line)
        if heading:
            group = f"{heading.group(1)} {heading.group(2)}"
            continue
        match = ROW.match(line)
        if match:
            number, reference, generation_name, traits = (part.strip() for part in match.groups())
            items.append({"number": number, "group": group, "reference": reference,
                          "generation_name": generation_name, "traits": traits})
    return items


def individual_image_path(number: str) -> str:
    cat = number.split("-")[0]
    return f"../../../images/individual/{cat}/{number}.webp"


def gallery_html(styles: list[dict[str, str]], sheets: list[dict[str, str]] | None = None) -> str:
    total_count = len(styles)
    version = load_version()

    alias_map = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8")) if ALIAS_MAP_FILE.exists() else {}
    new_to_legacy = alias_map.get("new_to_legacy", {})

    counts = {"all": total_count}
    for g, _, _ in GROUPS[1:]:
        counts[g] = sum(s["group"].startswith(g) for s in styles)

    controls = "".join(
        f'<button class="filter{" is-active" if group == "all" else ""}" type="button" '
        f'data-group="{group}" data-label-zh="{label_zh}" data-label-en="{label_en}">'
        f'{label_zh} <span>{counts[group]}</span></button>'
        for group, label_zh, label_en in GROUPS
    )

    group_sections = []
    for idx, (g, _, _) in enumerate(GROUPS[1:]):
        g_styles = [s for s in styles if s["group"].startswith(g)]
        if not g_styles:
            continue
        g_cards = []
        for s in g_styles:
            num = s["number"]
            gen_name = s["generation_name"]
            ref = s["reference"]
            traits = s["traits"]
            img_src = individual_image_path(num)
            legacy_num = new_to_legacy.get(num, "")
            legacy_attr = f' data-legacy="{legacy_num}"' if legacy_num else ''

            g_cards.append(
                f'<button class="style-card" type="button" data-number="{num}" data-group="{g}"{legacy_attr} '
                f'data-image="{img_src}" '
                f'data-name="{html.escape(gen_name, quote=True)}" '
                f'data-reference="{html.escape(ref, quote=True)}" '
                f'data-traits="{html.escape(traits, quote=True)}" '
                f'title="#{num} · {html.escape(gen_name, quote=True)} ({html.escape(ref, quote=True)})" '
                f'aria-label="查看 #{num} {html.escape(gen_name, quote=True)}">'
                f'<img src="{img_src}" alt="#{num} {html.escape(gen_name, quote=True)}" loading="lazy">'
                f'<span class="style-info">'
                f'<span class="style-header"><span class="style-num">#{num}</span><span class="style-group-pill">{g}</span></span>'
                f'<span class="style-name">{html.escape(gen_name)}</span>'
                f'<span class="style-ref">{html.escape(ref)}</span>'
                f'</span></button>'
            )
        zh_title, en_title = GROUP_LABELS.get(g, (g, g))
        cards_html = "\n".join(g_cards)
        first_cls = " is-first" if idx == 0 else ""
        group_sections.append(
            f'<section class="style-group{first_cls}" data-group="{g}">'
            f'<div class="group-header">'
            f'<span class="group-badge">{g}</span>'
            f'<h2 class="group-title" data-zh="{html.escape(zh_title)}" data-en="{html.escape(en_title)}">'
            f'{g} · {html.escape(zh_title)} <span class="group-count">({len(g_styles)})</span></h2>'
            f'</div>'
            f'<div class="gallery group-gallery">{cards_html}</div>'
            f'</section>'
        )
    gallery_groups = "\n".join(group_sections)

    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>手绘风格编号画廊</title>
<script src="index-thumbnails.js"></script>{IMAGE_FALLBACK_SCRIPT}
<style>
:root{{color:#24211e;background:#f7f5f0;font:16px/1.5 system-ui,"Microsoft YaHei",sans-serif}}
body{{margin:0}}
main{{max-width:1440px;margin:auto;padding:18px 30px 30px}}
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
.sub-nav{{display:flex;gap:10px;align-items:center;padding:9px 30px;background:#faf7f2;border-bottom:1px solid #ded8cf;box-shadow:0 2px 6px rgba(0,0,0,0.03)}}
.filter{{display:inline-flex;align-items:center;gap:6px;border:1px solid #c9c1b6;border-radius:6px;background:#fff;color:#514a43;padding:6px 14px;font:inherit;font-size:14px;font-weight:600;line-height:1.4;cursor:pointer;transition:background .15s,color .15s,border-color .15s,box-shadow .15s}}
.filter:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}}
.filter span{{display:inline-block;padding:1px 6px;border-radius:999px;background:#eee8df;color:#6b6257;font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.2;transition:all .15s}}
.filter.is-active{{border-color:#b74227;background:#b74227;color:#fff;box-shadow:0 1px 3px rgba(183,66,39,0.3)}}
.filter.is-active span{{background:rgba(255,255,255,0.25);color:#fff}}
h1{{margin:0}}
.lead{{margin:8px 0 16px;color:#665f57}}
.prompt-examples{{display:flex;align-items:center;flex-wrap:wrap;gap:10px 18px;margin:12px 0 20px}}
.prompt-examples h2{{margin:0;color:#665f57;font-size:14px;font-weight:600}}
.prompt-example{{display:flex;align-items:center;gap:8px;min-width:0}}
.prompt-label{{color:#71685e;font-size:13px;white-space:nowrap}}
.prompt-value{{padding:5px 8px;border:1px solid #d9d2c8;border-radius:6px;background:#fffdf9;color:#24211e;font:13px/1.4 ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;white-space:nowrap}}
.prompt-notice{{width:100%;box-sizing:border-box;margin:2px 0 0;padding:9px 13px;border:1px solid #ded8cf;border-left:4px solid #d67d4d;border-radius:8px;background:#fff;color:#514a43;font-size:13.5px;line-height:1.6}}
.prompt-notice a,.prompt-notice button{{color:#b74227;font-weight:700;text-decoration:underline;text-underline-offset:2px;background:transparent;border:0;padding:0;font:inherit;cursor:pointer;display:inline}}
.prompt-notice a:hover,.prompt-notice button:hover{{color:#9f351f}}
.update-status{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0 18px;padding:9px 12px;border-left:3px solid #8b8177;background:#ece8e2;color:#514a43;font-size:14px}}
.update-status strong{{color:#24211e}}
.update-status.is-update{{border-color:#b74227;background:#fff0eb;color:#7f3022}}
.update-status button{{border:1px solid currentColor;border-radius:6px;background:transparent;color:inherit;padding:4px 8px;font:inherit;cursor:pointer}}
.update-status button:hover{{background:#ffffff80}}
.gallery-root{{display:block}}
.style-group{{margin-top:32px}}
.style-group.is-first,.is-filtered .style-group{{margin-top:10px}}
.group-header{{display:flex;align-items:center;gap:8px;padding-top:18px;border-top:1px dashed #dcd5ca;margin-bottom:12px}}
.style-group.is-first .group-header,.is-filtered .group-header{{border-top:none;padding-top:0}}
.group-badge{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;background:#b74227;color:#fff;font-size:12px;font-weight:800;border-radius:5px;line-height:1;flex-shrink:0}}
.group-title{{margin:0;font-size:14px;font-weight:700;color:#3b352f;display:flex;align-items:baseline;gap:6px}}
.group-count{{font-size:12px;color:#8c8276;font-weight:600;font-variant-numeric:tabular-nums}}
.gallery{{--columns:14;--gap:8px;display:grid;grid-template-columns:repeat(var(--columns),minmax(0,1fr));gap:var(--gap);align-items:start}}
.masonry-column{{display:flex;flex-direction:column;gap:var(--gap);min-width:0}}
.style-card{{display:block;box-sizing:border-box;position:relative;width:100%;margin:0;padding:0;border:0;border-radius:6px;background:#fff;box-shadow:0 1px 3px #0000001f;overflow:hidden;cursor:zoom-in;text-align:left;transition:transform .15s ease,box-shadow .15s ease}}
.style-card:hover{{transform:scale(1.04);z-index:5;box-shadow:0 4px 12px rgba(0,0,0,0.18)}}
.style-card:focus-visible,.filter:focus-visible,.copy:focus-visible,.close:focus-visible{{outline:2px solid #d67d4d;outline-offset:2px}}
.style-card img{{display:block;width:100%;height:auto;background:#ede8e1}}
.style-info{{display:block;padding:4px 5px;background:#fffdf9}}
.style-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:1px}}
.style-num{{color:#b74227;font-weight:850;font-size:11px;font-variant-numeric:tabular-nums;line-height:1.2}}
.style-group-pill{{font-size:9px;font-weight:700;color:#857b70;background:#eee9e0;padding:0 3px;border-radius:2px;line-height:1.2}}
.style-name{{display:block;font-weight:700;font-size:10.5px;color:#24211e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.25}}
.style-ref{{display:block;font-size:9.5px;color:#786f65;margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.2}}
dialog#preview{{width:min(94vw,960px);max-height:94vh;padding:18px;border:0;border-radius:14px;background:#171513;color:#fff;box-shadow:0 20px 70px #0008;box-sizing:border-box}}
dialog::backdrop{{background:#000b}}
.dialog-content{{display:flex;flex-direction:column;max-height:86vh}}
.dialog-image-box{{display:flex;align-items:center;justify-content:center;min-height:0;flex:1 1 auto;overflow:hidden}}
dialog img{{display:block;max-width:100%;max-height:60vh;margin:auto;object-fit:contain;border-radius:8px}}
.dialog-body{{margin-top:12px;display:flex;flex-direction:column;gap:8px;flex-shrink:0}}
.dialog-title-row{{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.dialog-title{{margin:0;font-size:17px;font-weight:700;color:#fff}}
.dialog-ref{{font-size:13.5px;color:#c4bbb0}}
.dialog-traits{{background:#23201d;border:1px solid #3d3731;border-radius:8px;padding:9px 12px;font-size:13px;line-height:1.5;color:#ded8cf;max-height:14vh;overflow-y:auto}}
.dialog-actions{{display:flex;align-items:center;gap:10px;margin-top:4px}}
.copy,.close{{border:0;border-radius:7px;padding:7px 12px;font:inherit;font-size:13.5px;font-weight:600;cursor:pointer;transition:background .15s,opacity .15s}}
.copy{{background:#b74227;color:#fff}}
.copy:hover{{background:#cf4f33}}
.copy-secondary{{background:#38332c;color:#ded8cf;border:1px solid #544d44}}
.copy-secondary:hover{{background:#4a443b;color:#fff}}
.close{{background:#332f2b;color:#ded8cf;margin-left:auto}}
.close:hover{{background:#47423d;color:#fff}}
.dialog-tip{{margin:6px 0 0;font-size:12px;color:#8e877e;text-align:center}}
.visually-hidden{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
[hidden]{{display:none!important}}
@media(min-width:1441px){{.gallery{{--columns:16;--gap:8px}}}}
@media(max-width:1200px){{.gallery{{--columns:11;--gap:7px}}}}
@media(max-width:960px){{.gallery{{--columns:9;--gap:6px}}}}
@media(max-width:760px){{main{{padding:14px 16px 20px}}
.site-nav{{padding:10px 16px;flex-wrap:wrap;gap:8px}}
.nav-right{{width:100%;justify-content:flex-start;gap:6px;margin-left:0}}
.site-nav a,.nav-btn{{padding:6px 10px;font-size:13px}}
.sub-nav{{padding:8px 16px;gap:6px;overflow-x:auto;-webkit-overflow-scrolling:touch}}
.filter{{padding:4px 8px;font-size:12.5px;white-space:nowrap}}
.prompt-examples{{align-items:flex-start;flex-direction:column;gap:8px}}
.prompt-example{{flex-wrap:wrap}}
.prompt-value{{white-space:normal}}
.gallery{{--columns:7;--gap:6px}}
.dialog-actions{{flex-wrap:wrap}}
.gallery-title-bar{{gap:10px}}
.gallery-title-bar h1{{font-size:22px}}
}}
@media(max-width:560px){{.gallery{{--columns:5;--gap:5px}}}}
@media(max-width:400px){{.gallery{{--columns:4;--gap:4px}}}}
.gallery-title-bar{{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:0 0 2px}}
.gallery-title-bar h1{{margin:0;font-size:26px;font-weight:800;color:#24211e;line-height:1.2}}
.size-switcher{{display:inline-flex;align-items:center;gap:6px;background:#eee8df;padding:3px 6px;border-radius:8px;border:1px solid #dcd5ca;margin-left:auto}}
.size-label{{font-size:12px;color:#786f65;font-weight:700;line-height:1;margin-left:2px}}
.size-btn-group{{display:inline-flex;align-items:center;gap:3px}}
.size-btn{{border:1px solid transparent;background:transparent;color:#514a43;font:inherit;font-size:12px;font-weight:750;padding:2px 8px;border-radius:5px;cursor:pointer;line-height:1.3;transition:background .15s,color .15s,border-color .15s,box-shadow .15s}}
.size-btn:hover{{color:#b74227;background:#ffffffa0}}
.size-btn.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 3px rgba(183,66,39,0.3)}}
.size-btn:focus-visible{{outline:2px solid #d67d4d;outline-offset:1px}}

[data-size="2x"] .gallery{{--columns:7;--gap:10px}}
[data-size="2x"] .style-info{{padding:6px 7px}}
[data-size="2x"] .style-num{{font-size:12px}}
[data-size="2x"] .style-group-pill{{font-size:10px;padding:1px 4px}}
[data-size="2x"] .style-name{{font-size:12px}}
[data-size="2x"] .style-ref{{font-size:11px}}
@media(min-width:1441px){{[data-size="2x"] .gallery{{--columns:8;--gap:10px}}}}
@media(max-width:1200px){{[data-size="2x"] .gallery{{--columns:6;--gap:9px}}}}
@media(max-width:960px){{[data-size="2x"] .gallery{{--columns:5;--gap:8px}}}}
@media(max-width:760px){{[data-size="2x"] .gallery{{--columns:4;--gap:8px}}}}
@media(max-width:560px){{[data-size="2x"] .gallery{{--columns:3;--gap:7px}}}}
@media(max-width:400px){{[data-size="2x"] .gallery{{--columns:2;--gap:6px}}}}

[data-size="3x"] .gallery{{--columns:5;--gap:12px}}
[data-size="3x"] .style-info{{padding:8px 9px}}
[data-size="3x"] .style-num{{font-size:13px}}
[data-size="3x"] .style-group-pill{{font-size:11px;padding:1px 5px}}
[data-size="3x"] .style-name{{font-size:13px}}
[data-size="3x"] .style-ref{{font-size:12px}}
@media(min-width:1441px){{[data-size="3x"] .gallery{{--columns:5;--gap:12px}}}}
@media(max-width:1200px){{[data-size="3x"] .gallery{{--columns:4;--gap:10px}}}}
@media(max-width:960px){{[data-size="3x"] .gallery{{--columns:3;--gap:10px}}}}
@media(max-width:760px){{[data-size="3x"] .gallery{{--columns:3;--gap:8px}}}}
@media(max-width:560px){{[data-size="3x"] .gallery{{--columns:2;--gap:8px}}}}
@media(max-width:400px){{[data-size="3x"] .gallery{{--columns:2;--gap:6px}}}}

[data-size="4x"] .gallery{{--columns:3;--gap:14px}}
[data-size="4x"] .style-info{{padding:9px 11px}}
[data-size="4x"] .style-num{{font-size:14px}}
[data-size="4x"] .style-group-pill{{font-size:11.5px;padding:2px 5px}}
[data-size="4x"] .style-name{{font-size:14px}}
[data-size="4x"] .style-ref{{font-size:12.5px}}
@media(min-width:1441px){{[data-size="4x"] .gallery{{--columns:4;--gap:14px}}}}
@media(max-width:1200px){{[data-size="4x"] .gallery{{--columns:3;--gap:12px}}}}
@media(max-width:960px){{[data-size="4x"] .gallery{{--columns:3;--gap:12px}}}}
@media(max-width:760px){{[data-size="4x"] .gallery{{--columns:2;--gap:10px}}}}
@media(max-width:560px){{[data-size="4x"] .gallery{{--columns:2;--gap:8px}}}}
@media(max-width:400px){{[data-size="4x"] .gallery{{--columns:1;--gap:8px}}}}
</style></head>
<body>
<header class="sticky-header">
<nav class="site-nav" aria-label="画廊导航"><a href="index.html" aria-current="page" data-i18n="stylesNav">风格画廊</a><a href="layouts.html" data-i18n="layoutsNav">图型画廊</a><a href="colors.html" data-i18n="colorsNav">色彩画廊</a><a href="assets.html" data-i18n="assetsNav">自建图库</a><a href="tutorials.html" data-i18n="tutorialsNav">提示词</a><div class="nav-right"><a class="nav-ext" href="https://github.com/yang0/handraw-style" target="_blank" rel="noopener noreferrer" title="GitHub 仓库"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a><a class="nav-ext" href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer" title="X (Twitter) @yang02010"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>X (@yang02010)</a><button class="nav-btn" id="wechat-btn" type="button" data-i18n="wechatBtn">💬 创作变现交流群</button><button class="nav-btn" id="lang-btn" type="button" aria-label="Switch Language">🌐 EN / 中</button></div></nav>
<nav class="sub-nav filters" aria-label="风格分类">{controls}</nav>
</header>
<main data-local-version="{version}" data-remote-version-url="{REMOTE_VERSION_URL}">
<div class="gallery-title-bar">
<h1 data-i18n="title">手绘风格编号画廊</h1>
<div class="size-switcher" role="group" aria-label="图片尺寸">
<span class="size-label" data-i18n="sizeLabel">尺寸</span>
<div class="size-btn-group">
<button type="button" class="size-btn is-active" data-size="1x">1x</button>
<button type="button" class="size-btn" data-size="2x">2x</button>
<button type="button" class="size-btn" data-size="3x">3x</button>
<button type="button" class="size-btn" data-size="4x">4x</button>
</div>
</div>
</div>
<p class="lead" data-i18n="lead">浏览 {total_count} 种手绘风格，点击卡片放大查看并复制生图指令与特征词。</p>
<section class="prompt-examples" aria-labelledby="prompt-examples-title">
<h2 id="prompt-examples-title" data-i18n="promptTitle">提示词案例</h2>
<div class="prompt-example"><span class="prompt-label" data-i18n="ex1Label">1 · 出图</span><code class="prompt-value" data-i18n="ex1Code">风格：001，主题：吃冰淇淋的小姑娘</code></div>
<div class="prompt-example"><span class="prompt-label" data-i18n="ex2Label">2 · 切换图文模式</span><code class="prompt-value" data-i18n="ex2Code">切换为图文模式</code></div>
<div class="prompt-example"><span class="prompt-label" data-i18n="ex3Label">3 · 海报提示词</span><code class="prompt-value" data-i18n="ex3Code">请帮我出海报提示词， 主题：秋分</code></div>
<div class="prompt-notice" data-i18n-html="promptNotice">💡 强烈推荐大家关注我的<a href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer">x账号</a>，或者<button type="button" class="open-wechat-modal">加入交流群</button>获取skill更新的最新信息。因为这不是一个发布就完事的skill，这段时间几乎每天都会有新的风格或者功能发布。</div>
</section>
<section id="update-status" class="update-status" role="status" aria-live="polite" hidden></section>
<h2 data-i18n="stylesTitle" class="visually-hidden">风格索引（{total_count}）</h2>
<section id="gallery" class="gallery-root">{gallery_groups}</section>
</main>
<dialog id="preview" aria-labelledby="dialog-title">
<div class="dialog-content">
<div class="dialog-image-box"><img id="preview-image" alt=""></div>
<div class="dialog-body">
<div class="dialog-title-row"><h3 class="dialog-title" id="dialog-title"></h3><span class="dialog-ref" id="dialog-ref"></span></div>
<div class="dialog-traits" id="dialog-traits"></div>
<div class="dialog-actions">
<button class="copy" id="copy-cmd" type="button" data-i18n="copyCmdBtn">复制出图指令</button>
<button class="copy copy-secondary" id="copy-traits" type="button" data-i18n="copyTraitsBtn">复制特征词</button>
<button class="close" type="button" data-i18n="closeBtn">关闭 ×</button>
</div>
</div>
<p class="dialog-tip" data-i18n="dialogTip">图片出于展示目的做了压缩，AI出的图字迹是很清晰的</p>
</div>
</dialog>
<dialog id="wechat-modal" aria-labelledby="wechat-title" style="width:min(94vw,560px);padding:22px;border:0;border-radius:14px;background:#1e1b18;color:#fff;box-shadow:0 20px 70px #000a;text-align:center"><button class="close" type="button" aria-label="关闭" style="position:absolute;top:12px;right:12px;border:0;border-radius:7px;padding:5px 9px;background:#fff;color:#24211e;cursor:pointer;font:inherit">关闭 ×</button><h3 id="wechat-title" style="margin:4px 0 10px;font-size:17px;color:#fff" data-i18n="wechatTitle">💬 创作变现交流群</h3><p style="margin:0 0 4px;font-size:14px;color:#eee" data-i18n="wechatSub">请优先加群，满了的话也可以尝试加我个人微信</p><p style="margin:0 0 16px;font-size:13px;color:#d67d4d;font-weight:600" data-i18n="wechatNote">请备注：手绘</p><div style="display:flex;justify-content:center;align-items:flex-start;gap:24px;flex-wrap:wrap"><div style="flex:1 1 200px;max-width:240px;background:#fff;padding:10px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.3)"><div style="color:#24211e;font-size:13px;font-weight:700;margin-bottom:6px" data-i18n="wechatGroupLabel">① 优先加入群聊</div><img src="../../../images/wechat_group.png" onerror="this.onerror=null;this.src='https://raw.githubusercontent.com/yang0/handraw-style/master/images/wechat_group.png';" alt="手绘交流群二维码" style="display:block;width:100%;height:auto;border-radius:6px"></div><div style="flex:1 1 200px;max-width:240px;background:#fff;padding:10px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.3)"><div style="color:#24211e;font-size:13px;font-weight:700;margin-bottom:6px" data-i18n="wechatPersonalLabel">② 个人微信备用</div><img src="../../../images/wechat_personal.png" onerror="this.onerror=null;this.src='https://raw.githubusercontent.com/yang0/handraw-style/master/images/wechat_personal.png';" alt="旺德福个人微信二维码" style="display:block;width:100%;height:auto;border-radius:6px"></div></div><div style="margin-top:16px;padding-top:12px;border-top:1px solid #332f2b;display:flex;justify-content:center;gap:16px;font-size:13px"><a href="https://github.com/yang0/handraw-style" target="_blank" rel="noopener noreferrer" style="color:#d67d4d;text-decoration:none;font-weight:600">GitHub 仓库 ↗</a><a href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer" style="color:#d67d4d;text-decoration:none;font-weight:600">X @yang02010 ↗</a></div></dialog>
<script>
const cards=[...document.querySelectorAll('.style-card')],filters=[...document.querySelectorAll('.filter')],sizeBtns=[...document.querySelectorAll('.size-btn')],dialog=document.querySelector('#preview'),preview=document.querySelector('#preview-image'),dialogTitle=document.querySelector('#dialog-title'),dialogRef=document.querySelector('#dialog-ref'),dialogTraits=document.querySelector('#dialog-traits'),copyCmdBtn=document.querySelector('#copy-cmd'),copyTraitsBtn=document.querySelector('#copy-traits'),gallery=document.querySelector('#gallery'),groupGalleries=[...document.querySelectorAll('.group-gallery')],styleGroups=[...document.querySelectorAll('.style-group')],mainElem=document.querySelector('main'),updateStatus=document.querySelector('#update-status'),localVersion=mainElem.dataset.localVersion||'1.0.0',remoteVersionUrl=mainElem.dataset.remoteVersionUrl,updateCommand='{UPDATE_COMMAND}',wechatBtn=document.querySelector('#wechat-btn'),wechatModal=document.querySelector('#wechat-modal'),langBtn=document.querySelector('#lang-btn');
let activeCard=null;
const groupMap=new Map();
groupGalleries.forEach(gGal=>groupMap.set(gGal,[...gGal.querySelectorAll('.style-card')]));
const I18N = {{
  zh: {{
    pageTitle: "手绘风格编号画廊",
    title: "手绘风格编号画廊",
    lead: "浏览 {total_count} 种手绘风格，点击卡片放大查看并复制生图指令与特征词。",
    sizeLabel: "尺寸",
    stylesNav: "风格画廊",
    layoutsNav: "图型画廊",
    colorsNav: "色彩画廊",
    assetsNav: "自建图库",
    tutorialsNav: "提示词",
    wechatBtn: "💬 创作变现交流群",
    promptTitle: "提示词案例",
    promptNotice: '💡 强烈推荐大家关注我的<a href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer">x账号</a>，或者<button type="button" class="open-wechat-modal">加入交流群</button>获取skill更新的最新信息。因为这不是一个发布就完事的skill，这段时间几乎每天都会有新的风格或者功能发布。',
    ex1Label: "1 · 出图",
    ex1Code: "风格：FA-001，主题：吃冰淇淋的小姑娘",
    ex2Label: "2 · 切换图文模式",
    ex2Code: "切换为图文模式",
    ex3Label: "3 · 海报提示词",
    ex3Code: "请帮我出海报提示词， 主题：秋分",
    stylesTitle: "风格索引（" + cards.length + "）",
    copyCmdBtn: "复制出图指令",
    copyTraitsBtn: "复制特征词",
    copied: "已复制",
    copyFailed: "复制失败",
    closeBtn: "关闭 ×",
    dialogTip: "图片出于展示目的做了压缩，AI出的图字迹是很清晰的",
    wechatTitle: "💬 创作变现交流群",
    wechatSub: "请优先加群，满了的话也可以尝试加我个人微信",
    wechatNote: "请备注：手绘",
    wechatGroupLabel: "① 优先加入群聊",
    wechatPersonalLabel: "② 个人微信备用",
    langBtn: "🌐 English",
    updateHeading: "发现风格库更新",
    updateMsg: "请复制更新指令，然后丢给 Codex 进行更新。",
    updateCopyBtn: "复制更新指令",
    updateCopied: "已复制",
    updateCopyFailed: "复制失败，请手动复制"
  }},
  en: {{
    pageTitle: "Hand-drawn Style Gallery",
    title: "Hand-drawn Style Gallery",
    lead: "Browse {total_count} hand-drawn styles. Click cards to enlarge and copy style commands and traits.",
    sizeLabel: "Size",
    stylesNav: "Styles",
    layoutsNav: "Layouts",
    colorsNav: "Colors",
    assetsNav: "Custom Library",
    tutorialsNav: "Prompts",
    wechatBtn: "💬 Creator Community",
    promptTitle: "Prompt Examples",
    promptNotice: '💡 Highly recommend following my <a href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer">X account</a> or <button type="button" class="open-wechat-modal">joining the community</button> to get the latest skill updates. This is not a one-and-done skill—new styles and features are released almost every day.',
    ex1Label: "1 · Generate",
    ex1Code: "Style: FA-001, Theme: Little girl eating ice cream",
    ex2Label: "2 · Graphic-Text Mode",
    ex2Code: "Switch to graphic-text mode",
    ex3Label: "3 · Poster Prompt",
    ex3Code: "Please generate a poster prompt for me, Theme: Autumn Equinox",
    stylesTitle: "Style Index (" + cards.length + ")",
    copyCmdBtn: "Copy Command",
    copyTraitsBtn: "Copy Traits",
    copied: "Copied!",
    copyFailed: "Copy failed",
    closeBtn: "Close ×",
    dialogTip: "Images are compressed for display; AI outputs are sharp and clear.",
    wechatTitle: "💬 Creator Monetization Community",
    wechatSub: "Please prioritize joining the group; if full, try adding personal WeChat",
    wechatNote: "Note: handdraw",
    wechatGroupLabel: "① Join Group (Priority)",
    wechatPersonalLabel: "② Personal WeChat (Fallback)",
    langBtn: "🌐 中文",
    updateHeading: "Style Library Update Available",
    updateMsg: "Copy update command and send to Codex to update.",
    updateCopyBtn: "Copy Update Command",
    updateCopied: "Copied",
    updateCopyFailed: "Failed to copy, please copy manually"
  }}
}};
let currentLang = localStorage.getItem('handdraw_lang') || ((navigator.language && navigator.language.startsWith('zh')) ? 'zh' : 'en');
function applyLang(lang) {{
  currentLang = lang;
  localStorage.setItem('handdraw_lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.title = I18N[lang].pageTitle;
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    const key = el.dataset.i18n;
    if (I18N[lang] && I18N[lang][key]) {{
      el.textContent = I18N[lang][key];
    }}
  }});
  document.querySelectorAll('[data-i18n-html]').forEach(el => {{
    const key = el.dataset.i18nHtml;
    if (I18N[lang] && I18N[lang][key]) {{
      el.innerHTML = I18N[lang][key];
    }}
  }});
  document.querySelectorAll('.filter').forEach(btn => {{
    const label = lang === 'en' ? btn.dataset.labelEn : btn.dataset.labelZh;
    if (btn.firstChild && btn.firstChild.nodeType === Node.TEXT_NODE) {{
      btn.firstChild.textContent = label + ' ';
    }}
  }});
  document.querySelectorAll('.style-group').forEach(groupSec => {{
    const g = groupSec.dataset.group;
    const titleEl = groupSec.querySelector('.group-title');
    const countEl = groupSec.querySelector('.group-count');
    if (titleEl && countEl) {{
      const text = lang === 'en' ? titleEl.dataset.en : titleEl.dataset.zh;
      titleEl.replaceChildren(document.createTextNode(`${{g}} · ${{text}} `), countEl);
    }}
  }});
  if (langBtn) langBtn.textContent = I18N[lang].langBtn;
  if (activeCard) updateDialogContent();
}}
if (langBtn) {{
  langBtn.addEventListener('click', () => {{
    applyLang(currentLang === 'zh' ? 'en' : 'zh');
  }});
}}
applyLang(currentLang);
document.addEventListener('click',event=>{{if(event.target.closest('.open-wechat-modal')){{event.preventDefault();if(wechatModal)wechatModal.showModal();}}}});
if(wechatBtn&&wechatModal){{wechatBtn.addEventListener('click',()=>wechatModal.showModal());wechatModal.querySelector('.close').addEventListener('click',()=>wechatModal.close());wechatModal.addEventListener('click',event=>{{if(event.target===wechatModal)wechatModal.close()}});}}

let layoutFrame=0;
function scheduleLayout(){{if(!layoutFrame)layoutFrame=requestAnimationFrame(arrangeCards);}}
function arrangeCards(){{
  layoutFrame=0;
  const focused=document.activeElement;
  groupGalleries.forEach(gGal=>{{
    const sec=gGal.closest('.style-group');
    if(sec&&sec.hidden)return;
    const gCards=groupMap.get(gGal)||[];
    const visibleCards=gCards.filter(card=>!card.hidden);
    if(!visibleCards.length)return;
    const count=Number(getComputedStyle(gGal).getPropertyValue('--columns'))||1;
    const gap=parseFloat(getComputedStyle(gGal).getPropertyValue('--gap'))||0;
    const columns=Array.from({{length:count}},()=>{{const col=document.createElement('div');col.className='masonry-column';return col;}});
    gGal.replaceChildren(...columns);
    const heights=Array(count).fill(0);
    visibleCards.forEach(card=>{{
      const index=heights.indexOf(Math.min(...heights));
      columns[index].append(card);
      heights[index]+=card.getBoundingClientRect().height+gap;
    }});
  }});
  if(cards.includes(focused)&&!focused.hidden)focused.focus({{preventScroll:true}});
}}
function setCategory(group){{
  document.body.classList.toggle('is-filtered',group!=='all');
  filters.forEach(btn=>btn.classList.toggle('is-active',btn.dataset.group===group));
  styleGroups.forEach(sec=>{{
    sec.hidden=group!=='all'&&sec.dataset.group!==group;
  }});
  cards.forEach(card=>{{
    card.hidden=group!=='all'&&card.dataset.group!==group;
  }});
  scheduleLayout();
}}
cards.forEach(card=>{{
  const img=card.querySelector('img');
  img.addEventListener('load',scheduleLayout);
  img.addEventListener('error',scheduleLayout);
}});
let lastWidth=-1;
new ResizeObserver(entries=>{{
  const width=entries[0].contentRect.width;
  if(width!==lastWidth){{lastWidth=width;scheduleLayout();}}
}}).observe(gallery);
window.addEventListener('resize',scheduleLayout);
if(document.fonts)document.fonts.ready.then(scheduleLayout);

function updateDialogContent(){{
  if(!activeCard) return;
  const num=activeCard.dataset.number;
  const name=activeCard.dataset.name;
  const ref=activeCard.dataset.reference;
  const traits=activeCard.dataset.traits;
  dialogTitle.textContent=`#${{num}} · ${{name}}`;
  dialogRef.textContent=(currentLang==='en'?'Reference: ':'参考：')+ref;
  dialogTraits.textContent=traits;
  copyCmdBtn.textContent=I18N[currentLang].copyCmdBtn;
  copyTraitsBtn.textContent=I18N[currentLang].copyTraitsBtn;
}}
function openPreview(card){{
  activeCard=card;
  const cardImg=card.querySelector('img');
  preview.src=(cardImg&&cardImg.src)?cardImg.src:card.dataset.image;
  preview.alt=`#${{card.dataset.number}} ${{card.dataset.name}}`;
  updateDialogContent();
  dialog.showModal();
}}
async function copyText(text,button,successLabel){{
  try{{
    await navigator.clipboard.writeText(text);
    button.textContent=successLabel;
    setTimeout(()=>{{updateDialogContent();}},1500);
  }}catch{{
    const area=document.createElement('textarea');
    area.value=text;
    area.style.position='fixed';
    area.style.opacity='0';
    document.body.append(area);
    area.select();
    document.execCommand('copy');
    area.remove();
    button.textContent=successLabel;
    setTimeout(()=>{{updateDialogContent();}},1500);
  }}
}}
copyCmdBtn.addEventListener('click',()=>{{
  if(!activeCard) return;
  const num=activeCard.dataset.number;
  const cmd=currentLang==='en'?`Style: ${{num}}, Theme: `:`风格：${{num}}，主题：`;
  copyText(cmd,copyCmdBtn,I18N[currentLang].copied);
}});
copyTraitsBtn.addEventListener('click',()=>{{
  if(!activeCard) return;
  copyText(activeCard.dataset.traits,copyTraitsBtn,I18N[currentLang].copied);
}});
filters.forEach(button=>button.addEventListener('click',()=>setCategory(button.dataset.group)));
cards.forEach(card=>card.addEventListener('click',()=>openPreview(card)));
dialog.querySelector('.close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{{if(event.target===dialog)dialog.close()}});

function setSize(size){{
  const targetSize=['1x','2x','3x','4x'].includes(size)?size:'1x';
  document.body.dataset.size=targetSize;
  localStorage.setItem('handdraw_gallery_size',targetSize);
  sizeBtns.forEach(btn=>btn.classList.toggle('is-active',btn.dataset.size===targetSize));
  scheduleLayout();
}}
sizeBtns.forEach(btn=>btn.addEventListener('click',()=>setSize(btn.dataset.size)));
const urlSize=new URLSearchParams(window.location.search).get('size');
const savedSize=urlSize||localStorage.getItem('handdraw_gallery_size')||'1x';
setSize(savedSize);

const urlCat=new URLSearchParams(window.location.search).get('cat')||(window.location.hash?window.location.hash.replace(/^#/,''):'');
if(urlCat&&filters.some(b=>b.dataset.group===urlCat)){{
  setCategory(urlCat);
}}else{{
  setCategory('all');
}}

function showUpdateStatus(remoteVer){{
  const t = I18N[currentLang] || I18N.zh;
  updateStatus.hidden=false;
  updateStatus.className='update-status is-update';
  updateStatus.replaceChildren();
  const heading=document.createElement('strong'),message=document.createElement('span'),copyButton=document.createElement('button');
  heading.textContent=t.updateHeading+(remoteVer?' (v'+remoteVer+')':'');
  message.textContent=t.updateMsg;
  copyButton.type='button';
  copyButton.textContent=t.updateCopyBtn;
  copyButton.addEventListener('click',async()=>{{try{{await navigator.clipboard.writeText(updateCommand);copyButton.textContent=t.updateCopied;}}catch{{copyButton.textContent=t.updateCopyFailed;}}}});
  updateStatus.append(heading,message,copyButton);
}}
function isNewerVersion(remote,local){{
  const clean=s=>String(s).replace(/^v/i,''),r=clean(remote).split('.').map(n=>parseInt(n,10)||0),l=clean(local).split('.').map(n=>parseInt(n,10)||0);
  for(let i=0;i<Math.max(r.length,l.length);i++){{const rv=r[i]||0,lv=l[i]||0;if(rv>lv)return true;if(rv<lv)return false;}}
  return false;
}}
async function checkRepositoryUpdate(){{
  try{{
    const response=await fetch(remoteVersionUrl);
    if(!response.ok)throw new Error('Remote version is unavailable');
    const data=await response.json();
    const remoteVer=typeof data==='object'&&data!==null?(data.version||''):String(data);
    if(remoteVer&&isNewerVersion(remoteVer,localVersion))showUpdateStatus(remoteVer);
  }}catch{{}}
}}
checkRepositoryUpdate();
</script></body></html>'''


def main() -> None:
    styles = parse_styles()
    if len(styles) < 365:
        raise SystemExit(f"Expected at least the 365 baseline styles, parsed {len(styles)}")
    cat_counts: dict[str, int] = {}
    for item in styles:
        m = re.match(r"^([A-Za-z]{2})-(\d{3})$", item["number"])
        if not m:
            raise SystemExit(f"Invalid style number format: {item['number']}")
        cat, idx = m.group(1), int(m.group(2))
        expected_idx = cat_counts.get(cat, 0) + 1
        if idx != expected_idx:
            raise SystemExit(f"Non-continuous style number in category {cat}: expected {cat}-{expected_idx:03}, got {item['number']}")
        cat_counts[cat] = idx
    STYLE_JSON.parent.mkdir(parents=True, exist_ok=True)
    GALLERY.parent.mkdir(parents=True, exist_ok=True)
    STYLE_JSON.write_text(json.dumps(styles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GALLERY.write_text(gallery_html(styles).replace("</body>", '<script src="personal-library.js" defer></script><script src="local-navigation.js" defer></script></body>'), encoding="utf-8")
    write_thumbnail_fallback(GALLERY)
    print(f"Built {len(styles)} styles into adaptive waterfall gallery.")
    try:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_markdown_galleries import build_styles_md
        build_styles_md()
    except Exception as exc:
        print(f"Notice: build_styles_md skipped: {exc}")


if __name__ == "__main__":
    main()
