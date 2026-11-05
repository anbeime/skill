#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HandRaw 发布配图规划与生图引擎 (Release Illustration Planner)
================================================================
专为 HandRaw 新【画风 (Style)】或新【图型 (Layout)】发布文章定制的插图规划与批量生图工具。
核心哲学：
1. 本质是实测手绘 Skill 的画风与图型在真实商业场景中的表现边界；
2. 【画风发布】：商业主题推导完成后，必须为每个商业主题严密搭配契合的【图型 (Layout)】；
3. 【图型发布】：功能场景推导完成后，必须为每个场景搭配不同艺术流派的【画风 (Style)】；
4. 严格由【手绘 Skill (handdraw-style-prompter)】官方解析器驱动装配提示词；
5. 严格调用官方 36 色库（零色彩幻觉）、契合黄金画幅（16:9 / 3:4，严禁 2:3 截断）；
6. 批量调用统一生图客户端（VirtualBrowser b1 Plus CDP / HTTP API），原生落盘。
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HANDRAW_STYLE_DIR = Path(__file__).resolve().parents[3]
g_drive = Path("G" + ":") / "x-expert"
DEFAULT_X_EXPERT = g_drive if g_drive.exists() else Path(__file__).resolve().parents[3].parent / "x-expert"
X_EXPERT_DIR = Path(os.environ.get("X_EXPERT_DIR", str(DEFAULT_X_EXPERT)))
SKILL_DIR = HANDRAW_STYLE_DIR / "skills" / "handdraw-style-prompter"
SKILL_SCRIPTS_DIR = SKILL_DIR / "scripts"
STYLES_JSON_PATH = SKILL_DIR / "references" / "styles.json"
LAYOUTS_JSON_PATH = SKILL_DIR / "references" / "layouts.json"
COLORS_JSON_PATH = SKILL_DIR / "references" / "colors.json"
BUSINESS_DIR = HANDRAW_STYLE_DIR / "business"

MATRIX_PATH = Path(__file__).resolve().parent.parent / "references" / "domain_layout_matrix.json"

# 动态引入手绘 Skill 解析引擎
if str(SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

try:
    from layout_library import resolve_layout
    from prompt_style import resolve_style_entry, resolve_color, GRAPHIC_TEXT_SUFFIX
    from resolve_reference import resolve
except ImportError as e:
    raise ImportError(f"加载手绘 Skill 脚本失败: {e} (路径: {SKILL_SCRIPTS_DIR})")

# 引入项目生图客户端
default_fabu = HANDRAW_STYLE_DIR.parent / "handraw-fabu" / "style" / "scripts"
RELEASE_SCRIPTS_DIR = Path(os.environ.get("RELEASE_SCRIPTS_DIR", str(default_fabu)))
if str(RELEASE_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(RELEASE_SCRIPTS_DIR))

try:
    from image_client import generate_image
except ImportError:
    generate_image = None


# ======================================================================
# 1. 商业领域与排版图型匹配知识库加载
# ======================================================================
def load_domain_layout_matrix() -> List[Dict[str, Any]]:
    """加载预置商业领域与图型对应矩阵"""
    if MATRIX_PATH.is_file():
        try:
            data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
            return data.get("domains", [])
        except Exception as e:
            print(f"[!] 读取 domain_layout_matrix.json 异常: {e}")
    return []


def match_layout_for_domain(
    domain_text: str,
    used_layout_ids: Optional[List[str]] = None,
    layouts_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """为特定商业主题智能推荐契合的排版图型（避免相邻案例图型扎堆）"""
    used = set(used_layout_ids or [])
    matrix = load_domain_layout_matrix()
    clean_text = domain_text.lower()

    # 1. 优先在知识矩阵中按关键词匹配
    best_candidate = None
    for entry in matrix:
        kw_hits = sum(1 for kw in entry.get("keywords", []) if kw in clean_text)
        if kw_hits > 0:
            for rec in entry.get("recommended_layouts", []):
                lid = rec["layout_id"]
                if lid not in used:
                    return {
                        "layout_id": lid,
                        "layout_name": rec.get("name_zh", lid),
                        "rationale": rec.get("rationale", ""),
                        "ratio": rec.get("ratio", "16:9")
                    }
                elif best_candidate is None:
                    best_candidate = {
                        "layout_id": lid,
                        "layout_name": rec.get("name_zh", lid),
                        "rationale": rec.get("rationale", ""),
                        "ratio": rec.get("ratio", "16:9")
                    }

    if best_candidate and best_candidate["layout_id"] not in used:
        return best_candidate

    # 2. 启发式降级默认序列（覆盖不同版式类型）
    default_pool = [
        {"layout_id": "SC-021", "layout_name": "左右对开 1:1 双重视口", "rationale": "纪实视口与艺术风格对照，适合在地文旅与明信片", "ratio": "16:9"},
        {"layout_id": "SC-004", "layout_name": "图文分区卡", "rationale": "上图下文结构清晰，适合杯套包装与产品腰封", "ratio": "16:9"},
        {"layout_id": "SB-001", "layout_name": "经典电影宽银幕分镜", "rationale": "横幅光影张力强，契合唱片封套与舞台演出", "ratio": "16:9"},
        {"layout_id": "IG-007", "layout_name": "标签小图卡矩阵", "rationale": "多元素工整排布，契合文具印章与贴纸陈列", "ratio": "16:9"},
        {"layout_id": "SC-019", "layout_name": "手机端全屏故事卡", "rationale": "竖屏沉浸视觉，适合移动端开屏与情感故事流", "ratio": "3:4"},
        {"layout_id": "IG-018", "layout_name": "全景手绘导览地图", "rationale": "开阔视角与路线标记，适合景区与打卡折页", "ratio": "16:9"},
        {"layout_id": "SC-001", "layout_name": "经典拍立得白边卡", "rationale": "旅行留念回忆感，适合生活方式小物", "ratio": "3:4"}
    ]

    for item in default_pool:
        if item["layout_id"] not in used:
            return item

    return default_pool[0]


# ======================================================================
# 2. 画幅尺寸判定（严格遵守 16:9 与 3:4，杜绝 2:3 截断）
# ======================================================================
def determine_smart_size(
    layout: Optional[Dict[str, Any]] = None,
    style: Optional[Dict[str, Any]] = None,
    user_size: Optional[str] = None
) -> str:
    """智能决定生图尺寸：绝不无脑默认正方形，根据图型特征与分类匹配最契合的画幅规格。
    【铁律】竖版插图严禁使用 2:3 (1024x1536)，强制采用 3:4 (1086x1448)，彻底杜绝 X (Twitter) 文章截断。
    """
    if user_size and user_size != "default" and user_size != "1024x1024":
        if user_size == "1024x1536":
            return "1086x1448"  # 强制纠偏 2:3 到 3:4
        return user_size

    if layout:
        cat = (layout.get("category") or "").lower()
        name = (layout.get("name") or "").lower()
        name_en = (layout.get("name_en") or "").lower()
        layout_id = (layout.get("id") or "").upper()

        # 竖版插图 / 模块长图 / 社媒故事卡 -> 1086x1448 (3:4 黄金画幅 · 杜绝 X 截断)
        if layout_id in ["IG-038", "SC-019", "SC-001", "SC-015"] or any(k in name or k in name_en for k in ["竖版", "长图", "模块", "卡片", "海报", "card", "poster"]) or cat in ["social-card"]:
            return "1086x1448"

        # 横版全景 / 宽银幕分镜 / 地图导览 / 左右对开 -> 1792x1024 (16:9 横屏宽幅)
        return "1792x1024"

    # 默认横屏宽幅
    return "1792x1024"


# ======================================================================
# 3. 手绘 Skill 官方提示词解析器装配
# ======================================================================
def build_handdraw_prompt(
    layout_id: Optional[str] = None,
    style_id: Optional[str] = None,
    color_id: Optional[str] = None,
    theme: str = "",
    language: str = "zh",
    model: str = "gpt-image-2",
    size: Optional[str] = None,
    subject_category: str = "",
    concrete_visual: str = "",
    camera_perspective: str = ""
) -> str:
    """完全遵循 handdraw-style-prompter 官方规范装配提示词"""
    styles = json.loads(STYLES_JSON_PATH.read_text(encoding="utf-8"))
    layout = resolve_layout(layout_id) if layout_id else None
    selected, number = resolve_style_entry(style_id, styles) if style_id else (None, None)
    color_info = resolve_color(color_id) if color_id else None

    target_size = size or determine_smart_size(layout=layout, style=selected)
    if target_size == "1792x1024":
        aspect_zh = "画幅规格：1792x1024 横屏超宽画幅（16:9比例），开阔全景构图，严禁默认正方形裁切。"
        aspect_en = "Framing & Aspect Ratio: 1792x1024 widescreen landscape (16:9 ratio), wide panoramic composition, strictly avoid square 1:1 framing."
    elif target_size in ("1086x1448", "3:4", "1024x1536"):
        aspect_zh = "画幅规格：3:4 黄金竖版比例（分辨率 1086x1448），竖向插画构图，严禁 2:3 极端长图，严禁默认正方形裁切，确保 X (Twitter) 与微信公众号排版无截断。"
        aspect_en = "Framing & Aspect Ratio: 3:4 portrait ratio (1086x1448 resolution), vertical illustration framing, strictly avoid 2:3 or ultra-tall formats, strictly avoid square 1:1 framing to prevent clipping in articles."
    else:
        aspect_zh = f"画幅规格：{target_size} 原生指定画幅，严禁默认正方形裁切。"
        aspect_en = f"Framing & Aspect Ratio: {target_size} specified native format, strictly avoid square 1:1 framing."

    negative_constraint_zh = " 画面文案铁律：严禁在图内标题、标签、印章或说明文案中出现“新中式”、“东方”、“国潮”、“慢生活”等风格口号空话。画面风格由画风自然呈现，文案必须100%基于真实具体的业务内容或生活自愈细节。"
    negative_constraint_en = " Negative Constraint: Strictly forbid generic style slogans or buzzwords (e.g., 'New Chinese', 'Eastern', 'Guochao', 'Slow Life') in the in-image text/labels/stamps. Let the visual style convey aesthetics naturally; keep copy strictly grounded in realistic domain content."

    # 图型与画风协同装配模式 (Layout + Style)
    if layout:
        layout_name = layout["name"]
        layout_prompt = layout["prompts"][language]
        if language == "zh":
            parts = [
                f"图型：{layout['name']}。",
                f"主题：{theme}。",
                aspect_zh,
                f"图型排版规范：{layout_prompt}",
            ]
        else:
            parts = [
                f"Layout: {layout_name}.",
                f"Theme: {theme}.",
                aspect_en,
                f"Layout instructions: {layout_prompt}",
            ]

        if color_info:
            color_prompt = color_info["prompt_zh"] if language == "zh" else color_info["prompt_en"]
            parts.insert(1, color_prompt)

        if selected and number:
            decision = resolve(model, number)
            traits = decision.get("prompt_traits", "")
            if language == "zh":
                parts.append(f"风格名称：{selected['generation_name']}。参考作者/风格名称：{selected['reference']}。")
                if traits:
                    parts.append(f"核心风格特征：{traits}。")
            else:
                parts.append(f"Style name: {selected['generation_name']}. Reference author/style name: {selected['reference']}.")
                if traits:
                    parts.append(f"Core style traits: {traits}.")

        if concrete_visual:
            if language == "zh":
                entity_block = f"【画面核心实体与视觉场景（必须严格聚焦此主体，绝不雷同重复）】：{concrete_visual}。"
                if camera_perspective:
                    entity_block += f"【镜头景别与构图视角】：{camera_perspective}。"
                entity_block += f"【画面主体严格防模板化铁律】：严禁画面出现千篇一律的女性/女孩后背或侧面！严禁模板化单人站立仰望天空！本案例必须专注刻画指定的【{subject_category or '核心实体'}】，5个案例的主体元素彻底异构、跨度极大、绝对不得雷同！"
                parts.append(entity_block)
            else:
                entity_block = f" [Core Visual Subject & Scene (Mandatory Strict Execution)]: {concrete_visual}."
                if camera_perspective:
                    entity_block += f" [Camera Framing & Angle]: {camera_perspective}."
                entity_block += f" [Strict Anti-Stereotype Constraint]: Strictly forbid generic single-girl from behind or looking up at the sky! Focus entirely on the designated {subject_category or 'subject'}. Across all showcases, visual entities must be radically diverse and non-repeating!"
                parts.append(entity_block)
        parts.append(GRAPHIC_TEXT_SUFFIX)
        if language == "zh":
            parts.append(negative_constraint_zh)
        else:
            parts.append(negative_constraint_en)
        return "".join(parts) if language == "zh" else " ".join(parts)

    # 纯画风模式 (Style Only)
    if selected and number:
        decision = resolve(model, number)
        traits = decision.get("prompt_traits", "")
        if language == "zh":
            parts = [
                f"风格名称：{selected['generation_name']}。",
                f"参考作者/风格名称：{selected['reference']}。",
                f"主题：{theme}。",
                aspect_zh,
            ]
            if color_info:
                parts.insert(2, color_info["prompt_zh"])
            if traits:
                parts.append(f"核心风格特征：{traits}。")
            parts.append(GRAPHIC_TEXT_SUFFIX)
            parts.append(negative_constraint_zh)
            return "".join(parts)
        else:
            parts = [
                f"Style name: {selected['generation_name']}.",
                f"Reference author/style name: {selected['reference']}.",
                f"Theme: {theme}.",
                aspect_en,
            ]
            if color_info:
                parts.insert(2, color_info["prompt_en"])
            if traits:
                parts.append(f"Core style traits: {traits}.")
            parts.append(GRAPHIC_TEXT_SUFFIX)
            parts.append(negative_constraint_en)
            return " ".join(parts)

    raise ValueError("必须指定 layout_id 或 style_id 之一！")


# ======================================================================
# 4. 模式 A：画风发布配图规划 (Style Release Illustration Planning)
# ======================================================================


FG_025_TAXONOMIES = [
    {
        "category": "潮玩文创与手工消费 (Craft & DIY Merch)",
        "concrete_visual_zh": "手作工作台上整齐陈列的拼豆 DIY 套装物料：方形带钉塑料底板上正在拼搭的微缩像素地标建筑，旁边散落着鲜红、群青色与亮黄色的高光圆形塑料熔珠颗粒（带中心小圆孔），一把精密金属镊子、半透明耐热熨烫纸与一张 1:1 彩色像素点位图纸，微距手作质感，纯工艺静物",
        "concrete_visual_en": "A perler bead DIY craft kit neatly arranged on a clean crafting table: a square pegboard with a half-assembled pixel miniature landmark, scattered bright red, ultramarine blue and yellow cylindrical fuse beads with hollow center holes, precision metal tweezers, translucent ironing paper and a 1:1 color pixel pattern guide sheet, macro craft still life",
        "camera_zh": "45度桌面微距特写，工整手作材料排布，纯静物，绝无人物抢镜",
        "camera_en": "45-degree tabletop macro closeup, tidy craft knolling arrangement, strictly zero human presence",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    },
    {
        "category": "独立游戏与科技极客 (Indie Game & Geek Gear)",
        "concrete_visual_zh": "深灰胡桃木极客桌面上，一台半透明外壳的经典复古掌上游戏机，彩色液晶屏幕内清晰显示着纯正拼豆风格的 2D 像素关卡地图；游戏机旁摆放着几颗用真实拼豆熔融工艺定制的机械键盘个性键帽（分别印有像素爱心与像素小蘑菇），旁边盘绕着复古编织数据线",
        "concrete_visual_en": "On a dark walnut geek desk, a vintage handheld gaming console with a translucent shell, the color screen displaying a pure perler bead pixel 2D quest level map; next to it are custom mechanical keyboard artisan keycaps crafted from fused beads with pixel heart and pixel mushroom icons, coiled braided cable nearby",
        "camera_zh": "桌面中景特写视角，电子屏光感与实体拼豆塑料熔融肌理结合，纯极客数码静物，画面无人物",
        "camera_en": "Tabletop medium closeup view, screen luminescence combined with fused plastic bead texture, strictly zero human presence",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    },
    {
        "category": "新茶饮与快闪餐饮 (Beverage & Pop-up Merch)",
        "concrete_visual_zh": "极简咖啡外带纸杯特写，杯身套着一款极具创意的拼豆掌机造型加厚杯套，杯套正面用凹凸颗粒感的拼豆像素画排版着'满电咖啡'能量槽；旁边平放着一张硬卡纸像素集点打卡卡片，上面盖着几个红色小像素印章，以及一条带有拼豆亚克力吊坠的吸管套套件",
        "concrete_visual_en": "A modern takeaway coffee cup featuring a creative perler bead retro game console shaped cardboard sleeve with raised pixel battery energy gauge; lying beside is a thick cardstock pixel loyalty stamp card with red pixel stamps, and a paper straw accessory with a miniature pixel acrylic charm",
        "camera_zh": "干净通透的快闪餐饮特写镜头，强调杯套塑料熔珠凹凸质感与平面图文一体化设计，纯餐饮文创物料，无人物",
        "camera_en": "Clean pop-up cafe closeup shot, emphasizing the tactile fuse bead texture and packaging graphic integration, strictly zero human presence",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    },
    {
        "category": "文房平铺与手账工艺 (Stationery Flatlay Knolling)",
        "concrete_visual_zh": "垂直 90 度自上而下俯视平铺陈列 (Flatlay)：一本展开的高级米灰色网格手账本，内页绘制着精美的拼豆像素小动物速写图谱；周围工整罗列着两枚长条形拼豆熔珠书签、一支黄铜旋转签字笔、一盒分色分类的马卡龙色塑料小熔珠亚克力收纳盒与一把木质像素刻度尺，留白充足透气",
        "concrete_visual_en": "Top-down 90-degree flatlay knolling: an open premium warm grey grid notebook showing detailed perler bead animal sketches; neatly arranged around it are two fused bead bookmarks, a brass twist pen, a clear acrylic storage box of sorted pastel beads, and a wooden pixel ruler, with generous clean breathing space",
        "camera_zh": "垂直90度俯视平铺图鉴构图，工整间距透气留白，纯手账文具陈列，画面无人物",
        "camera_en": "Top-down 90-degree flatlay knolling composition, precise spacing and breathing margin, pure stationery display, zero human presence",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    },
    {
        "category": "城市文旅与复古街区 (City Walk & Retro Map)",
        "concrete_visual_zh": "一张精美装裱的城市街区漫步像素探险全景图卡：整座老街区全部由工整的拼豆塑料熔珠颗粒拼接而成，清晰可见红砖老火车站钟楼、坡道上的墨绿色有轨电车、街角暖光面包房与树木水系，所有道路、建筑与地标均呈现清晰硬朗的阶梯像素网格，兼具复古 RPG 游戏地图的奇趣与现实街区风貌",
        "concrete_visual_en": "A framed city walk pixel exploration map: the entire historic urban district is intricately composed of perler fuse beads, showing a red-brick clock tower train station, a dark green tram on a sloped street, a corner warm bakery, and stylized trees and canals, with all roads and buildings formed by crisp stepped pixel bead grids, blending retro RPG map charm with urban exploration",
        "camera_zh": "微倾斜45度等距轴测全景俯瞰，整幅画面如同一张精细的实体拼豆微缩沙盘，纯街区地貌空镜，无人物特写",
        "camera_en": "45-degree isometric bird's eye view, resembling an intricate miniature fused bead city diorama, pure urban landscape, zero human closeup",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    }
]

FIVE_SUBJECT_TAXONOMIES = [
    {
        "category": "建筑与交通实景 (Architecture & Transit)",
        "concrete_visual_zh": "复古双节有轨电车穿行在临海铁桥与坡道街巷间，头顶巨大积雨云与电线纵横交错，夕阳逆光拉出长长轨道反光与微湿沥青路面，纯实景电车与沿海建筑全景，绝无人物抢镜",
        "concrete_visual_en": "A vintage double-section electric tram crossing an ocean-side railway bridge between sloped streets, towering cumulonimbus clouds and crisscrossing power cables overhead, sunset casting long glowing rail reflections on wet asphalt, pure realistic architectural and transit panorama without human characters",
        "camera_zh": "开阔长焦街景全景，景深压缩，纯建筑与机具空镜，无人物",
        "camera_en": "Open telephoto streetscape panorama with compressed depth of field, pure architectural transit still, zero human presence",
        "preferred_ratio": "16:9",
        "size": "1792x1024"
    },
    {
        "category": "餐饮流体与微距静物 (Food, Beverage & Liquid Still Life)",
        "concrete_visual_zh": "原木咖啡吧台上一杯盛满透明气泡冰块与新鲜橙片的冰萃咖啡，杯壁凝结一层晶莹冰凉的水珠，黄昏夕阳（柿子橙色）穿透玻璃杯在桌面投下梦幻焦散光斑(Caustics)，旁边放着咖啡量勺与麻布杯垫，纯静物微距光影",
        "concrete_visual_en": "On a warm wooden cafe bar, an iced citrus cold brew coffee in a crystal tall glass filled with sparkling ice cubes and fresh orange slices, condensation droplets on glass wall, sunset light casting dreamlike caustic reflections across tabletop, accompanied by coffee scoop and linen coaster, pure macro still life lighting",
        "camera_zh": "45度桌面静物微距特写，光线穿透液体与玻璃杯，纯静物，画面100%无人物",
        "camera_en": "45-degree tabletop still life macro closeup, light refraction through liquid and glass, strictly zero human presence",
        "preferred_ratio": "16:9",
        "size": "1792x1024"
    },
    {
        "category": "室内器物与声学空间 (Interior & Acoustic Objects)",
        "concrete_visual_zh": "电影宽银幕分镜：第一格木壳复古黑胶唱机旋转播放黑色唱盘特写；第二格百叶窗斜射暖灰粉色夕阳光束照在木吉他与乐谱架上；第三格窗台上摆放的专业监听耳机，窗外远处是暮色中的城市天际线，纯室内乐器器材空间",
        "concrete_visual_en": "Cinematic widescreen multi-panel: Panel 1 closeup of wooden vintage turntable playing black vinyl record; Panel 2 warm sunset light streaming through window blinds onto an acoustic guitar and sheet music stand; Panel 3 studio monitor headphones resting on windowsill overlooking twilight city skyline, pure indoor musical gear atmosphere",
        "camera_zh": "电影宽银幕室内器物中景分镜，乐器特写与逆光光束，纯静物器物，画面无人物",
        "camera_en": "Cinematic widescreen indoor still-life panels, musical instrument closeups and backlit rays, strictly zero human presence",
        "preferred_ratio": "16:9",
        "size": "1792x1024"
    },
    {
        "category": "文房平铺与手账工艺 (Stationery Flatlay Knolling)",
        "concrete_visual_zh": "自上而下的桌面俯视平铺陈列（Flatlay/Knolling）：一本展开的深灰蓝色棉麻手账本（上面绘有精致星轨速写），旁边工整罗列着复古黄铜旋转钢笔、半透明硫酸纸信封、带有火漆印章的手写信笺、一小卷红色编织结绳书签、古董放大镜，四周大面积干净象牙白留白",
        "concrete_visual_en": "Direct top-down 90-degree knolling flatlay: an open deep slate-blue linen journal with delicate star-trail sketches, neatly surrounded by a vintage brass fountain pen, translucent vellum envelope, wax-sealed handwritten letter, a small coil of braided red cord bookmark, and antique magnifying glass, generous clean ivory negative space",
        "camera_zh": "垂直90度俯视平铺图鉴构图，工整间距透气留白，纯物料陈列，画面无人物",
        "camera_en": "Vertical 90-degree top-down flatlay catalog composition, tidy breathing margins, pure stationery objects, strictly zero human presence",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    },
    {
        "category": "宏大天象与奇幻地景 (Celestial Landscape & Worldview)",
        "concrete_visual_zh": "黄昏之时的巍峨群山与无垠深蓝天穹，一颗璀璨耀眼的分岔双子彗星拖着朱砂红与金色粒子光尾划过夜空，远方是巨大的远古陨石环形湖，湖面平静如镜完整倒映出漫天繁星与彗星光斑，群鸟在山隘间展翅翱翔，空灵神秘的宏大史诗感自然全景",
        "concrete_visual_en": "Twilight over majestic mountain ranges and infinite deep indigo sky, a brilliant bifurcated twin comet trailing vermilion and golden particle tails across space, reflecting on a vast ancient meteor crater mirror lake beneath star trails, birds soaring between mountain passes, an ethereal epic landscape panorama",
        "camera_zh": "超广角宏大远景，纯自然与天文空镜，宏伟壮阔史诗感，绝无单一人像特写",
        "camera_en": "Ultra-wide epic panoramic landscape, pure celestial nature and sky, monumental grandeur, strictly zero single-character portrait",
        "preferred_ratio": "3:4",
        "size": "1086x1448"
    }
]

DEFAULT_STYLE_SCENES = [
    {
        "domain": "城市文旅与在地文创",
        "materials": "城市限定明信片、景点联名胶片、打卡地图折页",
        "reason": "将本地真实地标以风格光影美学重构，游客获得电影感纪念品，本地人获得情感认同。"
    },
    {
        "domain": "青春向饮品/咖啡连锁",
        "materials": "外带杯套、季节限定杯身、门店窗贴、周边贴纸",
        "reason": "杯套是高频触达的情绪载体，与版式结合制造收集欲与社交晒图动机。"
    },
    {
        "domain": "独立音乐/演出与唱片",
        "materials": "专辑封面、演出海报、黑胶内页、票根设计",
        "reason": "光影渐变与逆光人物天然契合音乐的情绪属性，提升实体唱片的收藏溢价。"
    },
    {
        "domain": "情感向文具与手账品牌",
        "materials": "手账胶带、便签本、信纸信封、书签",
        "reason": "写信与等待的叙事母题与文具品类高度同构，强化使用仪式感。"
    },
    {
        "domain": "游戏/APP 情感化运营",
        "materials": "开屏插画、活动落地页主视觉、限定皮肤、加载页",
        "reason": "用一张开屏图完成情绪定调，提升留存与分享率。"
    }
]

def plan_illustrations_for_style(
    style_identifier: str,
    count: int = 5,
    user_size: Optional[str] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """为画风规划 4~5 个跨商业领域、且每个领域均搭配契合排版图型的案例"""
    styles = json.loads(STYLES_JSON_PATH.read_text(encoding="utf-8"))
    layouts = json.loads(LAYOUTS_JSON_PATH.read_text(encoding="utf-8"))
    selected, number = resolve_style_entry(style_identifier, styles)

    style_num = number
    style_zh = selected.get("reference", "")
    style_en = selected.get("generation_name", "")

    # 1. 尝试从 business/{style_identifier}.md 或 business/{number}.md 解析真实商业场景与推荐色彩
    biz_file = BUSINESS_DIR / f"{style_identifier}.md"
    if not biz_file.is_file():
        biz_file = BUSINESS_DIR / f"{style_num}.md"
    extracted_scenes: List[Dict[str, str]] = []
    extracted_colors: List[str] = []
    if biz_file.is_file():
        try:
            content = biz_file.read_text(encoding="utf-8")
            table_matches = re.findall(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|", content)
            for m in table_matches:
                domain_title = m[0].strip()
                materials = m[1].strip()
                reason = m[2].strip()
                if "商业场景" in domain_title or "---" in domain_title:
                    continue
                extracted_scenes.append({
                    "domain": domain_title,
                    "materials": materials,
                    "reason": reason
                })
            # 提取官方推荐主题色 (零幻觉色彩)
            color_matches = re.findall(r"`(C-\d{2})`", content)
            if color_matches:
                extracted_colors = list(dict.fromkeys(color_matches))
        except Exception as e:
            print(f"[!] 读取商业指南异常: {e}")

    # 若未提取到，使用标准场景备选
    active_scenes = extracted_scenes if len(extracted_scenes) >= count else DEFAULT_STYLE_SCENES

    cases: List[Dict[str, Any]] = []
    used_layout_ids = []

    for i in range(min(count, len(active_scenes))):
        case_idx = i + 1
        sc = active_scenes[i]
        domain = sc["domain"]
        materials = sc.get("materials", "")
        reason = sc.get("reason", "")
        theme = f"{materials}，具体展现：{reason[:60]}" if materials and reason else f"{domain}商业物料设计"

        # 【核心特性】：适合的商业主题出来后，考虑搭配的图型！
        matched_layout_info = match_layout_for_domain(
            domain_text=f"{domain} {materials} {reason}",
            used_layout_ids=used_layout_ids,
            layouts_data=layouts
        )
        matched_layout_id = matched_layout_info["layout_id"]
        matched_layout_name = matched_layout_info["layout_name"]
        used_layout_ids.append(matched_layout_id)

        # 匹配主题色 (优先从商业指南提取，其次官方轮转)
        if extracted_colors:
            color_spec = extracted_colors[i % len(extracted_colors)]
        else:
            default_color_cycle = ["C-05", "C-26", "C-22", "C-31", "C-15"]
            color_spec = default_color_cycle[i % len(default_color_cycle)]

        color_info = resolve_color(color_spec)
        color_label = f"{color_spec} · {color_info['name_zh']} ({color_info['name_en']})"

        # 绑定五维实体异构与零雷同规范
        if style_num == "FG-025":
            sub = FG_025_TAXONOMIES[i % len(FG_025_TAXONOMIES)]
        else:
            sub = FIVE_SUBJECT_TAXONOMIES[i % len(FIVE_SUBJECT_TAXONOMIES)]
        subj_category = sub["category"]
        concrete_zh = sub["concrete_visual_zh"]
        concrete_en = sub["concrete_visual_en"]
        camera_zh = sub["camera_zh"]
        camera_en = sub["camera_en"]

        # 智能判定尺寸 (支持实体维度专属推荐尺寸，杜绝2:3)
        if user_size and user_size != "default":
            target_size = determine_smart_size(layout=resolve_layout(matched_layout_id), style=selected, user_size=user_size)
        else:
            target_size = sub.get("size") or determine_smart_size(layout=resolve_layout(matched_layout_id), style=selected)

        # 【核心特性】：用手绘 Skill 原生解析器装配出图提示词 (同时融入 Style + Layout + Color + Theme + 实体异构 + 防模板化铁律)
        prompt_zh = build_handdraw_prompt(
            layout_id=matched_layout_id,
            style_id=style_num,
            color_id=color_spec,
            theme=theme,
            language="zh",
            size=target_size,
            subject_category=subj_category,
            concrete_visual=concrete_zh,
            camera_perspective=camera_zh
        )
        prompt_en = build_handdraw_prompt(
            layout_id=matched_layout_id,
            style_id=style_num,
            color_id=color_spec,
            theme=theme,
            language="en",
            size=target_size,
            subject_category=subj_category,
            concrete_visual=concrete_en,
            camera_perspective=camera_en
        )

        cases.append({
            "index": case_idx,
            "filename": f"showcase_{case_idx}.png",
            "domain": domain,
            "theme": theme,
            "subject_category": subj_category,
            "concrete_visual": concrete_zh,
            "camera_perspective": camera_zh,
            "matched_layout": f"{matched_layout_id} {matched_layout_name}",
            "matched_layout_id": matched_layout_id,
            "color_palette": color_label,
            "size": target_size,
            "prompt_zh": prompt_zh,
            "prompt_en": prompt_en,
            "prompt": prompt_zh,
            "description": f"案例 {case_idx}（{domain} · {subj_category}）：运用官方画风【{style_zh} ({style_num})】，搭配专属排版图型【{matched_layout_id} {matched_layout_name}】，官方配色为【{color_label}】，画幅设定为【{target_size}】。聚焦实体：{concrete_zh[:32]}...，彻底杜绝模板化背影人物，实测其在商业物料中的跨维度表现。"
        })

    meta = {
        "type": "style",
        "identifier": style_num,
        "name_zh": f"{style_zh} / {style_en}",
        "name_en": style_en,
        "total_cases": len(cases),
        "smart_size": cases[0]["size"] if cases else "1792x1024"
    }
    return meta, cases


# ======================================================================
# 5. 模式 B：图型发布配图规划 (Layout Release Illustration Planning)
# ======================================================================
def plan_illustrations_for_layout(
    layout_identifier: str,
    count: int = 5,
    user_size: Optional[str] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """为图型规划 4~5 个跨功能场景、且每个场景均搭配不同流派画风的案例"""
    styles = json.loads(STYLES_JSON_PATH.read_text(encoding="utf-8"))
    layouts = json.loads(LAYOUTS_JSON_PATH.read_text(encoding="utf-8"))
    colors = json.loads(COLORS_JSON_PATH.read_text(encoding="utf-8"))

    layout = resolve_layout(layout_identifier)
    layout_id = layout["id"]
    layout_name = layout["name"]
    layout_en = layout.get("name_en") or layout_name

    target_size = determine_smart_size(layout=layout, user_size=user_size)

    # 跨流派画风推荐序列（确保清晰度优先与多艺术流派兼备）
    cross_genre_style_candidates = [
        {"code": "FA-029", "genre": "清晰线条插画 (Chris Ware)", "color": "C-01 + C-15", "domain": "立体交通接驳与导览路线图"},
        {"code": "FB-018", "genre": "水彩寻宝找物绘本风", "color": "C-15 + C-05", "domain": "特色美食街区与餐饮点示意图"},
        {"code": "FD-012", "genre": "清透日系商业手绘风", "color": "C-29 + C-01", "domain": "便民公共服务与卫生间设施地图"},
        {"code": "FE-049", "genre": "现代新国潮工笔重彩", "color": "C-26 + C-31", "domain": "特色文创街区与手作商铺索引"},
        {"code": "FG-024", "genre": "唯美动漫光影天空美学", "color": "C-05 + C-26", "domain": "亲子探索打卡与露营野餐区"}
    ]

    cases: List[Dict[str, Any]] = []
    for i in range(min(count, len(cross_genre_style_candidates))):
        case_idx = i + 1
        st = cross_genre_style_candidates[i]
        style_code = st["code"]
        color_spec = st["color"]
        domain = st["domain"]
        theme = f"{domain}，包含清晰路线、地标、图例与功能编号标注"

        s_obj, _ = resolve_style_entry(style_code, styles)
        style_ref = s_obj.get("reference", style_code)
        style_gen = s_obj.get("generation_name", style_code)
        paired_style_label = f"{style_ref} · {style_gen} ({style_code})"

        color_info = resolve_color(color_spec)
        color_label = f"{color_spec} · {color_info['name_zh']} ({color_info['name_en']})"

        prompt_zh = build_handdraw_prompt(
            layout_id=layout_id,
            style_id=style_code,
            color_id=color_spec,
            theme=theme,
            language="zh",
            size=target_size
        )
        prompt_en = build_handdraw_prompt(
            layout_id=layout_id,
            style_id=style_code,
            color_id=color_spec,
            theme=theme,
            language="en",
            size=target_size
        )

        cases.append({
            "index": case_idx,
            "filename": f"showcase_{case_idx}.png",
            "paired_style": paired_style_label,
            "style_code": style_code,
            "domain": domain,
            "theme": theme,
            "color_palette": color_label,
            "size": target_size,
            "prompt_zh": prompt_zh,
            "prompt_en": prompt_en,
            "prompt": prompt_zh,
            "description": f"案例 {case_idx}（{domain}）：将版式图型【{layout_id} {layout_name}】与官方画风【{style_ref} ({style_code})】跨界混搭，官方配色为【{color_label}】，尺寸指定为【{target_size}】，实测其在“{domain}”场景中的图文融合与叙事张力。"
        })

    meta = {
        "type": "layout",
        "identifier": layout_id,
        "name_zh": layout_name,
        "name_en": layout_en,
        "category": layout.get("category", "infographic"),
        "total_cases": len(cases),
        "smart_size": target_size,
    }
    return meta, cases


# ======================================================================
# 6. 生图执行与 Manifest 导出
# ======================================================================
def execute_batch_case_generation(
    target_dir: Path,
    cases: List[Dict[str, Any]],
    meta: Dict[str, Any],
    dry_run: bool = False,
    size: Optional[str] = None,
    quality: str = "hd",
    delay_sec: int = 5,
    force: bool = False
) -> Path:
    """批量调用生图接口生成案例图片并写出规范 manifest 文件"""
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_json_path = target_dir / "cases_manifest.json"
    manifest_md_path = target_dir / "cases_manifest.md"

    print("\n" + "=" * 60)
    print(f"🚀 开始执行实测配图任务: {meta.get('identifier')} · {meta.get('name_zh')}")
    print(f"📁 目标目录: {target_dir}")
    print(f"📊 规划案例数: {len(cases)} | 预设画幅: {meta.get('smart_size')} | 模式: {'预演 (DRY-RUN)' if dry_run else '真实生图'} | 强制重生: {force}")
    print("=" * 60)

    for case in cases:
        idx = case["index"]
        fn = case["filename"]
        out_file = target_dir / fn
        dom = case["domain"]
        cspec = case["color_palette"]
        prompt = case["prompt_zh"]
        csize = case.get("size") or meta.get("smart_size") or "1792x1024"

        print(f"\n[{idx}/{len(cases)}] 案例 {idx} · {dom}")
        print(f"   图型/画风搭配: {case.get('matched_layout') or case.get('paired_style') or '官方原生'}")
        print(f"   官方配色: {cspec} | 尺寸规格: {csize}")
        print(f"   文件目标: {out_file.name}")

        if dry_run:
            print(f"   [DRY-RUN 提示词预览]: {prompt[:120]}...")
            continue

        if not force and out_file.is_file() and out_file.stat().st_size > 10000:
            print(f"   ⚡ 文件已存在且完整 ({out_file.stat().st_size / (1024*1024):.2f} MB)，跳过生图。")
            continue

        if generate_image is None:
            raise RuntimeError("生图模块 image_client 未找到，无法执行生成！")

        print(f"   🎨 正在发起生图请求 (尺寸: {csize})...")
        try:
            generate_image(
                prompt=prompt,
                output_path=out_file,
                size=csize,
                quality=quality,
                aspect_ratio="raw"
            )
            print(f"   ✓ 案例 {idx} 生成成功: {out_file.name}")
        except Exception as e:
            print(f"   ❌ 案例 {idx} 生图失败: {e}", file=sys.stderr)
            raise

        if idx < len(cases) and delay_sec > 0:
            print(f"   ⏳ 冷却休眠 {delay_sec} 秒...")
            time.sleep(delay_sec)

    # 导出 cases_manifest.json
    manifest_data = {
        "metadata": meta,
        "is_dry_run": dry_run,
        "engine": "release-illustration-planner",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": cases
    }
    manifest_json_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 导出 cases_manifest.md (供专栏文章一键嵌入)
    md_lines = [
        f"# {meta.get('identifier')} · 实测案例素材清单 (Release Illustration Manifest)",
        f"",
        f"- **目标对象**：`{meta.get('identifier')}` {meta.get('name_zh')}",
        f"- **类型**：{'风格 (Style)' if meta.get('type') == 'style' else '图型 (Layout)'}",
        f"- **总计案例**：{len(cases)} 组",
        f"- **生成模式**：{'DRY-RUN 预演' if dry_run else '已落盘真实高清原图'}",
        f"- **更新时间**：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"---",
        f"",
        f"## 案例一览与文章嵌入代码",
        f""
    ]

    for c in cases:
        idx = c["index"]
        fn = c["filename"]
        dom = c["domain"]
        cp = c["color_palette"]
        ml = c.get("matched_layout") or c.get("paired_style") or "官方原生"
        sz = c.get("size")
        pzh = c["prompt_zh"]

        md_lines.extend([
            f"### 案例 {idx}：{dom}",
            f"![]({fn})",
            f"- **商业场景**：{dom}",
            f"- **搭配图型/风格**：`{ml}`",
            f"- **官方配色**：`{cp}`",
            f"- **画幅规格**：`{sz}`",
            f"- **手绘 Skill 官方提示词**：",
            f"  ```text",
            f"  {pzh}",
            f"  ```",
            f""
        ])

    manifest_md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n✅ 案例清单已保存: {manifest_json_path}")
    print(f"✅ 专栏嵌入文档已保存: {manifest_md_path}")
    return manifest_json_path


# ======================================================================
# 7. CLI 入口
# ======================================================================
def main():
    parser = argparse.ArgumentParser(description="HandRaw 风格/图型发布配图规划与生图器 (Release Illustration Planner)")
    g_target = parser.add_mutually_exclusive_group(required=True)
    g_target.add_argument("--style", help="指定画风编号 (如 FG-024 / 367)")
    g_target.add_argument("--layout", help="指定图型编号 (如 SC-021 / IG-036)")

    parser.add_argument("-t", "--article-title", help="文章标题 (用于定位输出目录 x-expert/now/images\\<title>)")
    parser.add_argument("-o", "--output-dir", help="显式指定输出目录")
    parser.add_argument("--count", type=int, default=5, choices=[4, 5], help="生成案例数 (4 或 5 张，默认 5)")
    parser.add_argument("--size", help="显式覆盖画幅规格 (默认智能推导 1792x1024 或 1086x1448)")
    parser.add_argument("--quality", default="hd", choices=["hd", "high", "standard"], help="画质 (默认 hd)")
    parser.add_argument("--delay", type=int, default=3, help="批量调用休眠秒数 (默认 3 秒)")
    parser.add_argument("--dry-run", action="store_true", help="仅规划方案并输出提示词，不触发真实生图")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有配图，即使文件已存在")

    args = parser.parse_args()

    if args.style:
        meta, cases = plan_illustrations_for_style(args.style, count=args.count, user_size=args.size)
    else:
        meta, cases = plan_illustrations_for_layout(args.layout, count=args.count, user_size=args.size)

    if args.output_dir:
        target_dir = Path(args.output_dir).resolve()
    elif args.article_title:
        clean_title = re.sub(r'[\\/*?:"<>|]', '_', args.article_title.strip())
        target_dir = X_EXPERT_DIR / "now" / "images" / clean_title
    else:
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', f"{meta['identifier']}-{meta['name_zh']}")
        target_dir = X_EXPERT_DIR / "now" / "images" / clean_name

    execute_batch_case_generation(
        target_dir=target_dir,
        cases=cases,
        meta=meta,
        dry_run=args.dry_run,
        size=args.size,
        quality=args.quality,
        delay_sec=args.delay,
        force=args.force
    )

if __name__ == "__main__":
    main()
