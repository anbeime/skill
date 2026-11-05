#!/usr/bin/env python3
"""
逐镜头构图/光/运动量化（配 reference/composition-and-light.md §6 与 agent-qc-rules.md）。
用法：
  python3 scripts/frame_metrics.py [--frames fin_frames] [--storyboard 分镜表.md] [--shots SC11:1627-1806,SC12:1852-1965] [--step 4] [--out qc/frame_metrics_vN.md]
默认从 分镜表.md 解析 `| SCxx … | a–b |` 行得到镜头区间；帧目录默认 fin_frames/f_%04d.jpg。
每镜头输出：主体尺度（最大物体高度，宽物体按 min(w,4h)/2.5 折算；一行大字按整行计）中位数/最小值、空场最长连续帧数（无 ≥110 主体且无大面积光活动）、柔光面积（主角区 / 全区）中位数、紫色碎片数中位数、最长静止帧数、标记。
依赖：numpy pillow scipy。亮度统计用 int32。
"""
import argparse, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument('--frames', default='fin_frames')
ap.add_argument('--storyboard', default='分镜表.md')
ap.add_argument('--shots', default='')
ap.add_argument('--step', type=int, default=4)
ap.add_argument('--out', default='')
ap.add_argument('--rail-top', type=int, default=100, help='内容区上界（有流程轨的镜头可传 175）')
ap.add_argument('--bg', default='auto', help="幕底方案 stars|dots|auto（auto 读 src/config.ts 的 bg）。dots 时按 DotFieldBg 的网格坐标把点阵抠掉再统计，否则波前亮点会被数成背景碎屑")
a = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cfg_bg():
    try:
        m = re.search(r"bg:\s*'(stars|dots)'", open(f'{ROOT}/src/config.ts', encoding='utf-8').read())
        return m.group(1) if m else 'dots'
    except OSError:
        return 'dots'
BG = cfg_bg() if a.bg == 'auto' else a.bg

def dot_mask(W=1280, H=720, r=5):
    """点阵波幕底的屏幕坐标掩膜（与 src/common/DotFieldBg.tsx 同一组常量：设计坐标 960×540、步距 36、起点 (24,18)、等比放大）。
    点半径实际 2–2.7px，JPEG 再糊 1px，掩 5px 足够；点距 48px，掩掉的面积 <4%，对真实主体的统计影响可忽略。"""
    m = np.zeros((H, W), bool)
    if BG != 'dots':
        return m
    sc = max(W / 960, H / 540); ox = (W - 960 * sc) / 2; oy = (H - 540 * sc) / 2
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disc = (xx * xx + yy * yy) <= r * r
    for y in range(18, 540, 36):
        for x in range(24, 960, 36):
            cx = int(round(ox + x * sc)); cy = int(round(oy + y * sc))
            y0, y1 = max(0, cy - r), min(H, cy + r + 1); x0, x1 = max(0, cx - r), min(W, cx + r + 1)
            if y1 <= y0 or x1 <= x0: continue
            m[y0:y1, x0:x1] |= disc[(y0 - cy + r):(y1 - cy + r), (x0 - cx + r):(x1 - cx + r)]
    return m
DOT_MASK = dot_mask()
# 点阵底色 #0b0c11 本身带一点蓝（sat≈.35、lum≈12），会整屏落进「柔光」判据（sat>.25 且 10<lum<110）→ 空场检测被屏蔽、主角区柔光虚高；
# dots 模式把柔光亮度下限抬到 22（实测底色+噪点 ≤18；紫柔光在内容区的亮度多在 25–110，基本不受影响）。
SOFT_LO = 22 if BG == 'dots' else 10

def parse_shots():
    if a.shots:
        out = []
        for tok in a.shots.split(','):
            sid, rng = tok.split(':'); lo, hi = re.split(r'[–-]', rng)
            out.append((sid, int(lo), int(hi)))
        return out
    out = []
    for line in open(a.storyboard, encoding='utf-8'):
        m = re.match(r'^\|\s*(SC\d+)[^|]*\|\s*(\d+)\s*[–-]\s*(\d+)\s*\|', line)
        if m:
            out.append((m.group(1), int(m.group(2)), int(m.group(3))))
    # 去重（分镜表后面的白名单/衔接表也以 SC 开头但没有帧区间列，正则已排除）
    seen = {}
    for s in out:
        seen.setdefault(s[0], s)
    return list(seen.values())

def frame_path(i):
    p = os.path.join(a.frames, f'f_{i:04d}.jpg')
    return p if os.path.exists(p) else os.path.join(a.frames, f'frame_{i:04d}.jpg')

Z = slice(a.rail_top, 621)

def analyze(i):
    im = Image.open(frame_path(i)).convert('RGB'); arr = np.asarray(im).astype(np.int32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    lum = (r * 299 + g * 587 + b * 114) // 1000
    mx = arr.max(2); mn = arr.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    bright = (lum[Z] > 120) & ~DOT_MASK[Z]   # 点阵波幕底（BG='dots'）的点先抠掉，不然波前 40–60 个亮点会被数成碎屑
    # 横向 41 / 纵向 13 的结构元：把一行大字的字与字（含千分位逗号、字距 ≤40px）并成一个物体，但不会把间距 ≥50 的胶囊行并起来
    obj = ndi.binary_dilation(bright, structure=np.ones((13, 41), bool))
    lab, n = ndi.label(obj)
    hero_h = 0; hero_box = None; small = 0
    if n:
        ink = ndi.sum(bright, lab, index=np.arange(1, n + 1))  # 每个物体的实际亮像素数（星点只有 2–16px，排除）
        for k, s in enumerate(ndi.find_objects(lab)):
            if s is None or ink[k] < 30: continue
            h = s[0].stop - s[0].start; w = s[1].stop - s[1].start
            if h < 60 and w < 60: small += 1
            # 主体尺度：高度，或"宽度折算"——宽而不细的物体（一行大字、宽卡）按 min(w, 4h)/2.5 计，细线（h 很小）几乎不加分
            size = max(h, min(w, 4 * h) / 2.5)
            if size > hero_h: hero_h = size; hero_box = s
    soft = (sat[Z] > 0.25) & (lum[Z] > SOFT_LO) & (lum[Z] < 110) & ~DOT_MASK[Z]
    glow_total = int(soft.sum())  # 全内容区柔光面积：扫光 / 光线 / 光环阶段很大 → 这类帧不算空场
    glow_hero = 0
    if hero_box is not None:
        y0 = max(0, hero_box[0].start - 30); y1 = hero_box[0].stop + 30
        x0 = max(0, hero_box[1].start - 30); x1 = hero_box[1].stop + 30
        sub = soft[y0:y1, x0:x1]
        if sub.any():
            lab2, n2 = ndi.label(sub)
            glow_hero = int(np.bincount(lab2.ravel())[1:].max()) if n2 else 0
    # 紫色碎片：实心紫（排除柔光雾与虚线波纹），不膨胀，≥80px 才算一块
    purple = (b[Z] > r[Z]) & (r[Z] > g[Z]) & (sat[Z] > 0.45) & (lum[Z] > 45)
    lab3, n3 = ndi.label(ndi.binary_dilation(purple, structure=np.ones((7, 25), bool)))  # 把一行字的逐字硬投影并成一块
    npurple = int((np.bincount(lab3.ravel())[1:] >= 80).sum()) if n3 else 0
    return hero_h, glow_hero, npurple, small, int(bright.sum()), glow_total

def diff_series(lo, hi):
    prev = None; out = []
    for i in range(lo, hi + 1):
        im = Image.open(frame_path(i)); im.draft('L', (320, 180)); l = np.asarray(im.convert('L').resize((320, 180))).astype(np.int32)
        out.append(0 if prev is None else float(np.abs(l - prev).mean())); prev = l
    return out

shots = parse_shots()
if not shots:
    sys.exit('没有解析到镜头区间：检查 --storyboard 或用 --shots')
lines = ['| 镜头 | 帧 | 主体尺度 中位/最小 px | 空场最长连续帧 | 柔光 主角区/全区 中位 px² | 紫色碎片 中位 | 最长静止帧 | 标记 |', '|---|---|---|---|---|---|---|---|']
flags_total = {'高': 0, '中': 0, '低': 0}
for sid, lo, hi in shots:
    hh = []; gl = []; pp = []; sm = []; gt = []
    for i in range(lo, hi + 1, a.step):
        h, g, p, s, br, g_all = analyze(i)
        if br < 200: h = 0
        hh.append(h); gl.append(g); pp.append(p); sm.append(s); gt.append(g_all)
    hh = np.array(hh); gt = np.array(gt); run = 0; best = 0
    for h, g_all in zip(hh, gt):
        # 空场 = 没有 ≥110 的主体 **且** 没有大面积光活动（扫光 / 舞台光线 / 光环 的柔光 ≥10000px² 不算空；一根发光游标只有几千）
        run = run + 1 if (h < 110 and g_all < 10000) else 0; best = max(best, run)
    low_run = best * a.step
    d = diff_series(lo, hi); srun = 0; sbest = 0
    for v in d[1:]:
        srun = srun + 1 if v < 0.15 else 0; sbest = max(sbest, srun)
    flags = []
    # 主体尺度中位数只统计"非光效帧且有内容"的帧：高光时刻的扫光 / 光线阶段不算主角缺席
    solid = hh[(hh > 0) & ~((hh < 110) & (gt >= 10000))]
    med_h = float(np.median(solid)) if len(solid) else 0.0; min_h = int(hh.min())
    if low_run > 45:
        low_vals = hh[(hh < 110) & (hh > 0)]
        flags.append('高:空场(主体<80px>45帧)' if len(low_vals) and np.median(low_vals) < 80 else '中:空场(主体<110px>45帧)')
    elif med_h < 170:
        flags.append('低:主角<170px')
    if float(np.median(gl)) < 800: flags.append('低:主角无光')
    if float(np.median(pp)) >= 8: flags.append('低:紫色碎片≥8')
    if float(np.median(sm)) >= 10: flags.append('中:背景碎屑≥10')
    if sbest > 90: flags.append(f'中:静止{sbest}帧(>3s)')  # composition-and-light §7：完全静止 >3 s 才是缺陷，不为凑动作加漂浮；落位停留看 motion_check 的 hold
    for f in flags:
        flags_total[f[0]] += 1
    lines.append(f'| {sid} | {lo}–{hi} | {med_h:.0f} / {min_h} | {low_run} | {np.median(gl):.0f} / {np.median(gt):.0f} | {np.median(pp):.0f} | {sbest} | {"；".join(flags) or "OK"} |')
head = f'# 构图/光/运动量化（{a.frames}，步长 {a.step}，幕底 {BG}）\n\n标记合计：高 {flags_total["高"]} / 中 {flags_total["中"]} / 低 {flags_total["低"]}。判据见 reference/composition-and-light.md §6。\n\n'
txt = head + '\n'.join(lines) + '\n'
if a.out:
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True); open(a.out, 'w', encoding='utf-8').write(txt); print(a.out)
print(txt)
