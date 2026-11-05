#!/usr/bin/env python3
"""对照：参照页 vs 我们的页。输出左右并排对照图（同高，标出两边文字行的墨迹框），并打印每行文字的位置/字高偏差表。

做法（复刻练习里的测量法合并成通用版）：
  1. 两张图都按 1440 宽换算坐标（参照图宽高比不同也行，y 方向同样按 1440 宽的比例换算）。
  2. macOS Vision OCR（scripts/ocr.swift，中文优先，首次自动编译到 bin/ocr）找每一行字的大致框。
  3. 在 OCR 框附近按文字颜色阈值（白/米白、黄、橙、电子青、红；浅底上找深色字）量出墨迹外接框，
     行内取与 OCR 框中线重叠最多的那一段，避免把上下行、图片亮部连进来。
  4. 两边的行按文字相似度配对（--match order 改成按阅读顺序配对，适合文案不同、只比版式的情况），
     我们这边用参照行同一种颜色来量。
  5. 偏差 = 我们 − 参照：左/上/右/下四边和字高（墨迹高，近似字号），单位是 1440 宽像素，1% = 14.4px。

用法：
  python3 scripts/对照.py 参照/p03.jpg pages/p03.png                  # 出 pages/p03_对照.png，打印偏差表
  python3 scripts/对照.py 参照.jpg 我们.png --out 对照.png --json 偏差.json
  python3 scripts/对照.py 参照.jpg 我们.png --match order --colors white,cyan
  python3 scripts/对照.py 参照.jpg 我们.png --no-ocr                   # 只出并排图

注意：参照图只在本机处理，不要上传到任何外部网站（以图搜图等），除非用户在对话里明确同意。
"""
import argparse, difflib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OCR = HERE / 'bin/ocr'
FONT = HERE.parent / 'assets/fonts/NotoSansSC[wght].ttf'
W = 1440
ONE_PCT = W / 100


def ocr_lines(path):
    """Vision 行框（ocr.swift：简体中文优先、再英文）：[{text, box:[x0,y0,x1,y1] 0–1，左上原点}]。"""
    import shutil, tempfile
    if not OCR.exists():
        OCR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['swiftc', '-O', str(HERE / 'ocr.swift'), '-o', str(OCR)], check=True)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'in'; src.mkdir()
        Image.open(path).convert('RGB').save(src / 'page.png')
        subprocess.run([str(OCR), str(src), str(Path(td) / 'ocr.json')], capture_output=True, text=True, encoding='utf-8', check=True)
        res = json.loads((Path(td) / 'ocr.json').read_text(encoding='utf-8'))
    out = []
    for o in (res[0].get('lines', []) if res else []):
        x, y, w, h = o['box']
        t = o['text'].strip()
        if t:
            out.append({'text': t, 'box': [x, y, x + w, y + h], 'conf': o.get('confidence')})
    return sorted(out, key=lambda o: (round(o['box'][1], 2), o['box'][0]))


def load_1440(path):
    im = Image.open(path).convert('RGB')
    k = W / im.width
    im = im.resize((W, round(im.height * k)), Image.LANCZOS)
    return im, np.asarray(im).astype(int)


def masks(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    return {
        'white': (mn > 165) & (mx - mn < 45),
        'yellow': (r > 170) & (g > 190) & (b < 150) & (r - b > 60),
        'cyan': (g > 150) & (b > 150) & (r < 120),
        'orange': (r > 200) & (g > 60) & (g <= 190) & (b < 120) & (r - b > 100),
        'red': (r > 170) & (g < 60) & (b < 100),
        'dark': mx < 90,
    }


def ink_box(a, box_px, colors, force=None):
    """在 box_px（OCR 框外扩后）里按颜色量墨迹框。返回 (颜色名, [x0,y0,x1,y1], 文字色) 或 (None, None, None)。"""
    H = a.shape[0]
    ox0, oy0, ox1, oy1 = box_px
    lh = oy1 - oy0
    x0, y0 = max(0, int(ox0 - 12)), max(0, int(oy0 - 0.35 * lh))
    x1, y1 = min(W, int(ox1 + 14)), min(H, int(oy1 + 0.35 * lh))
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None, None, None
    sub = a[y0:y1, x0:x1]
    border = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
    light_bg = np.median(border.mean(-1)) > 140
    ms = masks(sub)
    cands = [force] if force else [c for c in colors if (c == 'dark') == light_bg or (light_bg and c in ('red', 'orange', 'cyan'))]
    best = None
    for c in cands:
        if c not in ms:
            continue
        n = ms[c].sum()
        if best is None or n > best[1]:
            best = (c, n)
    if not best or best[1] < 6:
        return None, None, None
    name = best[0]; m = ms[name]
    rows = m.sum(1) > 1
    runs, st, last = [], None, None
    for i, v in enumerate(rows):
        if v:
            if st is None:
                st = i
            last = i
        elif st is not None and i - last > max(3, lh * 0.08):
            runs.append((st, last)); st = None
    if st is not None:
        runs.append((st, last))
    if not runs:
        return None, None, None
    cy0, cy1 = oy0 - y0 + lh * 0.1, oy1 - y0 - lh * 0.1
    run = max(runs, key=lambda r: min(r[1], cy1) - max(r[0], cy0))
    s2 = m[run[0]:run[1] + 1]
    cols = np.where(s2.sum(0) > 0)[0]
    bx = [x0 + int(cols.min()), y0 + run[0], x0 + int(cols.max()) + 1, y0 + run[1] + 1]
    px = sub[run[0]:run[1] + 1][s2]
    col = '#%02X%02X%02X' % tuple(int(v) for v in np.median(px, 0)) if len(px) else None
    return name, bx, col


def norm(t):
    return re.sub(r'[\s\W_]+', '', t)


def measure(path, colors, use_ocr=True):
    im, a = load_1440(path)
    if not use_ocr:
        return im, []
    H = a.shape[0]
    out = []
    for o in ocr_lines(path):
        b = o['box']
        px = [b[0] * W, b[1] * H, b[2] * W, b[3] * H]
        name, bx, col = ink_box(a, px, colors)
        out.append({**o, 'ocr_px': [round(v) for v in px], 'color': name, 'ink': bx, 'ink_color': col})
    return im, out


def pair_lines(ref, ours, mode):
    pairs, used = [], set()
    if mode == 'order':
        for i, (r, o) in enumerate(zip(ref, ours)):
            pairs.append((r, o))
        return pairs, ref[len(ours):], ours[len(ref):]
    scored = []
    for i, r in enumerate(ref):
        for j, o in enumerate(ours):
            s = difflib.SequenceMatcher(None, norm(r['text']), norm(o['text'])).ratio()
            if s >= 0.5:
                d = abs(r['ocr_px'][1] - o['ocr_px'][1]) + abs(r['ocr_px'][0] - o['ocr_px'][0])
                scored.append((-s, d, i, j))
    taken_r = set()
    for _, _, i, j in sorted(scored):
        if i in taken_r or j in used:
            continue
        taken_r.add(i); used.add(j); pairs.append((ref[i], ours[j]))
    pairs.sort(key=lambda p: (p[0]['ocr_px'][1], p[0]['ocr_px'][0]))
    return pairs, [r for i, r in enumerate(ref) if i not in taken_r], [o for j, o in enumerate(ours) if j not in used]


def main():
    ap = argparse.ArgumentParser(description='参照页 vs 我们的页：左右并排对照图（同高）＋文字行墨迹框偏差表（1440 宽像素与百分比）。',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split('用法：')[1])
    ap.add_argument('ref', type=Path, help='参照页（对标作者的原图，只在本机用）')
    ap.add_argument('ours', type=Path, help='我们的页（pages/pXX.png）')
    ap.add_argument('--out', type=Path, help='对照图输出路径，默认 <我们的页>_对照.png')
    ap.add_argument('--json', type=Path, help='把逐行测量和偏差写成 JSON')
    ap.add_argument('--colors', default='white,yellow,orange,cyan,red,dark', help='参与测量的文字颜色类，逗号分隔（white/yellow/orange/cyan/red/dark）')
    ap.add_argument('--match', choices=['text', 'order'], default='text', help='行配对方式：text=按文字相似度（默认），order=按阅读顺序')
    ap.add_argument('--no-ocr', action='store_true', help='不做 OCR 测量，只出并排图')
    ap.add_argument('--tol', type=float, default=1.0, help='超差阈值（占 1440 宽的百分比），默认 1%%')
    a = ap.parse_args()
    colors = [c.strip() for c in a.colors.split(',') if c.strip()]

    rim, ref = measure(a.ref, colors, not a.no_ocr)
    oim, ours_raw = measure(a.ours, colors, not a.no_ocr)
    rows, miss_r, miss_o = [], [], []
    if not a.no_ocr:
        ref = [r for r in ref if r['ink']]
        pairs, miss_r, miss_o = pair_lines(ref, ours_raw, a.match)
        oa = np.asarray(oim).astype(int)
        for k, (r, o) in enumerate(pairs, 1):
            _, ob, ocol = ink_box(oa, o['ocr_px'], colors, force=r['color'])
            if not ob:
                rows.append({'n': k, 'text': r['text'], 'ref': r['ink'], 'ours': None, 'color': r['color']}); continue
            d = [ob[i] - r['ink'][i] for i in range(4)]
            hr, ho = r['ink'][3] - r['ink'][1], ob[3] - ob[1]
            rows.append({'n': k, 'text': r['text'], 'ours_text': o['text'], 'color': r['color'], 'ref': r['ink'], 'ours': ob,
                         'delta': d, 'max_abs': max(map(abs, d)), 'max_pct': round(max(map(abs, d)) / ONE_PCT, 2),
                         'ink_h': [hr, ho], 'size_ratio': round(ho / hr, 3) if hr else None,
                         'ref_color': r['ink_color'], 'ours_color': ocol})

    # ---------------- 并排图（同高）
    Hs = oim.height
    rk = Hs / rim.height
    rs = rim.resize((round(rim.width * rk), Hs), Image.LANCZOS)
    gap, top = 24, 64
    canvas = Image.new('RGB', (rs.width + gap + oim.width, Hs + top), (245, 245, 245))
    canvas.paste(rs, (0, top)); canvas.paste(oim, (rs.width + gap, top))
    d = ImageDraw.Draw(canvas)
    lab = ImageFont.truetype(str(FONT), 30); small = ImageFont.truetype(str(FONT), 22)
    ok = [r for r in rows if r.get('ours')]
    summ = (f'{len(ok)} 行配对，偏差中位 {np.median([r["max_abs"] for r in ok]):.0f}px，最大 {max(r["max_abs"] for r in ok)}px，'
            f'超 {a.tol:g}% 的 {sum(r["max_pct"] > a.tol for r in ok)} 行') if ok else ('只出并排图' if a.no_ocr else '没有配上的文字行')
    d.text((16, 14), '参照', font=lab, fill=(30, 30, 30))
    d.text((rs.width + gap + 16, 14), '我们   ' + summ, font=lab, fill=(30, 30, 30))
    for r in rows:
        bad = r.get('max_pct', 0) > a.tol
        rb = [v * rk for v in r['ref']]
        d.rectangle([rb[0], rb[1] + top, rb[2], rb[3] + top], outline=(0, 200, 90), width=2)
        d.text((rb[0], rb[1] + top - 24), str(r['n']), font=small, fill=(0, 160, 70))
        if r.get('ours'):
            ob = r['ours']; x = rs.width + gap
            d.rectangle([ob[0] + x, ob[1] + top, ob[2] + x, ob[3] + top], outline=(230, 30, 30) if bad else (220, 0, 200), width=2)
            d.text((ob[0] + x, ob[1] + top - 24), str(r['n']), font=small, fill=(230, 30, 30) if bad else (200, 0, 180))
    out = a.out or a.ours.with_name(a.ours.stem + '_对照.png')
    canvas.save(out)

    # ---------------- 偏差表
    if not a.no_ocr:
        print(f'参照 {a.ref.name}  vs  我们 {a.ours.name}   单位：1440 宽像素（1% = {ONE_PCT:.1f}px）；偏差 = 我们 − 参照')
        print(f'{"#":>3} {"文字":<16} {"色":<6} {"参照墨迹框":<22} {"Δ左":>5} {"Δ上":>5} {"Δ右":>5} {"Δ下":>5} {"字高 参照/我们":>14} {"字高比":>7} {"最大%":>6}')
        for r in rows:
            t = (r['text'][:14]).ljust(14 - sum(1 for c in r['text'][:14] if ord(c) > 0x2E7F) + 2)
            if not r.get('ours'):
                print(f'{r["n"]:>3} {t} {r["color"]:<6} {str(r["ref"]):<22}  我们这边量不到（颜色不同或被图片挡住）'); continue
            dl = r['delta']
            flag = '  <-- 超差' if r['max_pct'] > a.tol else ''
            print(f'{r["n"]:>3} {t} {r["color"]:<6} {str(r["ref"]):<22} {dl[0]:>+5} {dl[1]:>+5} {dl[2]:>+5} {dl[3]:>+5} '
                  f'{r["ink_h"][0]:>6}/{r["ink_h"][1]:<6} {r["size_ratio"]:>7.3f} {r["max_pct"]:>5.2f}%{flag}')
        print(summ)
        if miss_r:
            print('参照里没配上的行：', '、'.join(m['text'][:12] for m in miss_r))
        if miss_o:
            print('我们多出来/没配上的行：', '、'.join(m['text'][:12] for m in miss_o))
    print('对照图：', out)
    if a.json:
        a.json.write_text(json.dumps({'ref': str(a.ref), 'ours': str(a.ours), 'unit': '1440宽像素', 'rows': rows,
                                      'unmatched_ref': [m['text'] for m in miss_r], 'unmatched_ours': [m['text'] for m in miss_o]},
                                     ensure_ascii=False, indent=1),encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
