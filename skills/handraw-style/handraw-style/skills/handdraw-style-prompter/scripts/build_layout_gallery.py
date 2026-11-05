#!/usr/bin/env python3
"""Build the offline layout gallery from the canonical layout index."""
from __future__ import annotations

from gallery_thumbnails import write_thumbnail_fallback

import html
from pathlib import Path

from layout_library import load_layouts


SKILL = Path(__file__).resolve().parents[1]
GALLERY = SKILL / "gallery" / "layouts.html"
CATEGORIES = (
    ("social-card", "社媒卡", "Social Cards"),
    ("infographic", "信息图", "Infographics"),
    ("comic-storyboard", "漫画分镜", "Comic Storyboards"),
    ("ip-character", "IP设计", "IP Design"),
    ("ecommerce", "电商", "E-commerce"),
)

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


def gallery_html(layouts: list[dict[str, object]]) -> str:
    counts = {category: sum(layout["category"] == category for layout in layouts) for category, _, _ in CATEGORIES}
    visible_categories = [(category, label_zh, label_en) for category, label_zh, label_en in CATEGORIES if counts[category]]
    initial_category = visible_categories[0][0] if visible_categories else ""
    controls = "".join(
        f'<button class="filter" type="button" data-category="{category}" data-label-zh="{label_zh}" data-label-en="{label_en}">{label_zh} <span>{counts[category]}</span></button>'
        for category, label_zh, label_en in visible_categories
    )
    cards = "\n".join(
        f'<button class="layout-card" type="button" data-id="{layout["id"]}" data-category="{layout["category"]}" '
        f'data-image="{html.escape(str(layout["image"]), quote=True)}" '
        f'data-prompt="{html.escape(str(layout["prompts"]["zh"]), quote=True)}" '
        f'data-prompt-zh="{html.escape(str(layout["prompts"]["zh"]), quote=True)}" '
        f'data-prompt-en="{html.escape(str(layout["prompts"]["en"]), quote=True)}" '
        f'data-name="{html.escape(str(layout["name"]), quote=True)}" '
        f'data-name-zh="{html.escape(str(layout["name"]), quote=True)}" '
        f'data-name-en="{html.escape(str(layout.get("name_en", layout["name"])), quote=True)}" '
        f'aria-label="查看 {layout["id"]} {html.escape(str(layout["name"]), quote=True)}">'
        f'<img src="{html.escape(str(layout["image"]), quote=True)}" alt="{layout["id"]} {html.escape(str(layout["name"]), quote=True)}">'
        f'<span class="layout-info"><span class="layout-id">{layout["id"]}</span><span class="layout-name">{html.escape(str(layout["name"]))}</span></span></button>'
        for layout in layouts
    )
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>图型编号画廊</title>
<script src="layouts-thumbnails.js"></script>{IMAGE_FALLBACK_SCRIPT}
<style>
:root{{color:#24211e;background:#f7f5f0;font:16px/1.5 system-ui,"Microsoft YaHei",sans-serif}} body{{margin:0}} main{{max-width:1440px;margin:auto;padding:18px 30px 30px}} .sticky-header{{position:sticky;top:0;z-index:100}} .site-nav{{display:flex;align-items:center;gap:10px;margin:0;padding:12px 30px;border-bottom:1px solid #ded8cf;background:#fffdf9}} .site-nav a{{border:1px solid #9e9185;border-radius:8px;background:#fff;color:#403a34;padding:7px 13px;text-decoration:none;font-weight:800;line-height:1.2;transition:background .15s,color .15s,border-color .15s}} .site-nav a:hover{{border-color:#b74227;background:#fff0eb;color:#9f351f}} .site-nav a[aria-current="page"]{{border-color:#b74227;background:#b74227;color:#fff;box-shadow:0 1px 3px #b7422744}} .nav-right{{margin-left:auto;display:flex;align-items:center;gap:8px}} .nav-ext{{display:inline-flex;align-items:center;font-weight:700}} .nav-btn{{border:1px solid #9e9185;border-radius:8px;background:#fff;color:#403a34;padding:7px 13px;font:inherit;font-weight:700;line-height:1.2;cursor:pointer;transition:background .15s,color .15s,border-color .15s}} .nav-btn:hover{{border-color:#b74227;background:#fff0eb;color:#9f351f}} .nav-btn:focus-visible,.site-nav a:focus-visible{{outline:3px solid #d67d4d;outline-offset:3px}} .sub-nav{{display:flex;gap:10px;align-items:center;padding:9px 30px;background:#faf7f2;border-bottom:1px solid #ded8cf;box-shadow:0 2px 6px rgba(0,0,0,0.03)}} .filter{{display:inline-flex;align-items:center;gap:6px;border:1px solid #c9c1b6;border-radius:6px;background:#fff;color:#514a43;padding:6px 14px;font:inherit;font-size:14px;font-weight:600;line-height:1.4;cursor:pointer;transition:background .15s,color .15s,border-color .15s,box-shadow .15s}} .filter:hover{{border-color:#b74227;color:#b74227;background:#fff8f5}} .filter span{{display:inline-block;padding:1px 6px;border-radius:999px;background:#eee8df;color:#6b6257;font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.2;transition:all .15s}} .filter.is-active{{border-color:#b74227;background:#b74227;color:#fff;box-shadow:0 1px 3px rgba(183,66,39,0.3)}} .filter.is-active span{{background:rgba(255,255,255,0.25);color:#fff}} h1{{margin:0}} .lead{{margin:8px 0 20px;color:#665f57}}
.gallery-title-bar{{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:0 0 2px}}
.gallery-title-bar h1{{margin:0;font-size:26px;font-weight:800;color:#24211e;line-height:1.2}}
.size-switcher{{display:inline-flex;align-items:center;gap:6px;background:#eee8df;padding:3px 6px;border-radius:8px;border:1px solid #dcd5ca;margin-left:auto}}
.size-label{{font-size:12px;color:#786f65;font-weight:700;line-height:1;margin-left:2px}}
.size-btn-group{{display:inline-flex;align-items:center;gap:3px}}
.size-btn{{border:1px solid transparent;background:transparent;color:#514a43;font:inherit;font-size:12px;font-weight:750;padding:2px 8px;border-radius:5px;cursor:pointer;line-height:1.3;transition:background .15s,color .15s,border-color .15s,box-shadow .15s}}
.size-btn:hover{{color:#b74227;background:#ffffffa0}}
.size-btn.is-active{{background:#b74227;color:#fff;border-color:#b74227;box-shadow:0 1px 3px rgba(183,66,39,0.3)}}
.size-btn:focus-visible{{outline:2px solid #d67d4d;outline-offset:1px}}

/* 2x Default: standard size (4 columns on desktop) */
.gallery{{--columns:4;--gap:18px;display:grid;grid-template-columns:repeat(var(--columns),minmax(0,1fr));gap:var(--gap);align-items:start}}
.masonry-column{{display:flex;flex-direction:column;gap:var(--gap);min-width:0}}
.layout-card{{display:block;box-sizing:border-box;position:relative;width:100%;margin:0;padding:0;border:0;border-radius:12px;background:#fff;box-shadow:0 1px 5px #0002;overflow:hidden;cursor:zoom-in;text-align:left}}
.layout-card:focus-visible,.filter:focus-visible,.copy:focus-visible,.close:focus-visible{{outline:3px solid #d67d4d;outline-offset:3px}}
.layout-card img{{display:block;width:100%;height:auto}}
.layout-info{{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:10px 12px;background:#fffdf9}}
.layout-id{{color:#b74227;font-weight:850;font-variant-numeric:tabular-nums;white-space:nowrap}}
.layout-name{{overflow:hidden;color:#514a43;font-size:13px;text-overflow:ellipsis;white-space:nowrap}}
@media(max-width:1100px){{.gallery{{--columns:3}}}}
@media(max-width:720px){{main{{padding:16px 20px 20px}} .site-nav{{padding:10px 20px;flex-wrap:wrap;gap:8px}} .nav-right{{width:100%;justify-content:flex-start;gap:6px;margin-left:0}} .site-nav a,.nav-btn{{padding:6px 10px;font-size:13px}} .sub-nav{{padding:8px 20px;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch}} .filter{{padding:5px 10px;font-size:13px;white-space:nowrap}} .gallery{{--columns:2;--gap:12px}} .layout-info{{display:block;padding:8px 10px}} .layout-name{{display:block;margin-top:2px}}}}
@media(max-width:420px){{.gallery{{--columns:1}}}}

/* 1x: compact half size (8 columns on desktop) */
[data-size="1x"] .gallery{{--columns:8;--gap:10px}}
[data-size="1x"] .layout-card{{border-radius:8px;box-shadow:0 1px 4px #0002}}
[data-size="1x"] .layout-info{{display:flex;align-items:baseline;justify-content:space-between;gap:6px;padding:6px 8px}}
[data-size="1x"] .layout-id{{font-size:11.5px}}
[data-size="1x"] .layout-name{{font-size:11.5px}}
@media(min-width:1441px){{[data-size="1x"] .gallery{{--columns:8;--gap:10px}}}}
@media(max-width:1200px){{[data-size="1x"] .gallery{{--columns:6;--gap:9px}}}}
@media(max-width:960px){{[data-size="1x"] .gallery{{--columns:5;--gap:8px}}}}
@media(max-width:720px){{[data-size="1x"] .gallery{{--columns:4;--gap:8px}} [data-size="1x"] .layout-info{{display:block;padding:5px 6px}}}}
@media(max-width:480px){{[data-size="1x"] .gallery{{--columns:2;--gap:6px}}}}

dialog{{width:min(94vw,1100px);padding:14px;border:0;border-radius:14px;background:#171513;color:#fff;box-shadow:0 20px 70px #0008}} dialog::backdrop{{background:#000b}} dialog img{{display:block;max-width:100%;max-height:78vh;margin:auto;object-fit:contain}} .dialog-actions{{display:flex;align-items:center;gap:10px;justify-content:space-between;margin-top:10px}} .dialog-label{{margin:0;font-weight:700}} .copy,.close{{border:0;border-radius:7px;padding:7px 10px;background:#fff;color:#24211e;font:inherit;cursor:pointer}} .copy{{margin-left:auto}} .dialog-tip{{margin:8px 0 0;font-size:12px;color:#a8a199;text-align:center}} [hidden]{{display:none!important}}
</style></head><body>
<header class="sticky-header">
<nav class="site-nav" aria-label="画廊导航"><a href="index.html" data-i18n="stylesNav">风格画廊</a><a href="layouts.html" aria-current="page" data-i18n="layoutsNav">图型画廊</a><a href="colors.html" data-i18n="colorsNav">色彩画廊</a><a href="assets.html" data-i18n="assetsNav">自建图库</a><a href="tutorials.html" data-i18n="tutorialsNav">提示词</a><div class="nav-right"><a class="nav-ext" href="https://github.com/yang0/handraw-style" target="_blank" rel="noopener noreferrer" title="GitHub 仓库"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a><a class="nav-ext" href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer" title="X (Twitter) @yang02010"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>X (@yang02010)</a><button class="nav-btn" id="wechat-btn" type="button" data-i18n="wechatBtn">💬 创作变现交流群</button><button class="nav-btn" id="lang-btn" type="button" aria-label="Switch Language">🌐 EN / 中</button></div></nav>
<nav class="sub-nav filters" aria-label="图型分类">{controls}</nav>
</header>
<main>
<div class="gallery-title-bar">
<h1 data-i18n="title">图型编号画廊</h1>
<div class="size-switcher" role="group" aria-label="图片尺寸">
<span class="size-label" data-i18n="sizeLabel">尺寸</span>
<div class="size-btn-group">
<button type="button" class="size-btn" data-size="1x">1x</button>
<button type="button" class="size-btn is-active" data-size="2x">2x</button>
</div>
</div>
</div>
<p class="lead" id="gallery-lead" data-i18n="lead">社媒卡：画面有呼吸感，认知负担低，适合小红书和公众号贴图</p>
<section id="gallery" class="gallery">{cards}</section>
</main>
<dialog id="preview" aria-labelledby="dialog-label"><img id="preview-image" alt=""><div class="dialog-actions"><p class="dialog-label" id="dialog-label"></p><button class="copy" id="copy" type="button" data-i18n="copyBtn">复制排版提示词</button><button class="close" type="button" data-i18n="closeBtn">关闭 ×</button></div><p class="dialog-tip" data-i18n="dialogTip">图片出于展示目的做了压缩，AI出的图字迹是很清晰的</p></dialog>
<dialog id="wechat-modal" aria-labelledby="wechat-title" style="width:min(94vw,560px);padding:22px;border:0;border-radius:14px;background:#1e1b18;color:#fff;box-shadow:0 20px 70px #000a;text-align:center"><button class="close" type="button" aria-label="关闭" style="position:absolute;top:12px;right:12px;border:0;border-radius:7px;padding:5px 9px;background:#fff;color:#24211e;cursor:pointer;font:inherit">关闭 ×</button><h3 id="wechat-title" style="margin:4px 0 10px;font-size:17px;color:#fff" data-i18n="wechatTitle">💬 创作变现交流群</h3><p style="margin:0 0 4px;font-size:14px;color:#eee" data-i18n="wechatSub">请优先加群，满了的话也可以尝试加我个人微信</p><p style="margin:0 0 16px;font-size:13px;color:#d67d4d;font-weight:600" data-i18n="wechatNote">请备注：手绘</p><div style="display:flex;justify-content:center;align-items:flex-start;gap:24px;flex-wrap:wrap"><div style="flex:1 1 200px;max-width:240px;background:#fff;padding:10px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.3)"><div style="color:#24211e;font-size:13px;font-weight:700;margin-bottom:6px" data-i18n="wechatGroupLabel">① 优先加入群聊</div><img src="../../../images/wechat_group.png" onerror="this.onerror=null;this.src='https://raw.githubusercontent.com/yang0/handraw-style/master/images/wechat_group.png';" alt="手绘交流群二维码" style="display:block;width:100%;height:auto;border-radius:6px"></div><div style="flex:1 1 200px;max-width:240px;background:#fff;padding:10px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.3)"><div style="color:#24211e;font-size:13px;font-weight:700;margin-bottom:6px" data-i18n="wechatPersonalLabel">② 个人微信备用</div><img src="../../../images/wechat_personal.png" onerror="this.onerror=null;this.src='https://raw.githubusercontent.com/yang0/handraw-style/master/images/wechat_personal.png';" alt="旺德福个人微信二维码" style="display:block;width:100%;height:auto;border-radius:6px"></div></div><div style="margin-top:16px;padding-top:12px;border-top:1px solid #332f2b;display:flex;justify-content:center;gap:16px;font-size:13px"><a href="https://github.com/yang0/handraw-style" target="_blank" rel="noopener noreferrer" style="color:#d67d4d;text-decoration:none;font-weight:600">GitHub 仓库 ↗</a><a href="https://x.com/yang02010" target="_blank" rel="noopener noreferrer" style="color:#d67d4d;text-decoration:none;font-weight:600">X @yang02010 ↗</a></div></dialog>
<script>
const cards=[...document.querySelectorAll('.layout-card')],filters=[...document.querySelectorAll('.filter')],sizeBtns=[...document.querySelectorAll('.size-btn')],dialog=document.querySelector('#preview'),preview=document.querySelector('#preview-image'),label=document.querySelector('#dialog-label'),copyButton=document.querySelector('#copy'),wechatBtn=document.querySelector('#wechat-btn'),wechatModal=document.querySelector('#wechat-modal'),langBtn=document.querySelector('#lang-btn');
let activePrompt='', activeCard=null;
const I18N = {{
  zh: {{
    pageTitle: "图型编号画廊",
    stylesNav: "风格画廊",
    layoutsNav: "图型画廊",
    colorsNav: "色彩画廊",
    assetsNav: "自建图库",
    tutorialsNav: "提示词",
    wechatBtn: "💬 创作变现交流群",
    title: "图型编号画廊",
    sizeLabel: "尺寸",
    leads: {{
      "social-card": "社媒卡：画面有呼吸感，认知负担低，适合小红书和公众号贴图",
      "infographic": "信息图：层级逻辑清晰、数据结构一目了然，适合知识科普与深度干货表达",
      "comic-storyboard": "漫画分镜：多格连续叙事、镜头节奏分明，适合故事阐述与趣味条漫表达",
      "ip-character": "IP设计流程建议：先设计IP-001，出图后输入提示词：[把图片加入角色库]，后面即可持续引用基准图生成系列物料",
      "ecommerce": "电商：图片只做业务场景演示，不做排版演示，根据商品不同，出的图可能完全不同"
    }},
    copyBtn: "复制排版提示词",
    copied: "已复制",
    copyFailed: "复制失败",
    closeBtn: "关闭 ×",
    dialogTip: "图片出于展示目的做了压缩，AI出的图字迹是很清晰的",
    wechatTitle: "💬 创作变现交流群",
    wechatSub: "请优先加群，满了的话也可以尝试加我个人微信",
    wechatNote: "请备注：手绘",
    wechatGroupLabel: "① 优先加入群聊",
    wechatPersonalLabel: "② 个人微信备用",
    langBtn: "🌐 English"
  }},
  en: {{
    pageTitle: "Layout Numbered Gallery",
    stylesNav: "Styles",
    layoutsNav: "Layouts",
    colorsNav: "Colors",
    assetsNav: "Custom Library",
    tutorialsNav: "Prompts",
    wechatBtn: "💬 Creator Community",
    title: "Layout Numbered Gallery",
    sizeLabel: "Size",
    leads: {{
      "social-card": "Social Cards: Airy visual breathing room with low cognitive load, ideal for Xiaohongshu and WeChat posts.",
      "infographic": "Infographics: Clear hierarchical logic and intuitive data structures, ideal for knowledge explainers and in-depth educational posts.",
      "comic-storyboard": "Comic Storyboards: Multi-panel continuous sequential narrative with cinematic pacing, ideal for storytelling and entertaining comics.",
      "ip-character": "IP Design Workflow: Design IP-001 first. After generation, enter prompt: [Add image to character library], then reference this base image for subsequent visuals.",
      "ecommerce": "E-commerce: Images are for business scenario demonstration only, not layout templates; actual visuals will vary based on product inputs."
    }},
    copyBtn: "Copy Layout Prompt",
    copied: "Copied!",
    copyFailed: "Copy failed",
    closeBtn: "Close ×",
    dialogTip: "Images are compressed for display; AI outputs are sharp and clear.",
    wechatTitle: "💬 Creator Monetization Community",
    wechatSub: "Please prioritize joining the group; if full, try adding personal WeChat",
    wechatNote: "Note: handdraw",
    wechatGroupLabel: "① Join Group (Priority)",
    wechatPersonalLabel: "② Personal WeChat (Fallback)",
    langBtn: "🌐 中文"
  }}
}};
let currentLang = localStorage.getItem('handdraw_lang') || ((navigator.language && navigator.language.startsWith('zh')) ? 'zh' : 'en');
let activeCategory = 'social-card';
function updateLead() {{
  const leadEl = document.querySelector('#gallery-lead');
  if (leadEl && I18N[currentLang] && I18N[currentLang].leads) {{
    leadEl.textContent = I18N[currentLang].leads[activeCategory] || I18N[currentLang].leads['social-card'];
  }}
}}
function applyLang(lang) {{
  currentLang = lang;
  localStorage.setItem('handdraw_lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.title = I18N[lang].pageTitle;
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    const key = el.dataset.i18n;
    if (key !== 'lead' && I18N[lang] && I18N[lang][key]) {{
      el.textContent = I18N[lang][key];
    }}
  }});
  updateLead();
  document.querySelectorAll('.filter').forEach(btn => {{
    const label = lang === 'en' ? btn.dataset.labelEn : btn.dataset.labelZh;
    if (btn.firstChild && btn.firstChild.nodeType === Node.TEXT_NODE) {{
      btn.firstChild.textContent = label + ' ';
    }}
  }});
  document.querySelectorAll('.layout-card').forEach(card => {{
    const name = lang === 'en' ? (card.dataset.nameEn || card.dataset.name) : card.dataset.nameZh;
    const nameSpan = card.querySelector('.layout-name');
    if (nameSpan) nameSpan.textContent = name;
    card.setAttribute('aria-label', (lang === 'en' ? 'View ' : '查看 ') + card.dataset.id + ' ' + name);
  }});
  if (langBtn) langBtn.textContent = I18N[lang].langBtn;
  updateActivePrompt();
}}
if (langBtn) {{
  langBtn.addEventListener('click', () => {{
    applyLang(currentLang === 'zh' ? 'en' : 'zh');
  }});
}}
applyLang(currentLang);

const gallery=document.querySelector('#gallery');let layoutFrame=0;
function scheduleLayout(){{if(!layoutFrame)layoutFrame=requestAnimationFrame(arrangeCards);}}
function arrangeCards(){{
    layoutFrame=0;
    const focused=document.activeElement;
    const count=Number(getComputedStyle(gallery).getPropertyValue('--columns'))||1;
    const gap=parseFloat(getComputedStyle(gallery).getPropertyValue('--gap'))||0;
    const columns=Array.from({{length:count}},()=>{{const column=document.createElement('div');column.className='masonry-column';return column;}});
    gallery.replaceChildren(...columns);
    const heights=Array(count).fill(0);
    cards.filter(card=>!card.hidden).forEach(card=>{{
        const index=heights.indexOf(Math.min(...heights));
        columns[index].append(card);
        heights[index]+=card.getBoundingClientRect().height+gap;
    }});
    if(cards.includes(focused)&&!focused.hidden)focused.focus({{preventScroll:true}});
}}
function setCategory(category){{
  activeCategory = category;
  filters.forEach(button=>button.classList.toggle('is-active',button.dataset.category===category));
  cards.forEach(card=>{{card.hidden=card.dataset.category!==category;}});
  updateLead();
  scheduleLayout();
}}
cards.forEach(card=>{{const img=card.querySelector('img');img.addEventListener('load',scheduleLayout);img.addEventListener('error',scheduleLayout);}});
let lastWidth=-1;
new ResizeObserver(entries=>{{const width=entries[0].contentRect.width;if(width!==lastWidth){{lastWidth=width;scheduleLayout();}}}}).observe(gallery);
window.addEventListener('resize',scheduleLayout);
if(document.fonts)document.fonts.ready.then(scheduleLayout);

function setSize(size){{
  const targetSize=['1x','2x'].includes(size)?size:'2x';
  document.body.dataset.size=targetSize;
  localStorage.setItem('handdraw_layout_size',targetSize);
  sizeBtns.forEach(btn=>btn.classList.toggle('is-active',btn.dataset.size===targetSize));
  scheduleLayout();
}}
sizeBtns.forEach(btn=>btn.addEventListener('click',()=>setSize(btn.dataset.size)));
const savedSize=localStorage.getItem('handdraw_layout_size');
if(savedSize)setSize(savedSize);else setSize('2x');
if(wechatBtn&&wechatModal){{wechatBtn.addEventListener('click',()=>wechatModal.showModal());wechatModal.querySelector('.close').addEventListener('click',()=>wechatModal.close());wechatModal.addEventListener('click',event=>{{if(event.target===wechatModal)wechatModal.close()}});}}

function updateActivePrompt(){{
    if(!activeCard) return;
    activePrompt=(currentLang==='en'?activeCard.dataset.promptEn:activeCard.dataset.promptZh)||activeCard.dataset.prompt||'';
    const name = currentLang === 'en' ? (activeCard.dataset.nameEn || activeCard.dataset.name) : activeCard.dataset.nameZh;
    label.textContent=`${{activeCard.querySelector('.layout-id').textContent}} · ${{name}}`;
    if (preview) preview.alt=`${{activeCard.dataset.id||''}} ${{name}}`;
}}
function openPreview(card){{
    activeCard=card;
    const cardImg=card.querySelector('img');
    preview.src=(cardImg&&cardImg.src)?cardImg.src:card.dataset.image;
    updateActivePrompt();
    copyButton.textContent=I18N[currentLang].copyBtn;
    dialog.showModal();
}}
async function copyPrompt(){{
    updateActivePrompt();
    try{{
        await navigator.clipboard.writeText(activePrompt);
        copyButton.textContent=I18N[currentLang].copied;
        setTimeout(()=>{{copyButton.textContent=I18N[currentLang].copyBtn;}},1500);
    }}catch{{
        const area=document.createElement('textarea');
        area.value=activePrompt;
        area.style.position='fixed';
        area.style.opacity='0';
        document.body.append(area);
        area.select();
        document.execCommand('copy');
        area.remove();
        copyButton.textContent=I18N[currentLang].copied;
        setTimeout(()=>{{copyButton.textContent=I18N[currentLang].copyBtn;}},1500);
    }}
}}
filters.forEach(button=>button.addEventListener('click',()=>setCategory(button.dataset.category)));cards.forEach(card=>card.addEventListener('click',()=>openPreview(card)));copyButton.addEventListener('click',copyPrompt);dialog.querySelector('.close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',event=>{{if(event.target===dialog)dialog.close()}});
const urlCat=new URLSearchParams(window.location.search).get('cat')||(window.location.hash?window.location.hash.replace(/^#/,''):'');
if(urlCat&&filters.some(b=>b.dataset.category===urlCat)){{setCategory(urlCat);}}else{{setCategory('social-card');}}
</script></body></html>'''


def main() -> None:
    layouts = load_layouts()
    GALLERY.parent.mkdir(parents=True, exist_ok=True)
    GALLERY.write_text(gallery_html(layouts).replace("</body>", '<script src="personal-library.js" defer></script><script src="local-navigation.js" defer></script></body>'), encoding="utf-8")
    write_thumbnail_fallback(GALLERY)
    print(f"Built {len(layouts)} layouts.")
    try:
        import sys
        root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(root / "scripts"))
        from build_markdown_galleries import build_layouts_md
        build_layouts_md()
        from style_library_import import update_readme_and_skill_layouts
        update_readme_and_skill_layouts(len(layouts))
    except Exception as exc:
        print(f"Notice: build_layouts_md / doc sync skipped: {exc}")


if __name__ == "__main__":
    main()
