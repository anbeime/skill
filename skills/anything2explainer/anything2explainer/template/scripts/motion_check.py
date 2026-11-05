#!/usr/bin/env python3
"""节奏体检（composition-and-light.md §7：持续动作 + 落位停留）。渲染某组（或读成片逐帧）每 3 帧抽一张，量内容区逐帧变化，按镜头区间统计：
  · 最长静止    内容区 320×180 灰度平均变化 <0.35 的最长连续段          判据 ≤3.0 s（>3 s → 中；--frames 模式再分：全分辨率变化像素 <800 真静 → 给动词动作；800–2500 小面积动作 → 加大幅度）
  · 末拍稳定期 hold  离场开始前最后一段「无大面积变化」的连续帧数       判据 ≥30 帧（<30 → 中：推后离场 / 前挂末拍元素 / 并镜头，不是加动作）；不离场的承接镜头 hold 带 ~，不判
  · 静止占比    只报不判（不许为它给静止物体加漂浮 / 呼吸）
用法：python3 scripts/motion_check.py G3                       → 渲 G3 预览合成该组帧区间，每 3 帧一张、0.5 倍
     python3 scripts/motion_check.py --frames fin_frames        → 对成片逐帧目录（QC 用）
     选项 --shots index   镜头区间改从 src/shots/G*/index.ts 读（分镜表帧号与成片不一致时，如换配音后 retime 的片子；没有分镜表时自动用它）
          --root <项目根>  默认脚本所在项目
注意：组级（低分辨率渲染）读数偏松，成片 fin_frames 复测才是最终判据。
「无大面积变化」= 320×180 采样灰度平均变化 <1.5（第五片成片实测：落位后只剩动词动作 / 慢推 / 呼吸的尾段 0.4–1.2，入场 / 22 帧滑入 / 33 帧推近 / 整组平移 2.5–15）。
所以 hold 量的是「版面落定后停了多久」，不是「完全不动了多久」；离场前 6 帧灭光算离场，已从 hold 里扣掉。设计得很大的循环动作（摆动的大字、整框虚线行进）会让 hold 变小，那正是 §7 不许的「为动而动」。"""
import sys, os, re, glob, subprocess, tempfile, shutil
import numpy as np
from PIL import Image

THR = 0.35            # 静止帧阈值（320×180 内容区灰度平均变化）
HOLD_THR = 1.5        # 「大面积变化」阈值（同口径；落位后的动词动作 0.4–1.2，入场 / 运镜 2.5+）
STILL_MAX_S = 3.0     # 最长静止上限（秒）
HOLD_MIN = 30         # 末拍稳定期下限（帧）
EXIT_K = 0.9          # 亮度掉到镜头尾段中位亮度的这个比例以下 = 已在离场
GLOW_OFF = 6          # 离场前先灭光的帧数，算离场，不算 hold
STEP = 3

args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
ROOT = os.path.abspath(opt('--root', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
shots_src = opt('--shots', 'auto')
if not args:
    raise SystemExit(__doc__)

def shots_from_storyboard():
    sb = open(f'{ROOT}/分镜表.md', encoding='utf-8').read()
    return [(m.group(1), int(m.group(2)), int(m.group(3))) for m in re.finditer(r'^\| (SC\d\d)[^|]*\| (\d+)–(\d+) \|', sb, re.M)], sb
def shots_from_index():
    out = []
    for p in sorted(glob.glob(f'{ROOT}/src/shots/G*/index.ts')):
        out += [(m.group(1), int(m.group(2)), int(m.group(3))) for m in re.finditer(r"\{id: '(SC\d+)', from: (\d+), to: (\d+)", open(p, encoding='utf-8').read())]
    return out
sb = ''
if shots_src == 'index' or (shots_src == 'auto' and not os.path.exists(f'{ROOT}/分镜表.md')):
    shots = shots_from_index()
else:
    shots, sb = shots_from_storyboard()
shots.sort(key=lambda s: s[1])
if not shots:
    raise SystemExit('没有镜头区间：分镜表.md 或 src/shots/G*/index.ts 都读不到')

def load_small(path):
    im = Image.open(path).convert('L').resize((320, 180))
    return np.asarray(im).astype(int)[28:158, :]   # 去掉 HUD（y<110）与字幕/进度条（y>630）
def load_content(path):
    im = np.asarray(Image.open(path).convert('L')).astype(int); h = im.shape[0]
    return im[int(h * 110 / 720):int(h * 630 / 720), :]
def changed_px(a, b):
    return int((np.abs(a - b) > 25).sum())

tmpdirs = []
FULL = args[0] == '--frames'
if FULL:
    d = args[1]; files = sorted(glob.glob(f'{d}/f_*.jpg'))[::STEP]
    frames = [(int(re.search(r'f_(\d+)', f).group(1)), f) for f in files]
else:
    comp = args[0]
    if sb:
        m = re.search(r'## ' + comp + r'（.*?\n(.*?)(?=\n## |\n---)', sb, re.S)
        ids = re.findall(r'^\| (SC\d\d)', m.group(1), re.M) if m else []
    else:
        p = f'{ROOT}/src/shots/{comp}/index.ts'
        ids = re.findall(r"\{id: '(SC\d+)'", open(p, encoding='utf-8').read()) if os.path.exists(p) else []
    rng = [(a, b) for (i, a, b) in shots if i in ids]
    if not rng:
        raise SystemExit(f'{comp}：分镜表 / index.ts 里找不到该组镜头')
    a, b = min(x[0] for x in rng), max(x[1] for x in rng)
    # 每次重新 bundle（代码在变、多组并发），用进程独占目录，跑完删除
    bundle = f'{ROOT}/build_dev_mc_{os.getpid()}'
    subprocess.run(['npx', 'remotion', 'bundle', 'src/index.ts', '--out-dir', bundle, '--log=error'], cwd=ROOT, check=True)
    out = tempfile.mkdtemp(prefix='motion_check_'); tmpdirs += [out, bundle]
    subprocess.run(['npx', 'remotion', 'render', bundle, comp, out, '--sequence', '--image-format=jpeg', '--jpeg-quality=80', '--scale=0.5', f'--every-nth-frame={STEP}', f'--frames={a-1}-{b-1}', '--concurrency=4', '--log=error'], cwd=ROOT, check=True)
    files = sorted(glob.glob(f'{out}/*.jpeg') + glob.glob(f'{out}/*.jpg'))
    frames = [(a + i * STEP, f) for i, f in enumerate(files)]
    shots = [s for s in shots if s[0] in ids]

small = {f: load_small(p) for f, p in frames}
path_of = dict(frames)
fnums = [f for f, _ in frames]
diffs = {fnums[i + 1]: float(np.abs(small[fnums[i + 1]] - small[fnums[i]]).mean()) for i in range(len(fnums) - 1)}

print(f'{"shot":6s} {"len":>5s} {"still%":>7s} {"longest":>8s} {"hold":>6s}  verdict' + ('   longest-run  fullres-changed-px  class' if FULL else ''))
print(f'判据：最长静止 ≤{STILL_MAX_S:.0f} s；末拍稳定期 hold ≥{HOLD_MIN} 帧（离场前最后一段无大面积变化的连续帧；带 ~ = 该镜头不离场、承接进下一镜头，只供参考）；still% 只报不判。')
bad = 0
for sid, a, b in shots:
    fs = [f for f in fnums if a <= f <= b]
    if len(fs) < 3:
        continue
    d = [diffs[f] for f in fs[1:]]
    still = sum(v < THR for v in d) / len(d) * 100
    run = best = 0; end = 0
    for i, v in enumerate(d):
        run = run + 1 if v < THR else 0
        if run > best:
            best = run; end = i
    longest = best * STEP / 30
    # 末拍稳定期：先剔掉尾部已在离场的帧（亮度 < 尾段中位亮度 × EXIT_K），再从最后一张可见帧往前数「无大面积变化」的帧
    bright = [small[f].mean() for f in fs]
    ref = float(np.median(bright[-20:]))
    e = len(fs) - 1
    while e > 0 and bright[e] < EXIT_K * ref:
        e -= 1
    exited = e < len(fs) - 1
    hold = 0; k = e
    while k > 0 and diffs[fs[k]] < HOLD_THR:
        hold += STEP; k -= 1
    if exited:
        hold = max(0, hold - GLOW_OFF)
    flags = []
    if longest > STILL_MAX_S:
        flags.append(f'✗ still>{STILL_MAX_S:.0f}s')
    if exited and hold < HOLD_MIN:
        flags.append(f'✗ hold<{HOLD_MIN}f')
    verdict = ' '.join(flags) or 'OK'
    if flags:
        bad += 1
    extra = ''
    if FULL and longest > STILL_MAX_S and best > 0:
        s_ = fs[1:][end - best + 1] - STEP; e_ = fs[1:][end]
        imgs = [load_content(path_of[f]) for f in fs if max(a, s_) <= f <= e_]
        ch = [changed_px(imgs[i], imgs[i + 1]) for i in range(len(imgs) - 1)]
        cp = int(np.median(ch)) if ch else 0
        cls = '真静' if cp < 800 else ('小面积动作' if cp < 2500 else '有动作')
        extra = f'   {max(a, s_)}-{e_}  {cp:6d}  {cls}'
    print(f'{sid:6s} {(b-a+1)/30:4.1f}s {still:6.0f}% {longest:7.1f}s {hold:4d}f{"~" if not exited else " "}  {verdict}{extra}')
print(f'shots failing: {bad}')
for t in tmpdirs:
    shutil.rmtree(t, ignore_errors=True)
