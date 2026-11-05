#!/usr/bin/env python3
"""排版器：内容.json → 页面脚本.json → 1440×1920 成品。

v2（默认，原版风）版式在 layouts_v2.py：图文叠、立像、圆像、渐隐、宽幅、错落——无框照片、人物抠图贴边出血、
强调色粗黑体标题和强调句、文字绕开人物轮廓排、手绘箭头。下面的旧版式（v1）来自第5篇《头上顶着一艘战舰》，仍可用。
作者只写文字、选图。排版器负责：
- 按语意断行（先在标点处断，保护人名、书名、短引文、日期），不留孤字；
- 按栏高自动挑字号（正文52–60，强调84–108），把间距匀开，减少大块空黑；
- 标题与强调句「毛笔蓝 / 白色宋体」逐页交替；
- 不生成图注、页眉、页码、栏目名或页脚口号——这些在本风格里一律不要。

用法：
  python3 scripts/build.py 工作/新选题/内容.json --out 工作/新选题/成品
  python3 scripts/build.py 内容.json --out 成品 --pages 2,5      # 只重排第2、5张
  python3 scripts/build.py 内容.json --capacity                   # 只打印每个文字栏每行能放几个字
"""
from pathlib import Path
import sys, json, re, copy, shutil, argparse, math
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import render as RD
import layouts_v2 as V2

W, H = 1440, 1920
L, RIGHT = 0.056, 0.944
FULL = round(RIGHT - L, 4)
WHITE = '#FFFFFF'
SHADOW = {'color': '#000000', 'offset': [8, 10], 'blur': 12, 'opacity': 0.5}
TITLE_BOX = [L, 0.035, FULL, 0.17]
BOTTOM = 0.955                      # 文字最低到这里，给右下角署名留位
GAP_MIN, GAP_MAX = 54 / H, 150 / H  # 文字块之间的间距
PREF = {'body': 56, 'emphasis': 96, 'foot': 52, 'note': 48}
STEP = {'body': 2, 'emphasis': 4, 'foot': 2, 'note': 0}
LIMIT = {'body': (52, 60), 'emphasis': (84, 108), 'foot': (48, 56), 'note': (48, 48)}
LAYOUT_NAMES = ['封面', '右抠图', '左大图', '横幅', '整版底', '双图', '物件', '收尾']

# ---------------------------------------------------------------- 文字元素

def brush(text, box, size, fill, role='heading'):
    return {'kind': 'text', 'text': text, 'box': box, 'size': size, 'font': 'heading', 'fill': fill,
            'lineheight': round(size * 1.28), 'spacing': 0, 'tight_punctuation': 'all', 'text_role': role,
            'callout': True, 'effect': '3d', 'bold': 1, 'depth': 7, 'shadow_color': '#0C0C0C'}


def serif(text, box, size, fill=WHITE, role='heading'):
    return {'kind': 'text', 'text': text, 'box': box, 'size': size, 'font': 'serif-bold', 'fill': fill,
            'lineheight': round(size * 1.3), 'spacing': 0, 'tight_punctuation': 'all', 'text_role': role,
            'callout': True}


def note(text, box, size, bg):
    """底色文字：强调色逐行底条＋黑字，用来突出原话、关键数字或证据边界。"""
    from PIL import ImageColor
    r, g, b_ = ImageColor.getrgb(bg)[:3]
    ink = '#111111' if (0.299 * r + 0.587 * g + 0.114 * b_) / 255 > 0.55 else '#FFFFFF'   # 底色深就用白字
    return {'kind': 'text', 'text': text, 'box': box, 'size': size, 'font': 'sans-bold', 'fill': ink,
            'bg': bg, 'lineheight': round(size * 1.5), 'spacing': 0, 'tight_punctuation': 'all', 'text_role': 'note'}


def body(text, box, size):
    return {'kind': 'text', 'text': text, 'box': box, 'size': size, 'font': 'body', 'fill': WHITE,
            'lineheight': round(size * 1.32), 'spacing': 0, 'tight_punctuation': 'all', 'text_role': 'body'}


# ---------------------------------------------------------------- 测量与断行

CFG = {'accent': '#5AA9E6', 'background': '#000000'}
_CANVAS = Image.new('RGBA', (4, 4))
_FIT_CACHE = {}


def rendered_lines(proto, text):
    """用渲染器同一套换行逻辑数行数（画在4×4的空画布上，只取统计）。"""
    key = (proto['font'], proto['size'], round(proto['box'][2], 5), proto.get('effect'), proto.get('spacing'), text,
           proto.get('hscale'), proto.get('typo'), proto.get('latin_font'), proto.get('latin_scale'), proto.get('stroke'),
           proto.get('tight_punctuation'), proto.get('punctuation_gap'), proto.get('punctuation_shift'), proto.get('fallback_font'))
    if key in _FIT_CACHE:
        return _FIT_CACHE[key]
    m = {k: v for k, v in proto.items() if k not in ('effect', 'soft_shadow', 'shadow', 'glow', 'bg', 'stroke_fill')}
    if proto.get('effect') == '3d':
        m['stroke'] = proto.get('bold', 1)
    m.update(text=text, box=[proto['box'][0], 0, proto['box'][2], 50])
    audit = []
    RD.draw_text(_CANVAS, m, CFG, W, H, audit)
    _FIT_CACHE[key] = audit[-1]['lines']
    return _FIT_CACHE[key]


def fits(proto, text):
    return rendered_lines(proto, text) == 1


CLAUSE_END = set('，。：；！？…')
OPENING = set('「『《（(“')
CLOSING = set('，。、：；！？…」』》）)”,.!?:;·')
FRIENDLY_AFTER = set('的了着过在和与及把被是到从给向对为里上中后前时地得也都就还又才再却而并或说道')


try:
    import jieba                     # 可选：有就按词断行，没有就按字
    jieba.setLogLevel(60)
except Exception:
    jieba = None


def words(run):
    return [w for w in jieba.lcut(run)] if jieba and run else list(run)


def atoms(text, protect):
    pats = [re.escape(t) for t in sorted(protect, key=len, reverse=True) if t]
    pats += [r'\[\[.*?\]\]', r'《[^》]{1,16}》', r'「[^」]{1,7}」',
             r'\d{1,4}年(?:\d{1,2}月(?:\d{1,2}日)?)?', r'\d{1,2}月\d{1,2}日',
             r'\d[\d.,]*(?:年代|世纪|万|亿|千|百|厘米|毫米|公里|法寸|英寸|英尺|小时|分钟|岁|天|个|倍|号|米|寸|%|％)?',
             r'[A-Za-z][A-Za-z\'’\-]*']
    rx = re.compile('|'.join(f'(?:{p})' for p in pats))
    out, i, run = [], 0, ''
    while i < len(text):
        m = rx.match(text, i)
        if m and m.end() > i:
            out += words(run); run = ''
            out.append(m.group(0)); i = m.end()
        elif text[i] in CLOSING or text[i] in OPENING:
            out += words(run); run = ''
            out.append(text[i]); i += 1
        else:
            run += text[i]; i += 1
    out += words(run)
    merged = []                      # 标点贴前，开引号贴后，外文名间隔号「·」两边连住
    for a in out:
        if merged and a and a[0] in CLOSING and not a.startswith('[['):
            merged[-1] += a
        elif merged and merged[-1] and merged[-1][-1] in OPENING | {'·'} and not merged[-1].startswith('[['):
            merged[-1] += a
        else:
            merged.append(a)
    return merged


def visible_len(s):
    s = s.replace('[[', '').replace(']]', '')
    return sum(1 for ch in s if ch not in CLOSING and ch not in OPENING and not ch.isspace())


NO_START = set('的了着地得们吗呢吧啊')


def break_score(seq, k, kmax, cap):
    """在 seq[k] 前断行的得分：标点/引号处最好，词与词之间次之；两行尽量匀称；不让「的」「里，」开头，也不留两个字的短行。"""
    nxt, prev = seq[k], seq[k - 1]
    if nxt[0] in NO_START or (visible_len(nxt) <= 1 and nxt[-1] in CLOSING):
        return None
    head, tail = visible_len(''.join(seq[:k])), visible_len(''.join(seq[k:]))
    score = 3 if nxt[0] in OPENING or prev[-1] in CLOSING else 1 if prev[-1] in FRIENDLY_AFTER or len(prev) >= 2 else 0
    if head <= 2:
        score -= 3
    elif head < cap * 0.45:
        score -= 2
    if tail < 3:
        score -= 2.5
    score -= 0.25 * abs(head - tail) if head + tail <= 2 * cap else 0.35 * (kmax - k)
    return score


def split_long(proto, seq):
    """一段放不下的分句：在能放下的范围里挑得分最高的断点。"""
    lines = []
    cap = proto['box'][2] * W / proto['size']
    while seq and not fits(proto, ''.join(seq)):
        kmax = 0
        for k in range(1, len(seq)):
            if fits(proto, ''.join(seq[:k])):
                kmax = k
            else:
                break
        if kmax == 0:
            raise ValueError(f'一个词也放不下：{seq[0]}（栏太窄或字太大）')
        best, best_score = kmax, None
        for k in range(kmax, 0, -1):
            sc = break_score(seq, k, kmax, cap)
            if sc is not None and (best_score is None or sc > best_score):
                best, best_score = k, sc
        lines.append(seq[:best]); seq = seq[best:]
    if seq:
        lines.append(seq)
    return lines


def wrap(proto, text, protect=()):
    """返回带\\n的文字。已手动断行的保留；某行放不下才在行内再断。"""
    if '\n' in text:
        out = []
        for line in text.split('\n'):
            out.append(line if fits(proto, line) else wrap(proto, line, protect))
        return '\n'.join(out)
    if fits(proto, text):
        return text
    at = atoms(text, protect)
    clauses, cur = [], []
    for a in at:
        cur.append(a)
        if a[-1] in CLAUSE_END:
            clauses.append(cur); cur = []
    if cur:
        clauses.append(cur)
    lines, cur = [], []
    cap = proto['box'][2] * W / proto['size']
    for cl in clauses:
        ended = cur and cur[-1][-1] in '。！？' and visible_len(''.join(cur)) > cap * 0.4
        if cur and not ended and fits(proto, ''.join(cur + cl)):
            cur += cl; continue
        if cur:
            lines.append(cur); cur = []
        if fits(proto, ''.join(cl)):
            cur = list(cl)
        else:
            parts = split_long(proto, list(cl))
            lines += parts[:-1]; cur = parts[-1]
    if cur:
        lines.append(cur)
    # 防孤字：末行不足3个字，就从上一行挪词下来
    while len(lines) >= 2 and visible_len(''.join(lines[-1])) < 3 and len(lines[-2]) > 1:
        moved = lines[-2][-1:]
        cand_prev, cand_last = lines[-2][:-1], moved + lines[-1]
        if visible_len(''.join(cand_prev)) < 3 or not fits(proto, ''.join(cand_last)):
            break
        lines[-2], lines[-1] = cand_prev, cand_last
    return '\n'.join(''.join(l) for l in lines)


# ---------------------------------------------------------------- 图片元素

def is_cutout(path):
    try:
        with Image.open(path) as im:
            return im.mode in ('RGBA', 'LA') and im.getchannel('A').getextrema()[0] < 255
    except Exception:
        return False


def img_meta(spec, root):
    p = root / spec['path']
    if not p.exists():
        raise FileNotFoundError(f'找不到图片：{spec["path"]}')
    with Image.open(p) as im:
        size = im.size
    return p, size, spec.get('kind') or ('cutout' if is_cutout(p) else 'photo')


def face_fields(spec):
    faces = spec.get('face', [])
    if faces and isinstance(faces[0], (int, float)):
        faces = [faces]
    return {'face_boxes': faces, 'face_detection_method': spec.get('face_method', 'manual-verified'),
            'face_verified': bool(faces), 'face_review': spec.get('face_review', '人工目检')}


def sid(spec):
    return spec.get('id') or Path(spec['path']).stem


def cutout_el(spec, box, hero=True):
    return {'kind': 'image', 'path': spec['path'], 'box': box, 'fit': 'contain', 'role': 'foreground',
            'source_id': sid(spec), 'hero': hero, 'hero_form': 'cutout', 'major_image': hero,
            'soft_shadow': SHADOW, 'color_source': True, **face_fields(spec)}


def photo_el(spec, box, hero=True, torn=True):
    e = {'kind': 'image', 'path': spec['path'], 'box': box, 'fit': 'cover', 'source_id': sid(spec),
         'effects': ['torn'] if torn and spec.get('torn', True) else [], 'focus': spec.get('focus', [0.5, 0.4]),
         'soft_shadow': SHADOW, 'major_image': hero, 'hero': hero, 'color_source': True, **face_fields(spec)}
    if hero:
        e['hero_form'] = 'rectangle'
    if spec.get('crop'):
        e['crop'] = spec['crop']
    return e


def snug_box(spec, root, box, side='left'):
    """抠图按实际比例收紧占位框；底边是裁切边（半身像）就贴到页面底部，像从画面下方长出来。"""
    p, (iw, ih), _ = img_meta(spec, root)
    with Image.open(p) as im:
        a = np.asarray(im.getchannel('A')) if im.mode == 'RGBA' else None
    cut_bottom = a is not None and (a[-3:] > 128).mean() > 0.12
    bx, by, bw, bh = box[0] * W, box[1] * H, box[2] * W, box[3] * H
    s = min(bw / iw, bh / ih); w, h = iw * s, ih * s
    x = bx if side == 'left' else bx + bw - w if side == 'right' else bx + (bw - w) / 2
    if cut_bottom and by + bh >= 0.9 * H:
        y = H - h
    elif cut_bottom:
        y = by + bh - h
    else:
        y = by + (bh - h) / 2
    return [round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4)]


def image_el(spec, root, box_cut, box_photo, hero=True, side='left'):
    _, _, kind = img_meta(spec, root)
    if kind == 'cutout':
        return cutout_el(spec, snug_box(spec, root, box_cut, side), hero)
    return photo_el(spec, box_photo, hero)


def backdrop_el(spec, box, darken, fade):
    e = {'kind': 'dark_backdrop', 'path': spec['path'], 'box': box, 'fit': 'cover', 'source_id': sid(spec),
         'darken': spec.get('darken', darken), 'role': 'background', 'fade_fraction': fade,
         'cover_only': True, 'focus': spec.get('focus', [0.5, 0.5]), 'color_source': True,
         'face_boxes': spec.get('face', []), 'face_detection_method': spec.get('face_method', 'manual-verified')}
    if spec.get('crop'):
        e['crop'] = spec['crop']
    return e


def disc_el(cx, cy, r, color):
    return {'kind': 'ellipse', 'box': [cx - r / W, cy - r / H, 2 * r / W, 2 * r / H], 'fill': color,
            'circle_backdrop': True, 'circle_center': [cx, cy], 'radius_pixels': r}


def contain_face_center(spec, root, box):
    """抠图按contain放进框后，人脸中心落在页面哪里（用来放圆盘）。"""
    p, (iw, ih), _ = img_meta(spec, root)
    faces = face_fields(spec)['face_boxes']
    with Image.open(p) as im:
        bb = im.getchannel('A').getbbox() if im.mode == 'RGBA' else (0, 0, iw, ih)
    bx, by, bw, bh = box[0] * W, box[1] * H, box[2] * W, box[3] * H
    s = min(bw / iw, bh / ih); ox, oy = bx + (bw - iw * s) / 2, by + (bh - ih * s) / 2
    if faces:
        fx, fy, fw, fh = faces[0]
        return (ox + (fx + fw / 2) * iw * s) / W, (oy + (fy + fh * 0.65) * ih * s) / H
    return (ox + iw * s / 2) / W, (oy + ih * s * 0.35) / H


def muted(color):
    return RD.muted_accent(color)


# ---------------------------------------------------------------- 文字栏排布

class Block:
    def __init__(self, role, text, style, accent, protect, image=None):
        self.role, self.text, self.style, self.accent, self.protect, self.image = role, text, style, accent, protect, image

    def element(self, x, w, size, y=0.0):
        if self.image is not None:
            return None
        box = [x, y, w, 0.1]
        make = lambda sz: (brush(self.text, list(box), sz, self.accent, 'emphasis') if self.style == 'brush'
                           else serif(self.text, list(box), sz, WHITE, 'emphasis')) if self.role == 'emphasis' else (
                           note(self.text, list(box), sz, self.accent) if self.role == 'note' else body(self.text, list(box), sz))
        e = make(size)
        if '\n' in self.text:       # 作者手动断的行：放不下就缩字号，不在行内再折
            lo = LIMIT[self.role][0]
            while size > lo and not all(fits({**e, 'box': [x, 0, w * 0.93, 1]}, ln) for ln in self.text.split('\n')):
                size -= STEP[self.role]; e = make(size)
        e['box'][2] = w * 0.97        # 断行时留3%余量，句末标点不出界
        e['text'] = wrap(e, self.text, self.protect)
        e['box'][2] = w
        e['box'][3] = round((e['text'].count('\n') + 1) * e['lineheight'] / H + 8 / H, 4)
        return e


def lay_column(blocks, x, w, y0, y1, width_factor=1.0, step=None):
    """在一栏里竖排几个块：先试大字号，放得下就用；间距在 GAP_MIN–GAP_MAX 之间匀开。"""
    w_eff = w * width_factor
    steps = [step] if step is not None else [1, 0, -1, -2, -3]
    last = None
    for s, gmin in [(s, GAP_MIN) for s in steps] + [(steps[-1], 28 / H)]:
        els, total = [], 0.0
        for b in blocks:
            if b.image is not None:
                h = b.image['box'][3]; els.append(('img', b, h)); total += h; continue
            lo, hi = LIMIT[b.role]
            size = max(lo, min(hi, PREF[b.role] + s * STEP[b.role]))
            e = b.element(x, w_eff, size)
            e['box'][2] = w   # 断行按收窄后的宽度，框保持原宽
            els.append(('txt', e, e['box'][3])); total += e['box'][3]
        n = len(els)
        need = total + gmin * max(0, n - 1)
        last = (els, total, s)
        if need <= y1 - y0 + 1e-6:
            gap = min(GAP_MAX, (y1 - y0 - total) / max(1, n - 1)) if n > 1 else 0
            y, out = y0, []
            for kind, obj, h in els:
                if kind == 'img':
                    e = copy.deepcopy(obj.image); e['box'][1] = round(y, 4); out.append(e)
                else:
                    obj['box'][1] = round(y, 4); out.append(obj)
                y += h + gap
            leftover = (y1 - (y - gap)) if n else (y1 - y0)
            if s == 1 and step is None and leftover > 0.12:
                try:                     # 空得多就再放大一档
                    bigger = lay_column(blocks, x, w, y0, y1, width_factor, 2)
                    if bigger[1]['leftover'] >= 0:
                        return bigger
                except ValueError:
                    pass
            return out, {'step': s, 'leftover': round(leftover, 3)}
    imgs = [b for b in blocks if b.image is not None]
    if imgs and imgs[0].image['box'][3] > 0.17:          # 栏里有配图：先把配图缩小再排
        for b in imgs:
            bx = b.image['box']; b.image = {**b.image, 'box': [bx[0], bx[1], round(bx[2] * 0.85, 4), round(bx[3] * 0.85, 4)]}
        return lay_column(blocks, x, w, y0, y1, width_factor, step)
    els, total, s = last
    raise ValueError(f'文字太多，这一栏放不下（需要{(total + GAP_MIN * (len(els) - 1)) * H:.0f}px，'
                     f'只有{(y1 - y0) * H:.0f}px）：请删字，或换一个文字栏更大的版式')


# ---------------------------------------------------------------- 版式

def title_el(page, style, accent, protect):
    text = page['title']
    if '\n' not in text and '，' in text.strip('，') and len(text) >= 7 and not page.get('title_one_line'):
        a, b = text.split('，', 1); text = a + '，\n' + b
    size = page.get('title_size', 118)
    while True:
        e = brush(text, list(TITLE_BOX), size, accent) if style == 'brush' else serif(text, list(TITLE_BOX), size)
        e['text'] = wrap(e, text, protect)
        if e['text'].count('\n') <= 1 or size <= 100:
            break
        size -= 6
    if e['text'].count('\n') > 1:
        raise ValueError(f'标题超过两行：{page["title"]}（标题请控制在每行8字以内、最多两行）')
    e['box'][3] = round((e['text'].count('\n') + 1) * e['lineheight'] / H + 10 / H, 4)   # 框高=实际行高，避免和图片误判碰撞
    return e


def build_page(i, page, ctx, width_factor=1.0):
    """返回 (页面脚本, 排版说明)。i 从1开始，1是封面。"""
    accent, root, protect = ctx['accent'], ctx['root'], ctx['protect'] + page.get('protect', [])
    lay = page.get('layout')
    if i == 1 or lay == '封面':
        return cover_page(page, ctx), {'layout': '封面'}
    if lay in V2.LAYOUTS:
        return V2.build_page(i, page, ctx, sys.modules[__name__], width_factor)
    if lay not in LAYOUT_NAMES:
        raise ValueError(f'第{i}张版式「{lay}」不存在；可选：{"、".join(V2.LAYOUTS + LAYOUT_NAMES[1:])}')
    t_style = page.get('title_style') or ('serif' if i % 2 == 0 else 'brush')
    if re.search(r'\d', page.get('title', '')):
        t_style = 'serif'            # 毛笔字体不写阿拉伯数字
    e_style = page.get('emphasis_style') or ('brush' if t_style == 'serif' else 'serif')
    if re.search(r'\d', page.get('emphasis', '')):
        e_style = 'serif'
    mk = lambda role: Block(role, page[role], e_style if role == 'emphasis' else None, accent, protect) if page.get(role) else None
    B = {r: mk(r) for r in ('body', 'note', 'emphasis', 'foot')}
    order = [r for r in page.get('order', ['body', 'note', 'emphasis', 'foot']) if B.get(r)]
    els, info, cols = [], {'layout': lay}, []
    hero, second, bd = page.get('hero'), page.get('second'), page.get('backdrop')

    if lay == '右抠图':
        wide = page.get('wide_bottom', False)
        hbox = [0.47, 0.20, 0.52, 0.52] if wide else [0.47, 0.20, 0.52, 0.765]
        he = image_el(hero, root, hbox, [0.47, 0.215, 0.50, 0.70 if not wide else 0.50], side='right')
        if page.get('disc'):
            cx, cy = contain_face_center(hero, root, he['box'])
            r = page['disc'].get('r', 300) if isinstance(page['disc'], dict) else 300
            els.append(disc_el(round(cx, 4), round(cy, 4), r, page.get('disc_color', muted(accent))))
        els.append(he)
        if wide:
            cols.append(([B[r] for r in order if r in ('body', 'note')], L, 0.40, 0.235, 0.70))
            cols.append(([B[r] for r in order if r not in ('body', 'note')], L, FULL, 0.73, BOTTOM))
        else:
            cols.append(([B[r] for r in order], L, 0.40, 0.235, BOTTOM))

    elif lay == '左大图':
        els.append(image_el(hero, root, [0.0, 0.17, 0.52, 0.82], [0.0, 0.20, 0.53, 0.75]))
        blocks = [B[r] for r in order]
        if second:
            sb = Block('image', '', None, accent, protect, image=photo_el(second, [0.555, 0, 0.27, 0.30], hero=False)
                       if img_meta(second, root)[2] == 'photo' else cutout_el(second, [0.555, 0, 0.30, 0.28], hero=False))
            blocks.insert(min(len(blocks), 2), sb)
        cols.append((blocks, 0.555, 0.389, 0.235, BOTTOM))

    elif lay == '横幅':
        if bd:
            els.append(backdrop_el(bd, [0, 0.20, 1, 0.42], 0.42, 0.25))
            if B['emphasis']:
                b = B['emphasis']; e = b.element(L, 0.60, page.get('emphasis_size', 96))
                e['box'][1] = round(0.41 - e['box'][3] / 2, 4); els.append(('text', e)); order = [r for r in order if r != 'emphasis']
        elif hero:
            band = page.get('band', 0.40)            # 文字多时自动压低横幅（见 build_page 外层重试）
            els.append(photo_el(hero, [L, 0.215, FULL, band], hero=True))
        top = 0.215 + (page.get('band', 0.40) if (hero and not bd) else 0.40) + 0.02
        if second:
            els.append(image_el(second, root, [0.60, top - 0.035, 0.34, 0.36], [0.60, top - 0.035, 0.34, 0.36], hero=not bd and not hero))
            cols.append(([B[r] for r in order], L, 0.52, top - 0.01, BOTTOM))
        else:
            cols.append(([B[r] for r in order], L, FULL, top, BOTTOM))

    elif lay == '整版底':
        els.append(backdrop_el(bd, [0, 0, 1, 1], 0.66, 0))
        els.append(image_el(hero, root, [0.50, 0.24, 0.48, 0.61 if page.get('foot') else 0.74], [0.52, 0.26, 0.42, 0.56], side='right'))
        cols.append(([B[r] for r in order if r != 'foot'], L, 0.44, 0.235, 0.845))
        if B['foot']:
            cols.append(([B['foot']], L, FULL, 0.862, BOTTOM))

    elif lay == '双图':
        if second:
            els.append(image_el(second, root, [0.655, 0.215, 0.29, 0.22], [0.655, 0.215, 0.29, 0.22], hero=False, side='right'))
        els.append(image_el(hero, root, [0.0, 0.50, 0.46, 0.49], [L, 0.52, 0.40, 0.42]))
        cols.append(([B[r] for r in order if r in ('body', 'note')], L, 0.58 if second else FULL, 0.225, 0.47))
        cols.append(([B[r] for r in order if r not in ('body', 'note')], 0.50, 0.444, 0.505, BOTTOM))

    elif lay == '物件':
        els.append(image_el(second, root, [0.12, 0.345, 0.84, 0.30], [0.12, 0.345, 0.76, 0.29], hero=False, side='center'))
        els.append(image_el(hero, root, [0.0, 0.62, 0.36, 0.38], [L, 0.66, 0.30, 0.30]))
        cols.append(([B['body']] if B['body'] else [], L, FULL, 0.212, 0.34))
        cols.append(([B[r] for r in order if r != 'body'], 0.40, 0.544, 0.655, BOTTOM))

    elif lay == '收尾':
        els.append(image_el(hero, root, [0.47, 0.18, 0.52, 0.68], [0.47, 0.20, 0.50, 0.64], side='right'))
        if second:
            els.append(image_el(second, root, [L, 0.655, 0.29, 0.25], [L, 0.655, 0.29, 0.25], hero=False))
        cols.append(([B[r] for r in order if r != 'foot'], L, 0.40, 0.225, 0.64 if second else 0.83))
        if B['foot']:
            cols.append(([B['foot']], 0.38, 0.564, 0.85, BOTTOM))

    texts = [title_el(page, t_style, accent, protect)]
    for item in [e for e in els if isinstance(e, tuple)]:
        texts.append(item[1])
    images = [e for e in els if not isinstance(e, tuple)]
    info['columns'] = []
    for blocks, x, w, y0, y1 in cols:
        blocks = [b for b in blocks if b]
        if not blocks:
            continue
        out, meta = lay_column(blocks, x, w, y0, y1, width_factor, page.get('step'))
        info['columns'].append(meta)
        for e in out:
            (texts if e.get('kind') == 'text' else images).append(e)
    k = ctx.get('shrink', {}).get(i, 0)
    if k:                                   # 与文字相撞时：前景图每次缩小6%，向远离文字的一侧收
        for e in images:
            if e.get('kind') == 'image' and e.get('fit') == 'contain':
                x, y, w, h = e['box']; f = 0.94 ** k
                nx = x + w * (1 - f) if x > 0.3 else x
                e['box'] = [round(nx, 4), round(y + h * (1 - f), 4), round(w * f, 4), round(h * f, 4)]
    hero_id = next((e.get('source_id') for e in images if e.get('hero')), None) or next((e.get('source_id') for e in images), '')
    p = {'layout': 'collage', 'background': '#000000', 'watermark': True, 'skeleton': lay,
         'text_position': '+'.join(f'{round(c[1], 2)},{round(c[3], 2)}' for c in cols), 'visual_focus': hero_id,
         'elements': images + texts}
    return p, info


def cover_page(page, ctx):
    root, accent, work = ctx['root'], ctx['accent'], ctx['work']
    spec = page['hero']
    p, (iw, ih), _ = img_meta(spec, root)
    im = Image.open(p).convert('RGB')
    if spec.get('crop'):
        x0, y0, x1, y1 = spec['crop']; im = im.crop((round(x0 * iw), round(y0 * ih), round(x1 * iw), round(y1 * ih)))
    cw, ch = im.size
    tw, th = (cw, round(cw * 4 / 3)) if cw * 4 / 3 <= ch else (round(ch * 3 / 4), ch)
    fx, fy = spec.get('focus', [0.5, 0.35])
    left = min(max(0, round(fx * cw - tw / 2)), cw - tw); top = min(max(0, round(fy * ch - th / 2)), ch - th)
    im = im.crop((left, top, left + tw, top + th)).resize((W, H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); yy = np.arange(H) / H
    t = np.clip((yy - 0.58) / (0.82 - 0.58), 0, 1); k = 0.5 - 0.5 * np.cos(np.pi * t)
    a *= (1 - page.get('cover_dark', 0.55 if ctx.get('style') == 'v2' else 0.90) * k)[:, None, None]
    work.mkdir(parents=True, exist_ok=True)
    out = work / 'cover-bg.jpg'
    Image.fromarray(a.clip(0, 255).astype('uint8')).save(out, quality=94)
    shadow = {'color': '#000000', 'offset': [6, 7], 'blur': 5, 'opacity': 0.43}
    v2 = ctx.get('style') == 'v2'
    face = 'cover-display' if v2 else 'cover-title'   # v2：封面用思源宋体 Black＋立体投影（内页标题另用 title-display）
    l1 = {**brush(page['line1'], [L, 0.752 if v2 else 0.745, 0.89, 0.08 if v2 else 0.07], page.get('line1_size', 112 if v2 else 98), WHITE),
          'font': face, 'soft_shadow': shadow}
    size2 = page.get('line2_size', 168 if v2 else 156)
    while True:
        # v2：第二行尽量撑到画面宽度的八成左右（短句字就大），和对标账号一致
        l2 = {**brush(page['line2'], [L if v2 else 0.095, 0.828 if v2 else 0.835, 0.80 if v2 else 0.85, 0.115 if v2 else 0.105], size2, accent),
              'font': face, 'soft_shadow': shadow}
        if fits(l2, page['line2']) or size2 <= 100:
            break
        size2 -= 6
    if v2:
        l2['box'][2] = 0.89
        if page.get('line2_align'):
            l2['align'] = page['line2_align']
            if page['line2_align'] == 'right':
                l2['box'][2] = 0.915 - l2['box'][0]     # 靠右时离边框留够 60px 以上（含阴影）
        if page.get('line1_align'):
            l1['align'] = page['line1_align']
        if page.get('line2_indent'):
            l2['box'][0] += page['line2_indent']; l2['box'][2] -= page['line2_indent']
        for e in (l1, l2):
            e.update(depth=12, bold=1, shadow_color='#000000', soft_shadow={'color': '#000000', 'offset': [8, 11], 'blur': 9, 'opacity': 0.7})
    if not fits(l2, page['line2']):
        raise ValueError(f'封面第二行太长：{page["line2"]}（请控制在8字以内）')
    if not fits(l1, page['line1']):
        raise ValueError(f'封面第一行太长：{page["line1"]}（请控制在11字以内）')
    rel = out.relative_to(root).as_posix()
    if v2 and page.get('cover_style') == 'cutout':
        # 抠图封面：整幅图压暗偏旧色当底，人物抠图放大压在上面，加强调色光边（原版「帝国皇子」那种）
        import layouts_v2 as V
        bg = Image.open(out).convert('RGB')
        from PIL import ImageEnhance, ImageOps
        if page.get('cover_bg'):                       # 底图换一张，免得和抠出的人物重影
            b = page['cover_bg']; bp, (bw_, bh_), _ = img_meta(b, root)
            bim = Image.open(bp).convert('RGB')
            if b.get('crop'):
                c = b['crop']; bim = bim.crop((round(c[0] * bw_), round(c[1] * bh_), round(c[2] * bw_), round(c[3] * bh_)))
            bg = ImageOps.fit(bim, (W, H), Image.LANCZOS, centering=tuple(b.get('focus', [0.5, 0.5])))
        g = ImageOps.colorize(bg.convert('L'), '#120c08', '#bfa78a')
        g = ImageEnhance.Brightness(g).enhance(0.55)
        g.save(out, quality=94)
        cut = page.get('cut') or spec.get('cut')
        ce, alpha = V.place_cutout({**spec, 'cut': cut, 'max_scale': 1.6}, root, work, page.get('cut_side', 'center'),
                                   page.get('cut_h', 0.86), page.get('cut_w', 0.86), bottom=1.0)
        ce['soft_shadow'] = {'color': accent, 'offset': [0, 0], 'blur': 26, 'opacity': 0.95}
        ce['outline'] = accent; ce['outline_width'] = 11
        ce['role'] = 'background'; ce['cover_figure'] = True    # 封面标题本来就压在人物下半身上；人脸在上半部，标题碰不到
        return {'layout': 'cover', 'background': '#000000', 'skeleton': '封面·抠图光边', 'watermark': False,
                'border': accent if page.get('border', False) else None, 'border_width': page.get('border_width', 20),
                'elements': [{'kind': 'image', 'path': rel, 'source_id': sid(spec), 'box': [0, 0, 1, 1], 'fit': 'cover',
                              'role': 'background', 'darken': 0.0, 'face_boxes': [], 'face_detection_method': 'manual-verified'},
                             {**ce, 'coverage': True}, l1, l2]}
    return {'layout': 'cover', 'background': '#000000', 'skeleton': '封面·人物大脸', 'watermark': False,
            'border': accent if page.get('border', True) else None, 'border_width': page.get('border_width', 20 if ctx.get('style') == 'v2' else 5),
            'elements': [{'kind': 'image', 'path': rel, 'source_id': sid(spec), 'box': [0, 0, 1, 1], 'fit': 'cover',
                          'role': 'background', 'darken': 0.04, 'face_boxes': [], 'face_detection_method': 'manual-verified'},
                         l1, l2]}


# ---------------------------------------------------------------- 主流程

def blank_ratio(path):
    with Image.open(path) as im:
        a = np.asarray(im.convert('L').resize((360, 480)), dtype=float)
    tiles = [a[y:y + 30, x:x + 30] for y in range(0, 480, 30) for x in range(0, 360, 30)]
    return round(sum(v.max() - v.min() < 18 for v in tiles) / len(tiles) * 100)


def orphans(report):
    bad = []
    for t in report.get('text', []):
        g = t.get('glyphs') or []
        rows = {}
        for ch in g:
            rows.setdefault(ch['line'], []).append(ch['char'])
        for v in rows.values():
            if 0 < visible_len(''.join(v)) < 2 and len(rows) > 1:
                bad.append(''.join(v))
    return bad


BANNED = ['众所周知', '不难发现', '由此可见', '值得一提的是', '一时间', '轰动一时', '让人不禁', '说白了', '综上所述']
STOP = set('的了是在和与也都就还又这那一个我们你他她它们之其而及或被把将对从到为以于上下中里外后前时'.split()) | {'一个', '这个', '那个', '没有', '自己', '他们', '她们', '我们', '什么', '因为', '所以', '可是', '但是', '后来', '这样', '一条', '一位'}


def keywords(text):
    t = re.sub(r'\[\[|\]\]|\n', '', text)
    ws = jieba.lcut(t) if jieba else re.findall(r'[\u4e00-\u9fff]{2}', t)
    return {w for w in ws if len(w) >= 2 and w not in STOP and not re.fullmatch(r'[\d\W]+', w)}


def copy_checks(content):
    """文案检查：只提醒，不拦截。规则见 references/文案公式.md。"""
    out, pages = [], content['pages']
    if not content.get('thesis'):
        out.append('文案：内容.json 没有写 thesis（全篇论点）。先写一句「人们以为A，其实B」，每页都为它服务')
    alltext = ''
    for i, p in enumerate(pages, 1):
        texts = [p.get(k, '') for k in ('title', 'body', 'note', 'emphasis', 'foot', 'line1', 'line2')]
        alltext += ''.join(texts)
        for w in BANNED:
            if any(w in t for t in texts):
                out.append(f'文案 {i:02d}：「{w}」是解说腔，换成具体的说法')
        if i == 1:
            continue
        if p.get('body') and not re.search(r'\d|「|《', p.get('body', '') + p.get('foot', '') + p.get('note', '')):
            out.append(f'文案 {i:02d}：正文没有看得见的锚点（数字、日期、「原话」或《书名》），容易变成空泛的解说')
        emp = p.get('emphasis', '')
        if emp:
            n = visible_len(emp)
            if n > 16:
                out.append(f'文案 {i:02d}：强调句{n}字，太长；强调句写一个判断，4–14字')
            tk, ek = keywords(p.get('title', '')), keywords(emp)
            if ek and len(ek & tk) / len(ek) >= 0.6:
                out.append(f'文案 {i:02d}：强调句在重复标题，换成转折或判断')
    if sum(1 for p in pages if p.get('note')) > 5:
        out.append('文案：底色文字超过5处。它只用来突出原话、关键数字或证据边界，多了就不醒目')
    narr = re.sub(r'「[^」]*」', '', alltext)          # 引号里是别人的原话，不算作者的「我」
    if narr.count('我') - narr.count('我们') > 2:
        out.append('文案：全篇「我」超过2次。图文里「我」只用在一两处判断上')
    if len(pages) > 2:
        head = keywords(pages[0].get('line1', '') + pages[0].get('line2', '') + content.get('thesis', ''))
        last = pages[-1]
        tail = keywords(''.join(last.get(k, '') for k in ('title', 'body', 'emphasis', 'foot')))
        if head and not (head & tail):
            out.append('文案：最后一页没有回扣封面或论点里的物件、词。结尾要把开头的东西拿回来，换个意思')
    return out


def preview(paths, out):
    tw, th, cols = 460, 613, 4
    rows = math.ceil(len(paths) / cols)
    g = Image.new('RGB', (cols * (tw + 14) + 14, rows * (th + 44) + 14), '#e6e6e6'); d = ImageDraw.Draw(g)
    f = ImageFont.truetype(str(RD.FONT_ROOT / 'NotoSansSC[wght].ttf'), 26)
    for k, p in enumerate(paths):
        x, y = 14 + (k % cols) * (tw + 14), 14 + (k // cols) * (th + 44)
        d.text((x, y), '封面' if p.name == 'p01.png' else p.name[1:3], fill='#222', font=f)
        g.paste(Image.open(p).convert('RGB').resize((tw, th)), (x, y + 34))
    g.save(out, quality=88)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('content', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--pages', help='只排这几张，如 2,5（1是封面）')
    ap.add_argument('--capacity', action='store_true', help='只打印各文字栏每行大约能放几个字')
    a = ap.parse_args()
    content = json.loads(a.content.read_text(encoding='utf-8'))
    root = a.content.resolve().parent
    accent = content.get('accent', '#5AA9E6')
    CFG['accent'] = accent
    if a.capacity:
        for name, w in [('窄栏（右抠图/左大图/整版底/收尾）', 0.40), ('中栏（双图右下）', 0.444), ('宽栏（横幅/物件）', FULL)]:
            print(name, {r: int(w * W // PREF[r]) for r in PREF})
        return
    out = (a.out or root / '成品').resolve(); out.mkdir(parents=True, exist_ok=True)
    work = root / '_build'
    style = content.get('style') or ('v2' if any(p.get('layout') in V2.LAYOUTS for p in content['pages']) else 'v1')
    ctx = {'accent': accent, 'root': root, 'protect': content.get('protect', []), 'work': work, 'style': style,
           'max_arrows': content.get('max_arrows', 6), 'topic': content.get('topic', ''), 'fx': content.get('fx', {})}
    if style == 'v2' and content.get('accent2'):
        # 第二强调色：默认关。和素材色调不搭会很突兀（09 慈禧加黄色被否），只在 内容.json 写了 "accent2" 时启用
        from PIL import ImageColor
        r_, g_, b_ = ImageColor.getrgb(accent)[:3]
        yellowish = r_ > 200 and g_ > 170 and b_ < 140
        ctx['accent2'] = content['accent2'] if isinstance(content.get('accent2'), str) else ('#FF6FAE' if yellowish else '#FFD84D')
    for k in ('stack_rate', 'ghost_rate', 'title_mid_rate', 'accent2_rate'):      # 全篇比例，可在 内容.json 顶层覆盖
        if k in content:
            ctx[k] = content[k]
    config = {'tone': '暗', 'accent': accent, 'background': '#000000', 'account_name': content.get('account', '账号名'),
              'watermark_text': content.get('account', '账号名'), 'watermark_style': 'neutral', 'bookmark': False,
              'cover_only': False, 'background_profile': 'mixed-v2', 'visual_profile': 'v7-richness',
              'text_color_profile': 'v7.4-alternation', 'avoid_watermark_overlap': True,
              'require_face_every_page': content.get('require_face_every_page', True)}
    if content.get('title_font'):
        # 标题展示字体：字库放在选题目录里（相对路径），只用官方渠道、允许商用的字体
        config['fonts'] = {**config.get('fonts', {}), 'title-display': {'path': content['title_font'], 'weight': None}}
        CFG['fonts'] = config['fonts']                 # 断行测量也要用同一个字体
        from io_paths import set_assets_root
        set_assets_root(root)
    pages = content['pages']
    only = [int(x) for x in a.pages.split(',')] if a.pages else list(range(1, len(pages) + 1))
    script = {'schema_version': 1, 'built_by': 'build.py', 'topic': content.get('topic', ''), 'tone': '暗', 'mode': 'production',
              'config': config, 'delivery': {'main_cover': 'D', 'size': [W, H]}, 'pages': []}
    summary, warnings = [], []
    for i in only:
        page = pages[i - 1]
        factor, rr = 1.0, None
        for attempt in range(4):
            try:
                p, info = build_page(i, page, ctx, factor)
            except ValueError as err:
                p = None
                if page.get('layout') == '横幅' and page.get('hero') and not page.get('backdrop'):
                    for band in (0.36, 0.32, 0.28):     # 横幅压低一点，把高度让给文字
                        try:
                            p, info = build_page(i, {**page, 'band': band}, ctx, factor)
                            break
                        except ValueError:
                            continue
                if p is None:
                    raise SystemExit(f'第{i}张排不下：{err}')
            tmp = work / f'P{i:02d}'; tmp.mkdir(parents=True, exist_ok=True)
            s = tmp / '页面脚本.json'
            s.write_text(json.dumps({**script, 'pages': [p]}, ensure_ascii=False, indent=2),encoding='utf-8')
            try:
                rr = RD.render(s, tmp, assets_root=root)[0]
            except ValueError as err:
                if '碰撞' not in str(err) or attempt == 3:
                    raise ValueError(f'第{i}张：{err}') from err
                ctx.setdefault('shrink', {})[i] = ctx.get('shrink', {}).get(i, 0) + 1   # 图片缩小一点再排
                continue
            mismatch = [t['text'][:12].replace('\n', '|') for t in rr.get('text', []) if t['lines'] != t['text'].count('\n') + 1]
            if not mismatch:
                break
            factor -= 0.04          # 渲染器多折了一行：按更窄的宽度重断
        else:
            warnings.append(f'{i:02d} 断行与预期不一致：{mismatch}')
        shutil.copy2(tmp / 'p01.png', out / f'p{i:02d}.png')
        script['pages'].append(p)
        ob = orphans(rr)
        if ob:
            warnings.append(f'{i:02d} 有孤字行：{ob}')
        for t in rr.get('text', []):
            b = t.get('ink_bounds')
            if b and (b[0] < 70 or b[2] > 1370 or b[3] > 1880):
                warnings.append(f'{i:02d} 文字贴边：{t["text"][:10]}')
        if i > 1 and not any(e.get('face_boxes') for e in p['elements'] if e.get('kind') in ('image', 'dark_backdrop')):
            warnings.append(f'{i:02d} 这页没有标人脸框：本风格每页至少一张有人脸的图')
        chars = sum(visible_len(e['text']) for e in p['elements'] if e.get('kind') == 'text' and e.get('text_role') != 'heading')
        if i > 1 and chars < 55:
            warnings.append(f'{i:02d} 正文太少（{chars}字）：本风格每页正文约60–110字，太少会显得空')
        for c in info.get('columns', []):
            if c['leftover'] > 0.14:
                warnings.append(f'{i:02d} 有一栏下方空了{c["leftover"] * 100:.0f}%：加一句正文，或换文字栏更小的版式')
        blank = blank_ratio(out / f'p{i:02d}.png')
        summary.append({'page': i, **info, 'blank_tiles': blank})
        print(f'{i:02d} {info["layout"]:<4} 空格子{blank}%', flush=True)
    # 只重排部分页时，其余页沿用上次的页面脚本；合并渲染报告，供 check_all / package 使用
    if a.pages and (out / '页面脚本.json').exists():
        old = json.loads((out / '页面脚本.json').read_text(encoding='utf-8'))
        merged = {k + 1: pg for k, pg in enumerate(old.get('pages', []))}
        merged.update({i: pg for i, pg in zip(only, script['pages'])})
        script['pages'] = [merged[k] for k in sorted(merged)]
    (out / '页面脚本.json').write_text(json.dumps(script, ensure_ascii=False, indent=2),encoding='utf-8')
    target = root / '页面脚本.json'          # package.py 从选题目录读取；不覆盖别人手写的页面脚本
    if not target.exists() or json.loads(target.read_text(encoding='utf-8')).get('built_by') == 'build.py':
        target.write_text(json.dumps(script, ensure_ascii=False, indent=2),encoding='utf-8')
    else:
        warnings.append('选题目录里已有手写的页面脚本.json，没有覆盖；新脚本在输出目录里')
    reports = []
    for k in range(1, len(script['pages']) + 1):
        rp = work / f'P{k:02d}' / 'render-report.json'
        if rp.exists():
            r = json.loads(rp.read_text(encoding='utf-8'))[0]; r['page'] = k; reports.append(r)
    (out / 'render-report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2),encoding='utf-8')
    warnings += list(dict.fromkeys(ctx.get('warnings', [])))
    warnings += copy_checks(content)
    (out / '排版报告.json').write_text(json.dumps({'pages': summary, 'warnings': warnings}, ensure_ascii=False, indent=2),encoding='utf-8')
    inner = [r['blank_tiles'] for r in summary if r['page'] > 1]
    if inner:
        print(f'内页平均空格子 {sum(inner) / len(inner):.1f}%（目标≤22%）')
    preview(sorted(out.glob('p[0-9][0-9].png')), out / '全套预览.jpg')
    for w_ in warnings:
        print('注意', w_)
    print('文案自检：每页的强调句删掉后，信息会不会变少？不会，就说明它只是小结，需要改。')
    print('完成：', out)


if __name__ == '__main__':
    main()
