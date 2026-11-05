"""原版风版式（v2）：照对标账号的页面拆出来的六种骨架。

和旧版式（毛边框单图 + 毛笔大字）的区别：
- 标题：强调色粗黑体，左上角，一到两行；
- 正文：白色宋体，字距放宽，分成两小段；
- 强调句：强调色粗黑体，比正文大一号半，不再用毛笔大字；
- 图：照片不加边框；人物抠图压在照片上，或者从页面底边、侧边长出来；椭圆头像；整版暗底；
- 文字自动绕开抠图的轮廓排（逐行算可用宽度），不靠固定栏宽；
- 强调句旁边画一根强调色手绘箭头，指向人物（全篇最多 6 根）。

由 build.py 调用：build_page(i, page, ctx, T)，T 是 build 模块，共用断行和测量函数。
"""
from pathlib import Path
import copy, hashlib, math, re
import numpy as np
from PIL import Image, ImageDraw

import render as RD
from 保脸裁切 import local_faces, safe_focus
from 图像等比 import fit_geometry

W, H = 1440, 1920
L, R = 0.056, 0.944
TOP = 0.036
BOTTOM = 0.955
SC = 4                                   # 占位网格：1/4 分辨率
GW, GH = W // SC, H // SC
MARGIN = 20                              # 文字离图的最小水平距离（像素）；原版字和图贴得很紧
VPAD = 14                                # 竖直方向留的余量（像素）
MINW = 0.40                              # 文字栏最窄宽度（约10字）；更窄就把文字挪到图下面，不挤成窄条
WHITE = '#FFFFFF'
TEXT_SHADOW = {'color': '#000000', 'offset': [4, 6], 'blur': 7, 'opacity': 0.75}
# 标题、强调句：黑色硬投影（45° 挤出），像原版那样像贴纸一样立起来，不用柔光
HARD_SHADOW = {'effect': '3d', 'depth': 9, 'bold': 0, 'shadow_color': '#000000',
               'soft_shadow': {'color': '#000000', 'offset': [6, 9], 'blur': 6, 'opacity': 0.55}}

# 字号（1440 宽下的像素）：(最小, 首选, 最大)，以及每档步长
SIZE = {'title': (84, 96, 132), 'body': (52, 57, 58), 'foot': (52, 57, 58),
        'emphasis': (60, 72, 104), 'note': (48, 48, 48)}
STEP = {'title': 6, 'body': 2, 'foot': 2, 'emphasis': 6, 'note': 0}
GAP = {'body': 0.020, 'foot': 0.020, 'note': 0.018, 'emphasis': 0.028, 'title': 0.030}

LAYOUTS = ['拼贴', '大图', '图文叠', '立像', '圆像', '渐隐', '宽幅', '错落', '手排']


# ---------------------------------------------------------------- 文字

def tx(role, text, x, y, w, size, accent, align='left', fill=None):
    base = {'kind': 'text', 'text': text, 'box': [x, y, w, 0.1], 'size': size, 'tight_punctuation': 'all',
            'text_role': role, 'align': align}
    if role == 'title':
        base.update(font='title-display', fill=fill or accent, lineheight=round(size * 1.22), spacing=3,
                    text_role='heading', callout=True, **HARD_SHADOW)
    elif role == 'emphasis':
        base.update(font='title-display', fill=fill or accent, lineheight=round(size * 1.3), spacing=2,
                    callout=True, **HARD_SHADOW)
    elif role == 'note' and fill == 'plain':
        # 引语式：强调色粗体字，不加底条（原版常这样放原话）
        base.update(font='sans-bold', fill=accent, lineheight=round(size * 1.45), spacing=1, soft_shadow=TEXT_SHADOW)
    elif role == 'note':
        from PIL import ImageColor
        r, g, b = ImageColor.getrgb(accent)[:3]
        ink = '#111111' if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55 else WHITE
        base.update(font='sans-bold', fill=ink, bg=accent, lineheight=round(size * 1.5), spacing=0)
    else:
        base.update(font='serif-semibold', fill=WHITE, lineheight=round(size * 1.47), spacing=round(size * 0.07),
                    soft_shadow=TEXT_SHADOW, text_role=role)
    return base


def measure(e, T, protect):
    """断行并算出框高。作者手动断的行放不下时先缩字号。"""
    role = e['text_role'] if e['text_role'] != 'heading' else 'title'
    lo = SIZE[role][0]
    raw = e['text']
    if '\n' in raw:
        ratio = e['lineheight'] / e['size']
        while e['size'] > lo and not all(T.fits({**e, 'box': [0, 0, e['box'][2] * 0.95, 1]}, ln) for ln in raw.split('\n')):
            e['size'] -= max(2, STEP[role])
            e['lineheight'] = round(e['size'] * ratio)
    w = e['box'][2]
    e['box'][2] = w * 0.97
    e['text'] = T.wrap(e, raw, protect)
    e['box'][2] = w
    lines = e['text'].count('\n') + 1
    e['box'][3] = round(lines * e['lineheight'] / H + 10 / H, 4)
    return e


def ink_bounds(e, cfg):
    audit = []
    canvas = Image.new('RGBA', (W, H))
    plain = {k: v for k, v in e.items() if k not in ('soft_shadow', 'glow', 'effect')}
    RD.draw_text(canvas, plain, cfg, W, H, audit)
    return audit[-1].get('ink_bounds')


def paragraphs(text):
    """正文拆成两小段：在句号处断，不断在引号里面。已经用空行分段的照原样。"""
    if not text:
        return []
    if '\n\n' in text:
        return [p.strip() for p in text.split('\n\n') if p.strip()]
    ends, depth = [], 0
    for k, ch in enumerate(text):
        depth += ch in '「“'
        depth -= ch in '」”'
        if ch in '。！？' and depth <= 0 and k < len(text) - 1:
            ends.append(k + 1)
    n = len(re.sub(r'\s', '', text))
    if not ends or n < 58:
        return [text]
    cut = min(ends, key=lambda k: abs(k - len(text) * 0.5))
    a, b = text[:cut].strip(), text[cut:].strip()
    return [a, b] if len(a) >= 14 and len(b) >= 14 else [text]


# ---------------------------------------------------------------- 占位网格

class Occ:
    """记录页面上哪些地方已经有图（不透明像素），文字逐行避开。"""

    def __init__(self):
        self.g = np.zeros((GH, GW), bool)

    def add_box(self, box):
        x, y, w, h = box
        self.g[max(0, int(y * GH)):min(GH, math.ceil((y + h) * GH)), max(0, int(x * GW)):min(GW, math.ceil((x + w) * GW))] = True

    def add_alpha(self, alpha, box):
        if alpha is None:
            return self.add_box(box)
        x, y, w, h = box
        pw, ph = max(1, round(w * GW)), max(1, round(h * GH))
        a = np.asarray(alpha.resize((pw, ph))) > 90
        x0, y0 = round(x * GW), round(y * GH)
        sub = self.g[y0:y0 + ph, x0:x0 + pw]
        sub |= a[:sub.shape[0], :sub.shape[1]]

    def add_ellipse(self, box):
        x, y, w, h = box
        m = Image.new('L', (max(1, round(w * GW)), max(1, round(h * GH))))
        ImageDraw.Draw(m).ellipse((0, 0, m.width - 1, m.height - 1), fill=255)
        self.add_alpha(m, box)

    def rows(self, ya, yb):
        return slice(max(0, int((ya * H - VPAD) / SC)), min(GH, math.ceil((yb * H + VPAD) / SC)))

    def free_right(self, x, ya, yb, limit):
        """从 x 往右，到第一个有图的地方为止（再减去 MARGIN）。返回右边界（页面比例）。"""
        c0, c1 = int(x * GW), math.ceil(limit * GW)
        hit = self.g[self.rows(ya, yb), c0:c1].any(axis=0)
        if not hit.any():
            return limit
        return max(x, ((c0 + int(np.argmax(hit))) * SC - MARGIN) / W)

    def free_left(self, xr, ya, yb, limit):
        c0, c1 = int(limit * GW), math.ceil(xr * GW)
        hit = self.g[self.rows(ya, yb), c0:c1].any(axis=0)
        if not hit.any():
            return limit
        last = c0 + len(hit) - 1 - int(np.argmax(hit[::-1]))
        return min(xr, ((last + 1) * SC + MARGIN) / W)

    def add_photo(self, spec, root, box, faces_pad=0.02):
        """照片只把亮处和人脸当障碍：暗处（背景、深色衣服）允许文字压上去，像原版那样图文交叠。"""
        from PIL import ImageFilter, ImageOps
        try:
            _, win, (tw, th) = cover_window(spec, root, box)
            with Image.open(root / spec['path']) as im:
                im = im.convert('L')
                c = spec.get('crop', [0, 0, 1, 1])
                ox, oy = c[0] * im.width, c[1] * im.height
                x0, y0, x1, y1 = win
                im = im.crop((round(ox + x0), round(oy + y0), round(ox + x1), round(oy + y1)))
            pw, ph = max(1, round(box[2] * GW)), max(1, round(box[3] * GH))
            lum = im.resize((pw, ph)).filter(ImageFilter.GaussianBlur(3))
            m = Image.fromarray(((np.asarray(lum) > spec.get('dark_cut', 70)) * 255).astype('uint8')).filter(ImageFilter.MaxFilter(5))
            self.add_alpha(m, box)
            # 照片四周留一圈：文字不贴着照片边缘
            x, y, w, h = box
            edge = Image.new('L', (pw, ph), 0); d = ImageDraw.Draw(edge); d.rectangle((0, 0, pw - 1, ph - 1), outline=255, width=3)
            self.add_alpha(edge, box)
            for f in face_boxes_on_page(spec, root, box):
                self.add_box([f[0] - faces_pad, f[1] - faces_pad, f[2] + 2 * faces_pad, f[3] + 2 * faces_pad])
        except Exception:
            self.add_box(box)

    def blocked(self, box):
        x, y, w, h = box
        return self.g[self.rows(y, y + h), max(0, int(x * GW)):min(GW, math.ceil((x + w) * GW))].any()


# ---------------------------------------------------------------- 图片

def spec_faces(spec):
    faces = spec.get('face', [])
    if faces and isinstance(faces[0], (int, float)):
        faces = [faces]
    return faces


def cut_bbox(spec, root):
    src = spec.get('cut') or spec['path']
    with Image.open(root / src) as im:
        bb = im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        return im.size, bb


def cut_source(spec, root, work):
    """抠图收紧到不透明范围，缓存在 _build/cut/。人脸框跟着换算。"""
    src = spec.get('cut') or spec['path']
    p = root / src
    im = Image.open(p)
    if im.mode != 'RGBA' or im.getchannel('A').getextrema()[0] == 255:
        raise ValueError(f'{src} 不是透明抠图；需要抠图的版式请在图片里写 "cut": "assets/cut/xxx-cut.png"')
    a = im.getchannel('A')
    bb = a.point(lambda v: 255 if v > 40 else 0).getbbox()
    iw, ih = im.size
    out = work / 'cut' / (Path(src).stem + '-tight.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    tight = im.crop(bb)
    if not out.exists() or Image.open(out).size != tight.size:
        tight.save(out)
    faces = []
    for fx, fy, fw, fh in spec_faces(spec):
        faces.append([round((fx * iw - bb[0]) / tight.width, 4), round((fy * ih - bb[1]) / tight.height, 4),
                      round(fw * iw / tight.width, 4), round(fh * ih / tight.height, 4)])
    arr = np.asarray(tight.getchannel('A'))
    cut_bottom = (arr[-3:] > 128).mean() > 0.10
    return out, tight, faces, cut_bottom


def place_rect(spec, root, side, height, max_w, bottom=None, hero=True):
    """没有抠图时：照片按原比例贴着页面底边和侧边放（出血），不加边框。"""
    with Image.open(root / spec['path']) as im:
        iw, ih = im.size
    c = spec.get('crop', [0, 0, 1, 1])
    cw, ch = (c[2] - c[0]) * iw, (c[3] - c[1]) * ih
    h = min(height * H, ch * spec.get('max_scale', 1.25))
    w = h * cw / ch
    if w > max_w * W:
        w = max_w * W; h = w * ch / cw
    bottom = 1.0 if bottom is None else bottom
    x = W - w if side == 'right' else 0 if side == 'left' else (W - w) / 2
    box = [round(x / W, 4), round((bottom * H - h) / H, 4), round(w / W, 4), round(h / H, 4)]
    return photo(spec, box, hero=hero), None


def place_cutout(spec, root, work, side, height, max_w, bottom=None, top=None, edge=None, hero=True):
    """抠图贴边放：side='right' 贴右边，'left' 贴左边。底边是裁切边（半身像）就贴到页面底，
    像从下面长出来；全身像离底边留一点。超出页面的部分预先裁掉（出血）。没有抠图就用照片贴边。"""
    if not spec.get('cut'):
        with Image.open(root / spec['path']) as im:
            transparent = im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] < 255
        if not transparent:
            return place_rect(spec, root, side, height, max_w, bottom, hero)
    path, tight, faces, cut_bottom = cut_source(spec, root, work)
    tw, th = tight.size
    s = min(height * H / th, max_w * W / tw, spec.get('max_scale', 1.25))   # 放大不超过1.25倍，免得糊
    w, h = tw * s, th * s
    if bottom is None:
        bottom = 1.0 if cut_bottom else 0.985
    y = bottom * H - h
    if top is not None and y > top * H and cut_bottom:
        y = top * H
    edge = (1.0 if side == 'right' else 0.0) if edge is None else edge
    x = edge * W - w if side == 'right' else edge * W
    if side == 'center':
        x = (W - w) / 2
    # 出血：页面外的部分裁掉（左/上不能画到负坐标）
    vx0, vy0, vx1, vy1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    sx0, sy0, sx1, sy1 = (vx0 - x) / s, (vy0 - y) / s, (vx1 - x) / s, (vy1 - y) / s
    if (sx0, sy0, sx1, sy1) != (0, 0, tw, th) and (sx1 - sx0 < tw - 0.5 or sy1 - sy0 < th - 0.5):
        crop = tuple(round(v) for v in (sx0, sy0, sx1, sy1))
        key = hashlib.md5(repr(crop).encode()).hexdigest()[:6]
        bled = path.with_name(path.stem + f'-b{key}.png')
        if not bled.exists():
            tight.crop(crop).save(bled)
        faces = [[round((fx * tw - crop[0]) / (crop[2] - crop[0]), 4), round((fy * th - crop[1]) / (crop[3] - crop[1]), 4),
                  round(fw * tw / (crop[2] - crop[0]), 4), round(fh * th / (crop[3] - crop[1]), 4)] for fx, fy, fw, fh in faces]
        faces = [f for f in faces if f[0] >= 0 and f[1] >= 0 and f[0] + f[2] <= 1 and f[1] + f[3] <= 1]
        path, tight = bled, tight.crop(crop)
    box = [round(vx0 / W, 4), round(vy0 / H, 4), round((vx1 - vx0) / W, 4), round((vy1 - vy0) / H, 4)]
    e = {'kind': 'image', 'path': path.relative_to(root).as_posix(), 'box': box, 'fit': 'contain', 'role': 'foreground',
         'source_id': spec.get('id') or Path(spec['path']).stem, 'hero': hero, 'hero_form': 'cutout', 'major_image': hero,
         'soft_shadow': {'color': '#000000', 'offset': [10, 12], 'blur': 16, 'opacity': 0.55}, 'color_source': True,
         'face_boxes': faces, 'face_detection_method': spec.get('face_method', 'manual-verified'),
         'face_verified': bool(faces), 'face_review': '人工目检'}
    if spec.get('label'):
        e['label_text'] = spec['label']
    # 局部放大要用：原图（spec['path']，和抠图同尺寸）上的点怎么换算到页面
    _, bb = cut_bbox(spec, root)
    e['_src_path'] = spec['path']
    e['_map'] = {'x': x, 'y': y, 's': s, 'bb': [bb[0], bb[1]]}
    return e, tight.getchannel('A')


def cover_window(spec, root, box):
    """照片按 cover 放进框时，源图的哪一块会露出来（和渲染器用同一套保脸算法）。"""
    p = root / spec['path']
    with Image.open(p) as im:
        size = im.size
    e = {'crop': spec.get('crop'), 'face_boxes': spec_faces(spec)}
    if not e['crop']:
        e.pop('crop')
    crop = spec.get('crop', [0, 0, 1, 1])
    cs = (round((crop[2] - crop[0]) * size[0]), round((crop[3] - crop[1]) * size[1]))
    faces, _ = local_faces(e, size, cs)
    tw, th = max(1, round(box[2] * W)), max(1, round(box[3] * H))
    focus, info = safe_focus(cs, (tw, th), faces, tuple(spec.get('focus', [0.5, 0.4])))
    return faces, info['source_crop_box'], (tw, th)


def photo(spec, box, hero=True, oval=False):
    e = {'kind': 'image', 'path': spec['path'], 'box': [round(v, 4) for v in box], 'fit': 'cover',
         'source_id': spec.get('id') or Path(spec['path']).stem, 'effects': ['circle'] if oval else [],
         'focus': spec.get('focus', [0.5, 0.4]), 'major_image': hero, 'hero': hero, 'color_source': True,
         'face_boxes': spec_faces(spec), 'face_detection_method': spec.get('face_method', 'manual-verified'),
         'face_verified': bool(spec_faces(spec)), 'face_review': '人工目检'}
    if hero:
        e['hero_form'] = 'oval' if oval else 'rectangle'
    if spec.get('crop'):
        e['crop'] = spec['crop']
    if spec.get('label'):
        e['label_text'] = spec['label']
    e['_src_path'] = spec['path']
    return e


def backdrop(spec, darken):
    e = {'kind': 'dark_backdrop', 'path': spec['path'], 'box': [0, 0, 1, 1], 'fit': 'cover',
         'source_id': spec.get('id') or Path(spec['path']).stem, 'darken': spec.get('darken', darken),
         'role': 'background', 'fade_fraction': 0, 'cover_only': True, 'focus': spec.get('focus', [0.5, 0.4]),
         'color_source': True, 'face_boxes': spec_faces(spec), 'face_detection_method': spec.get('face_method', 'manual-verified')}
    if spec.get('crop'):
        e['crop'] = spec['crop']
    e['_src_path'] = spec['path']
    return e


def face_boxes_on_page(spec, root, box):
    """cover 照片/整版底上的人脸，换算成页面坐标（文字要避开）。"""
    faces, win, (tw, th) = cover_window(spec, root, box)
    x0, y0, x1, y1 = win
    s = tw / (x1 - x0)
    out = []
    for f in faces:
        a, b, c, d = f['box']
        out.append([box[0] + (a - x0) * s / W, box[1] + (b - y0) * s / H, (c - a) * s / W, (d - b) * s / H])
    return out


# ---------------------------------------------------------------- 逐页变化

def vary(i, page, ctx):
    """每页随机一点：标题字号/对齐/颜色、强调句字号/对齐、图片描边。同一选题每次结果一样（按页码和选题取种子）。
    原版不是一套模板到底，字号、位置、颜色会跟着素材跳。页面里写了的值优先。"""
    import random
    rng = random.Random(f"{ctx.get('topic', '')}-{i}")
    t = page.get('title', '')
    short = '\n' not in t and len(t) <= 6
    v = {
        'title_size': page.get('title_size') or (rng.choice([108, 116, 124, 128]) if short else rng.choice([88, 92, 96, 100])),
        'title_align': page.get('title_align') or rng.choices(['left', 'center', 'right'], [8, 1, 1 if short else 0])[0],
        'title_fill': WHITE if page.get('title_white', rng.random() < 0.2) else None,
        'emph_pref': page.get('emphasis_size') or rng.choice([64, 72, 80, 88, 96]),
        'emph_align': page.get('emphasis_align') or rng.choices(['left', 'right', 'center'], [6, 2, 2])[0],
        'emph_fill': WHITE if page.get('emphasis_white', rng.random() < 0.3) else None,
        'note_fill': 'plain' if page.get('note_plain', rng.random() < 0.4) else None,
        # 一半左右的页不放大字结论：强调句变成正文里一句强调色的话（原版多是这样）
        'emph_inline': page.get('emphasis_inline', rng.random() < 0.5),
        'side': page.get('side') or rng.choice(['left', 'right']),
        'ghost': page.get('ghost', rng.random() < ctx.get('ghost_rate', 0.45)),
        'emph_mid': page.get('emphasis_mid', rng.random() < 0.45),
        'title_mid': page.get('title_mid', rng.random() < ctx.get('title_mid_rate', 0.4)),
        'stack': rng.random() < ctx.get('stack_rate', 0.5),
        'stack_pos': rng.choices(['top', 'bottom', 'middle'], [45, 30, 25])[0],
        'jitter': [rng.uniform(-0.035, 0.035) for _ in range(4)],
    }
    # 第二强调色放在最后抽，免得改变前面已经定下的版式随机结果
    v['accent2_hl'] = page.get('accent2_hl', rng.random() < ctx.get('accent2_rate', 0.35))
    v['accent2_emph'] = page.get('accent2_emph', rng.random() < ctx.get('accent2_rate', 0.35) * 0.8)
    return v


def apply_fx(e, kind, k, ctx, page, accent):
    """图片描边：抠图加白色贴纸边或强调色发光；照片加强调色发光。全篇按 fx 设定，隔一张用一次，避免每张都一样。"""
    fx = {**ctx.get('fx', {}), **page.get('fx', {})}
    if e.get('no_fx'):
        return e
    style = fx.get(kind)
    if not style or (k + ctx.get('fx_phase', 0)) % fx.get('every', 2):
        return e
    glow = {'color': accent, 'offset': [0, 0], 'blur': 20, 'opacity': 0.95}
    if style == 'outline':
        e['outline'] = fx.get('outline_color', '#FFFFFF'); e['outline_width'] = fx.get('outline_width', 15)
    elif style == 'glow':
        e['soft_shadow'] = glow
    return e


# ---------------------------------------------------------------- 人名标签

LABEL_STYLE = {'black': ('#000000', WHITE), 'white': (WHITE, '#111111')}


def label_boxes_for(e, root):
    """图上可以放标签的位置（页面坐标），按优先顺序；同时给出这张图上的人脸框（标签要避开）。"""
    x, y, w, h = e['box']
    faces = []
    if e.get('role') == 'foreground':
        for fx, fy, fw, fh in e.get('face_boxes', []):
            faces.append([x + fx * w, y + fy * h, fw * w, fh * h])
        spots = [('l', y + h * 0.72), ('r', y + h * 0.72), ('l', y + h * 0.50), ('r', y + h * 0.50)]
    else:
        spec = {'path': e['path'], 'face': e.get('face_boxes', []), 'focus': e.get('focus', [0.5, 0.4])}
        if e.get('crop'):
            spec['crop'] = e['crop']
        try:
            faces = face_boxes_on_page(spec, root, e['box'])
        except Exception:
            faces = []
        spots = [('l', y + h - 0.032), ('r', y + h - 0.032), ('l', y + 0.012), ('r', y + 0.012)]
    return spots, faces


def place_labels(images, texts, root, accent, ctx):
    """给写了 label 的图配一个黑底白字的小标签（人名、物件名），贴在图的角上或人物身侧；避开文字、人脸和右下角署名。"""
    style = ctx.get('fx', {}).get('label', 'black')
    bg, ink = LABEL_STYLE.get(style, (accent, '#111111'))
    size = 32
    face_font = RD.font('sans-bold', size, {'accent': accent})
    out = []
    for e in images:
        txt = e.get('label_text')
        if not txt or e.get('kind') != 'image':
            continue
        tw = (face_font.getlength(txt) + len(txt) * 1 + 18) / W
        th = 44 / H
        spots, faces = label_boxes_for(e, root)
        x, y, w, h = e['box']
        for side, ly in spots:
            lx = x + 0.014 if side == 'l' else x + w - tw - 0.014
            lx = min(max(lx, 0.02), 0.98 - tw)
            ly = min(max(ly, 0.03), 0.94 - th)
            box = [lx, ly, tw, th]
            def hit(b):
                return box[0] < b[0] + b[2] and b[0] < box[0] + box[2] and box[1] < b[1] + b[3] and b[1] < box[1] + box[3]
            if any(hit(t['box']) for t in texts + out) or any(hit(f) for f in faces):
                continue
            if lx + tw > 0.86 and ly + th > 0.92:
                continue
            out.append({'kind': 'text', 'text': txt, 'box': [round(lx + 9 / W, 4), round(ly + 4 / H, 4), round(tw, 4), round(th, 4)],
                        'size': size, 'font': 'sans-bold', 'fill': ink, 'bg': bg, 'lineheight': 44, 'spacing': 1,
                        'tight_punctuation': 'all', 'text_role': 'label'})
            break
    return out


# ---------------------------------------------------------------- 上下堆叠

def place_stack(specs, by, bh, side, root, work):
    """上下堆叠：几张图挤在一条横跨整页的图带里，互相压叠；字整行排在图带的上方或下方。
    照片在一侧、人物抠图在另一侧并压住照片一角（人物底边贴图带底边）；第二张照片错开压在第一张上。
    返回 [(类型, 元素, 附加)]，类型同拼贴：alpha（抠图）/photo/box。"""
    out = []
    other = 'left' if side == 'right' else 'right'
    rects = [sp for sp in specs if (sp.get('as') or ('cut' if sp.get('cut') else 'rect')) == 'rect']
    cuts = [sp for sp in specs if sp.get('cut')]
    ovals = [sp for sp in specs if sp.get('as') == 'oval']
    def asp_of(sp):
        with Image.open(root / sp['path']) as im_:
            iw, ih = im_.size
        c = sp.get('crop', [0, 0, 1, 1])
        return (c[2] - c[0]) * iw / ((c[3] - c[1]) * ih)
    cut_w = 0.0
    only_cut = not rects and not ovals
    for k, sp in enumerate(cuts[:1]):
        # 图带里的人物不超过图带高度（拼贴预先放大过的 h 不用），只有人物时放正中，免得字又排到旁边
        ch = min(sp.get('h', bh * 1.02), bh * 1.05)
        ce, alpha = place_cutout(sp, root, work, 'center' if only_cut else other, ch, min(sp.get('w', 0.52), 0.6),
                                 bottom=min(1.0, by + bh), hero=True, edge=sp.get('edge'))
        out.append(('alpha', ce, alpha)); cut_w = ce['box'][2]
    for k, sp in enumerate(rects[:2]):
        a = asp_of(sp)
        if k == 0:
            h = min(sp.get('h', 1), bh * (0.86 if cut_w else 0.9)); w = min(max(sp.get('w', 0), 0.72 if cut_w else 0.80), h * H * a / W)
            h = min(h, w * W / a / H)
            x = 0.035 if side == 'left' else 1 - w - 0.035
            if cut_w and w < 1 - cut_w - 0.035:        # 照片和人物之间不留缝：照片往人物那边伸，被人物压住一角
                x = 0.035 if side == 'left' else 1 - w - 0.035
            y = by + (bh - h) * 0.25
        else:
            h = min(sp.get('h', 1), bh * 0.62); w = min(0.48, h * H * a / W); h = min(h, w * W / a / H)
            first = next(e for t_, e, _ in out if t_ != 'alpha')
            fx, fy, fw, fh = first['box']
            x = fx + fw - w * 0.25 if side == 'left' else fx - w * 0.75
            x = min(max(x, 0.0), 1 - w)
            y = by + bh - h
        pe = photo(sp, [round(x, 4), round(y, 4), round(w, 4), round(h, 4)], hero=not out)
        out.append(('photo' if sp.get('overlay', True) else 'box', pe, sp))
    for sp in ovals[:1]:
        ow = sp.get('w', 0.30); oh = ow * W * 1.25 / H
        ox = 1 - ow - 0.04 if other == 'right' else 0.04
        pe = photo(sp, [round(ox, 4), round(by, 4), round(ow, 4), round(oh, 4)], hero=False, oval=True)
        out.append(('ellipse', pe, None))
    # 人物压在照片上时别挡住照片里的人脸：挡到就把照片往外让
    cut_boxes = [e['box'] for t_, e, _ in out if t_ == 'alpha']
    for t_, pe, sp in out:
        if t_ not in ('photo', 'box') or not cut_boxes:
            continue
        try:
            spec = {'path': pe['path'], 'face': pe.get('face_boxes', []), 'focus': pe.get('focus', [0.5, 0.4])}
            if pe.get('crop'):
                spec['crop'] = pe['crop']
            for _ in range(12):
                fs = face_boxes_on_page(spec, root, pe['box'])
                if not any(f[0] < cb[0] + cb[2] and cb[0] < f[0] + f[2] and f[1] < cb[1] + cb[3] and cb[1] < f[1] + f[3]
                           for f in fs for cb in cut_boxes):
                    break
                pe['box'][0] = round(pe['box'][0] + (-0.03 if side == 'left' else 0.03), 4)
                pe['box'][0] = min(max(pe['box'][0], 0.0), 1 - pe['box'][2])
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- 局部放大

def region_on_page(e, region, root):
    """原图上的一块区域（相对 e 的原图 0–1 坐标）换算到页面坐标 [x,y,w,h]。换算不了返回 None。"""
    rx0, ry0, rx1, ry1 = region
    src = e.get('_src_path')
    if not src:
        return None
    with Image.open(root / src) as im:
        iw, ih = im.size
    if e.get('_map'):                                  # 抠图：contain，按记录的缩放和位置换算
        m = e['_map']
        def pt(px, py):
            return ((m['x'] + (px * iw - m['bb'][0]) * m['s']) / W, (m['y'] + (py * ih - m['bb'][1]) * m['s']) / H)
    elif e.get('fit') == 'cover':                      # 照片 / 整版底：和渲染器同一套 cover 裁切
        spec = {'path': src, 'face': e.get('face_boxes', []), 'focus': e.get('focus', [0.5, 0.4])}
        if e.get('crop'):
            spec['crop'] = e['crop']
        _, win, (tw, th) = cover_window(spec, root, e['box'])
        c = e.get('crop', [0, 0, 1, 1])
        x0, y0, x1, y1 = win
        sc = tw / (x1 - x0)
        bx, by = e['box'][0], e['box'][1]
        def pt(px, py):
            return (bx + ((px - c[0]) * iw - x0) * sc / W, by + ((py - c[1]) * ih - y0) * sc / H)
    else:
        return None
    a, b = pt(rx0, ry0); c2, d = pt(rx1, ry1)
    return [a, b, c2 - a, d - b]


def plan_zoom(z, images, texts, root, work, accent, top):
    """局部放大：把原图上的一小块裁出来，放大成圆形或方形小图，摆在原处旁边不挡脸、不压标题的地方；
    原处画一圈，再画一根箭头连过去。放大倍数不超过 max_scale（默认 1.25，免得糊）。"""
    want = z.get('src', '')
    src = next((e for e in images if e.get('kind') in ('image', 'dark_backdrop') and not e.get('ghost')
                and (want in (e.get('source_id') or '') or want in (e.get('_src_path') or ''))), None)
    if src is None:
        return [], [], f'局部放大找不到原图：{want}'
    region = list(z['region'])
    with Image.open(root / src['_src_path']) as im:
        iw, ih = im.size
        shape = z.get('shape', 'circle')
        if shape == 'circle':                           # 圆形：按像素取正方形区域
            cx, cy = (region[0] + region[2]) / 2 * iw, (region[1] + region[3]) / 2 * ih
            r = max((region[2] - region[0]) * iw, (region[3] - region[1]) * ih) / 2
            region = [(cx - r) / iw, (cy - r) / ih, (cx + r) / iw, (cy + r) / ih]
        px = [max(0, round(region[0] * iw)), max(0, round(region[1] * ih)), min(iw, round(region[2] * iw)), min(ih, round(region[3] * ih))]
        crop = im.convert('RGB').crop(px)
    out = work / 'zoom' / f"{Path(src['_src_path']).stem}-{'-'.join(str(v) for v in px)}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        crop.save(out, quality=94)
    rw, rh = crop.size
    zw = min(z.get('size', 0.32), rw * z.get('max_scale', 1.25) / W)
    zh = zw * W * rh / rw / H
    rp = region_on_page(src, region, root)
    if rp is None:
        return [], [], '局部放大：这类图换算不了位置'
    faces = []
    for e in images:
        if e.get('role') == 'foreground':
            x, y, w, h = e['box']
            faces += [[x + fx * w, y + fy * h, fw * w, fh * h] for fx, fy, fw, fh in e.get('face_boxes', [])]
        elif e.get('kind') == 'image' and e.get('fit') == 'cover' and e.get('_src_path'):
            try:
                spec = {'path': e['_src_path'], 'face': e.get('face_boxes', []), 'focus': e.get('focus', [0.5, 0.4])}
                if e.get('crop'):
                    spec['crop'] = e['crop']
                faces += face_boxes_on_page(spec, root, e['box'])
            except Exception:
                pass
    heads = [t['box'] for t in texts]
    img_boxes = [e['box'] for e in images if e.get('kind') == 'image' and e.get('box') != [0, 0, 1, 1]]
    def hit(a, b, pad=0.0):
        return a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad and a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad
    gap = 0.035
    rcx, rcy = rp[0] + rp[2] / 2, rp[1] + rp[3] / 2
    cands = []
    for dx, dy in [(1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1), (0, -1), (0, 1),
                   (0.5, -1), (-0.5, -1), (0.5, 1), (-0.5, 1), (1, -0.5), (-1, -0.5), (1, 0.5), (-1, 0.5)]:
        cx = rcx + dx * (rp[2] / 2 + gap + zw / 2)
        cy = rcy + dy * (rp[3] / 2 + gap * W / H + zh / 2)
        bx = min(max(cx - zw / 2, 0.025), 0.975 - zw)
        by = min(max(cy - zh / 2, top), 0.94 - zh)
        box = [bx, by, zw, zh]
        if hit(box, rp, 0.01) or any(hit(box, f, 0.01) for f in faces) or any(hit(box, t) for t in heads):
            continue
        if bx + zw > 0.86 and by + zh > 0.92:          # 右下角署名
            continue
        dist = abs(bx + zw / 2 - rcx) + abs(by + zh / 2 - rcy)
        # 优先压在已有的图上（那里本来就排不了字），少占空白，免得把正文挤没地方
        on_img = 0.0
        for ib in img_boxes:
            ix = max(0, min(box[0] + zw, ib[0] + ib[2]) - max(box[0], ib[0]))
            iy = max(0, min(box[1] + zh, ib[1] + ib[3]) - max(box[1], ib[1]))
            on_img = max(on_img, ix * iy / (zw * zh))
        cands.append((dist + 0.8 * (1 - on_img), box))
    if not cands:
        return [], [], '局部放大：原图旁边没有空位（挡脸或压标题）'
    box = [round(v, 4) for v in min(cands)[1]]
    circle = shape == 'circle'
    ze = {'kind': 'image', 'path': out.relative_to(root).as_posix(), 'box': box, 'fit': 'cover',
          'effects': ['circle'] if circle else [], 'source_id': (src.get('source_id') or '') + '-detail',
          'role': 'detail', 'no_fx': True, 'face_boxes': [], 'face_detection_method': 'manual-verified',
          'soft_shadow': {'color': '#000000', 'offset': [8, 10], 'blur': 14, 'opacity': 0.6}, 'coverage': True}
    if z.get('label'):
        ze['label_text'] = z['label']
    ring = {'kind': 'ellipse' if circle else 'rect', 'box': box, 'outline': z.get('color', accent), 'width': 8}
    pad = 0.006
    mark = {'kind': 'ellipse', 'box': [round(rp[0] - pad, 4), round(rp[1] - pad * W / H, 4), round(rp[2] + 2 * pad, 4), round(rp[3] + 2 * pad * W / H, 4)],
            'outline': z.get('color', accent), 'width': 6}
    # 箭头：从原处圈的边缘指向放大图的边缘，往外弯一点
    zcx, zcy = box[0] + zw / 2, box[1] + zh / 2
    vx, vy = (zcx - rcx) * W, (zcy - rcy) * H
    dist = max(1.0, (vx * vx + vy * vy) ** 0.5)
    ux, uy = vx / dist, vy / dist
    def edge(a, b, pad):                                # 沿方向 (ux,uy) 走到椭圆/矩形边上的距离
        a, b = a + pad, b + pad
        return 1.0 / max(1e-6, ((ux / a) ** 2 + (uy / b) ** 2) ** 0.5)
    rr = edge(rp[2] * W / 2, rp[3] * H / 2, 12)
    zr = edge(zw * W / 2, zh * H / 2, 10)
    sx, sy = rcx * W + ux * rr, rcy * H + uy * rr
    ex, ey = zcx * W - ux * zr, zcy * H - uy * zr
    arrows = []
    if ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 > 50:
        mx, my = (sx + ex) / 2 - uy * 40, (sy + ey) / 2 + ux * 40
        arrows.append({'kind': 'arrow', 'points': [[round(sx / W, 4), round(sy / H, 4)], [round(mx / W, 4), round(my / H, 4)], [round(ex / W, 4), round(ey / H, 4)]],
                       'fill': z.get('color', accent), 'width': 6, 'head': 26})
    occ_boxes = [('ellipse' if circle else 'box', [box[0] - 0.01, box[1] - 0.008, zw + 0.02, zh + 0.016])]
    if arrows:
        pts = arrows[0]['points']
        xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
        occ_boxes.append(('box', [min(xs) - 0.01, min(ys) - 0.01, max(xs) - min(xs) + 0.02, max(ys) - min(ys) + 0.02]))
    return [ze, ring, mark] + arrows, occ_boxes, None


# ---------------------------------------------------------------- 文字流

class Flow:
    def __init__(self, T, ctx, occ, protect, factor):
        self.T, self.ctx, self.occ, self.protect, self.factor = T, ctx, occ, protect, factor
        self.accent = ctx['accent']

    def size(self, role, step):
        lo, pref, hi = SIZE[role]
        pref = getattr(self, 'pref', {}).get(role, pref)
        return max(lo, min(hi, pref + step * STEP[role]))

    def run(self, items, x, y0, y1, anchor='left', maxw=0.888, align='left', step=0, spread=True):
        """先紧排一遍；下面空得多，就把空白分给段与段之间（强调句前面分得最多），
        像原作那样上下两组文字撑满页面。分完放不下就退回紧排。"""
        snap = self.occ.g.copy()
        base = self._run(items, x, y0, y1, anchor, maxw, align, step, None)
        if not base or not spread or len(items) < 2:
            return base
        left = y1 - base[1]
        if left < 0.06:
            return base
        weight = {'emphasis': 2.6, 'foot': 1.6, 'note': 1.0, 'body': 0.35, 'image': 1.0}   # 同一段正文之间少分，分组处多分
        ws = [weight.get(r, 1.0) for r, _ in items[1:]]
        for frac in (0.85, 0.55, 0.3):
            extra = [min(0.10, left * frac * w / sum(ws)) for w in ws]
            self.occ.g = snap.copy()
            r = self._run(items, x, y0, y1, anchor, maxw, align, step, extra)
            if r:
                return r
        self.occ.g = snap.copy()
        return self._run(items, x, y0, y1, anchor, maxw, align, step, None)

    def fit_at(self, role, text, y, anchor, x, maxw, align, size):
        """在高度 y 处，把一段文字放进 anchor 一侧的空位，宽度逐步收窄直到不碰图。放不下返回 None。"""
        w = maxw
        for _ in range(8):
            ex = x if anchor == 'left' else x - w
            al = getattr(self, 'align_of', {}).get(role, align)
            fl = getattr(self, 'fill_of', {}).get(role)
            e = measure(tx(role, text, ex, y, w * self.factor, size, self.accent, al, fl), self.T, self.protect)
            e['box'][2] = w
            h = e['box'][3]
            if anchor == 'left':
                fw = self.occ.free_right(x, y, y + h, x + maxw) - x
            else:
                fw = x - self.occ.free_left(x, y, y + h, x - maxw)
            if fw >= w - 0.002:
                return e, w
            if fw < MINW:
                return None
            w = fw
        return None

    def _run(self, items, x, y0, y1, anchor, maxw, align, step, extra):
        """items: [(role, text)] 或 ('image', 生成函数)。anchor='left' 左边对齐 x；'right' 右边对齐 x；
        'auto' 每段文字自己挑左右两侧里更宽的空位（拼贴版式用，图左右交替时文字跟着换边）。"""
        y, out, last_role = y0, [], None
        for k, (role, obj) in enumerate(items):
            if last_role:
                y += max(GAP.get(last_role, 0.02), GAP.get(role, 0.02)) if role != 'image' else 0.022
                if extra:
                    y += extra[k - 1]
            if anchor == 'auto' and role != 'image':
                size = self.size(role, step)
                for _ in range(60):
                    cands = [c for c in (self.fit_at(role, obj, y, 'left', L, maxw, align, size),
                                         self.fit_at(role, obj, y, 'right', R, maxw, align, size)) if c]
                    if cands:
                        break
                    y += 0.012
                else:
                    return None
                e, w = max(cands, key=lambda c: c[1])
                if y + e['box'][3] > y1 + 0.004:
                    return None
                out.append(e)
                y += e['box'][3]
                last_role = role
                continue
            if role == 'image':
                e = obj(x if anchor == 'left' else x - 0.42, y)
                out.append(e)
                self.occ.add_box(e['box'])
                y = e['box'][1] + e['box'][3]
                last_role = 'image'
                continue
            size = self.size(role, step)
            w = maxw
            for _ in range(40):
                ex = x if anchor == 'left' else x - w
                al = getattr(self, 'align_of', {}).get(role, align)
                fl = getattr(self, 'fill_of', {}).get(role)
                e = measure(tx(role, obj, ex, y, w * self.factor, size, self.accent, al, fl), self.T, self.protect)
                e['box'][2] = w
                h = e['box'][3]
                if anchor == 'left':
                    fw = self.occ.free_right(x, y, y + h, x + maxw) - x
                else:
                    fw = x - self.occ.free_left(x, y, y + h, x - maxw)
                if fw >= w - 0.002:
                    break
                if fw < MINW:
                    y += 0.012; w = maxw
                    continue
                w = fw
            else:
                return None
            if y + h > y1 + 0.004:
                return None
            out.append(e)
            y += h
            last_role = role
        return out, y


# ---------------------------------------------------------------- 版式

def arrow_to(e_text, target_box, occ, texts, cfg, accent):
    """强调句旁边画一根手绘箭头，指向人物：从强调句靠近人物的一侧出发，箭头尖停在人物边上。
    离得太远（>380px）、空间太挤或会碰到别的字，就不画。"""
    b = ink_bounds(e_text, cfg)
    if not b:
        return None
    tx0, ty0 = target_box[0] * W, target_box[1] * H
    tx1, ty1 = tx0 + target_box[2] * W, ty0 + target_box[3] * H
    cy = (b[1] + b[3]) / 2
    if tx0 > b[2] + 90:
        sx, sy = b[2] + 24, cy
    elif tx1 < b[0] - 90:
        sx, sy = b[0] - 24, cy
    elif ty1 < b[1] - 60:
        sx, sy = (b[0] + b[2]) / 2, b[1] - 20
    else:
        return None
    ex, ey = min(max(sx, tx0 + 30), tx1 - 30), min(max(sy, ty0 + 30), ty1 - 30)   # 人物框里离起点最近的点
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy)
    if dist < 80 or dist > 380:
        return None
    k = min(1.0, 240 / dist)
    ex, ey = sx + dx * k, sy + dy * k
    if dist * (1 - k) > 140:
        return None
    nx, ny = -dy / dist, dx / dist                    # 往法线方向弯一点，像手画的
    cx, cy2 = (sx + ex) / 2 + nx * 0.18 * dist * k, (sy + ey) / 2 + ny * 0.18 * dist * k
    pts = [[sx / W, sy / H], [cx / W, cy2 / H], [ex / W, ey / H]]
    xs, ys = [sx, cx, ex], [sy, cy2, ey]
    box = [min(xs) / W, min(ys) / H, (max(xs) - min(xs)) / W, (max(ys) - min(ys)) / H]
    if min(ys) < 60 or max(ys) > H - 60:
        return None
    for t in texts:
        if t is e_text:
            continue
        x, y, w, h = t['box']
        if box[0] < x + w and x < box[0] + box[2] and box[1] < y + h and y < box[1] + box[3]:
            return None
    return {'kind': 'arrow', 'points': [[round(a_, 4), round(c_, 4)] for a_, c_ in pts], 'fill': accent, 'width': 6, 'head': 30}


def grow(page, k):
    """拼贴页的图整体放大 k 倍（作者写的 h/w 和默认值都放大），用来先试大图。"""
    n = len(page['images'])
    defaults = {'cut': (0.64 if n == 2 else 0.46, 0.56), 'rect': (0.38 if n == 2 else 0.28, 0.66), 'oval': (None, 0.34), 'band': (0.34, None)}
    caps = {'cut': (0.80, 0.70), 'rect': (0.50, 0.80), 'oval': (None, 0.50), 'band': (0.50, None)}
    imgs = []
    for sp in page['images']:
        kind = sp.get('as') or ('cut' if sp.get('cut') else 'rect')
        dh, dw = defaults.get(kind, (None, None)); ch, cw = caps.get(kind, (None, None))
        sp = dict(sp)
        if dh: sp['h'] = round(min(ch, sp.get('h', dh) * k), 3)
        if dw: sp['w'] = round(min(cw, sp.get('w', dw) * k), 3)
        imgs.append(sp)
    return {**page, 'images': imgs}


def build_page(i, page, ctx, T, factor=1.0):
    lay = page['layout']
    if lay == '手排':                                   # 手工排好的页：元素原样交给渲染器
        return ({'layout': 'collage', 'background': '#000000', 'watermark': True, 'skeleton': '手排', 'style': 'v2',
                 'elements': page['elements']}, {'layout': '手排', 'columns': []})
    if lay == '拼贴' and '_shrink' not in page and not page.get('no_grow'):
        page = {**grow(page, 1.3), '_shrink': 0}      # 先试放大 1.3 倍的图，排不下再逐档缩小
    root, work, accent = ctx['root'], ctx['work'], ctx['accent']
    protect = ctx['protect'] + page.get('protect', [])
    cfg = {'accent': accent, 'background': '#000000', 'fonts': T.CFG.get('fonts', {})}
    zoom_els, zoom_occ = [], []
    if page.get('zoom') and not page.get('_dry'):
        # 先不带正文排一遍，拿到图的位置，再决定放大图摆哪里；正文再绕开它排
        saved = {k: ctx.get(k) for k in ('arrows', 'fx_phase')}
        dry = {k: v_ for k, v_ in page.items() if k not in ('body', 'note', 'emphasis', 'foot', 'zoom')}
        dry.update(_dry=True, arrow=False, ghost=False, _dry_body=page.get('body', ''))   # 标题、图带位置要和正式排版一致
        dp, _ = build_page(i, dry, ctx, T, factor)
        for k, v_ in saved.items():
            if v_ is None:
                ctx.pop(k, None)
            else:
                ctx[k] = v_
        d_imgs = [e for e in dp['elements'] if e.get('kind') != 'text']
        d_txts = [e for e in dp['elements'] if e.get('kind') == 'text']
        zs = page['zoom'] if isinstance(page['zoom'], list) else [page['zoom']]
        top = max([t['box'][1] + t['box'][3] for t in d_txts if t.get('text_role') == 'heading' and t['box'][1] < 0.12] + [TOP]) + 0.01   # 只看顶上的标题
        for zi, z in enumerate(zs):
            els, oc, err = plan_zoom(z, d_imgs, d_txts + [e for e in zoom_els if e.get('kind') == 'image'], root, work, accent, top)
            if err:
                ctx.setdefault('warnings', []).append(f'第{i}张：{err}')
            src = next((e for e in d_imgs if e.get('kind') in ('image', 'dark_backdrop') and not e.get('ghost')
                        and (z.get('src', '') in (e.get('source_id') or '') or z.get('src', '') in (e.get('_src_path') or ''))), None)
            for e in els:                               # 记下规划时原图的位置，正式排完后核对
                e['_zgroup'] = zi; e['_zsrcbox'] = list(src['box']) if src else None
            zoom_els += els; zoom_occ += oc
    paras = paragraphs(page.get('body', ''))
    hero, second, bd = page.get('hero'), page.get('second'), page.get('backdrop')
    side = page.get('side', 'right')

    last = None
    for step in ([0, -1, -2, -3] if not page.get('step') else [page['step']]):
        occ = Occ()
        images, texts, flow = [], [], Flow(T, ctx, occ, protect, factor)
        v = vary(i, page, ctx)
        flow.pref = {'emphasis': v['emph_pref'], 'title': v['title_size']}
        flow.align_of = {'emphasis': v['emph_align']}
        flow.fill_of = {'emphasis': v['emph_fill'], 'note': v['note_fill']}
        target = None                                   # 箭头指向谁
        for kind_, b in zoom_occ:
            (occ.add_ellipse if kind_ == 'ellipse' else occ.add_box)(b)

        # 标题（约四成页面把标题放到页面中段，当作一句大字，不压在顶上）
        y = TOP
        mid_title = None
        if page.get('title') and v['title_mid'] and lay in ('拼贴', '大图', '渐隐') and (page.get('body') or page.get('_dry')):
            mid_title = page['title'].replace('\n', '')
        if page.get('title') and not mid_title:
            t = page['title']
            if '\n' not in t and '，' in t.strip('，') and len(t) >= 8:
                a, b = t.split('，', 1); t = a + '，\n' + b
            size, talign = v['title_size'], v['title_align']
            while True:
                e = measure(tx('title', t, L, y, 0.888, size, accent, talign, v['title_fill']), T, protect)
                if e['text'].count('\n') <= 1 or size <= SIZE['title'][0]:
                    break
                size -= STEP['title']
            texts.append(e)
            y = e['box'][1] + e['box'][3] + 0.024
        tb = y

        emph = page.get('emphasis')
        pp = list(paras)
        if emph and v['emph_inline'] and pp:
            parts = [x for x in re.split(r'(?<=[，。！？：；])|\n', emph) if x and x.strip()]
            pp[-1] = pp[-1] + ''.join('[[' + x.strip() + ']]' for x in parts)   # 按分句高亮，断行时可以在分句之间断
            emph = None
        rest = [('body', p) for p in pp[1:]]
        if mid_title:
            rest.insert(0, ('title', mid_title))
        if page.get('note'):
            rest.append(('note', page['note']))
        if emph and v['emph_mid'] and rest:
            rest.insert(0, ('emphasis', emph))     # 强调句放在页面中段，不总压在最底下
        elif emph:
            rest.append(('emphasis', emph))
        if page.get('foot'):
            rest.append(('foot', page['foot']))
        first = [('body', pp[0])] if pp else []
        ok = True

        if bd:
            images.append(backdrop(bd, page.get('darken', 0.6)))
            for f in face_boxes_on_page(bd, root, [0, 0, 1, 1]):
                occ.add_box([f[0] - 0.02, f[1] - 0.02, f[2] + 0.04, f[3] + 0.04])

        if lay == '拼贴':
            # 2–3 张图左右交替（Z 字），图可以出血、互相压叠；文字每段自己找图旁边更宽的空位。
            specs = page['images']
            n = len(specs)
            deferred = []
            zone = 1.0 - tb
            side = v['side']
            arrange = page.get('arrange') or ('stack' if v['stack'] and not any(sp.get('as') == 'band' for sp in specs) else 'zigzag')
            if arrange == 'stack':
                pos = page.get('pos') or v['stack_pos']
                bh = page.get('band_h', 0.48 if n >= 2 else 0.42)
                if pos == 'top':
                    by = tb
                elif pos == 'bottom':
                    by = 1 - bh
                else:                                       # 中间：先估第一段字的高度，图带放在它下面
                    p0 = (paragraphs(page.get('body') or page.get('_dry_body', '')) or [''])[0]
                    est = measure(tx('body', p0, L, tb, 0.888 * factor, SIZE['body'][1], accent), T, protect)['box'][3] if p0 else 0
                    by = min(tb + est + 0.03, 1 - bh)
                deferred = place_stack(specs, by, bh, side, root, work)
                for t_, e, _ in deferred:
                    images.append(e)
                    if t_ == 'alpha':
                        target = target or e['box']
                deferred = [(('box' if t_ == 'ellipse' else t_), e, x_) for t_, e, x_ in deferred]
                specs = []
            for k, sp in enumerate(specs):
                sd = sp.get('side') or (side if k % 2 == 0 else ('left' if side == 'right' else 'right'))
                kind = sp.get('as') or ('cut' if sp.get('cut') else 'rect')
                cy = tb + zone * (k + 0.5) / n + sp.get('dy', v['jitter'][k % 4])
                last_img = k == n - 1
                if kind == 'cut':
                    h = sp.get('h', 0.64 if n == 2 else 0.46)
                    bottom = sp.get('bottom', 1.0 if last_img else min(1.0, max(cy + h * 0.5, tb + h)))
                    ce, alpha = place_cutout(sp, root, work, sd, h, sp.get('w', 0.56), bottom=bottom,
                                             hero=(k == 0), edge=sp.get('edge'))
                    images.append(ce); deferred.append(('alpha', ce, alpha))
                    target = target or ce['box']
                elif kind == 'band':
                    # 压暗的通栏图带，上下渐隐；文字可以直接压在上面（只避开人脸）
                    bh = sp.get('h', 0.34)
                    by = min(max(tb, cy - bh / 2), 1 - bh)
                    bd_e = {**backdrop(sp, sp.get('darken', 0.42)), 'box': [0, round(by, 4), 1, bh], 'fade_fraction': 0.25}
                    images.insert(0, bd_e)
                    for f in face_boxes_on_page(sp, root, [0, by, 1, bh]):
                        occ.add_box([f[0] - 0.02, f[1] - 0.02, f[2] + 0.04, f[3] + 0.04])
                elif kind == 'oval':
                    ow = sp.get('w', 0.34); oh = ow * W * 1.25 / H
                    ox = R - ow if sd == 'right' else L
                    oy = max(tb, cy - oh / 2)
                    images.append(photo(sp, [ox, oy, ow, oh], hero=(k == 0), oval=True))
                    occ.add_ellipse([ox - 0.01, oy - 0.008, ow + 0.02, oh + 0.016]); target = target or [ox, oy, ow, oh]
                else:
                    with Image.open(root / sp['path']) as im_:
                        iw, ih = im_.size
                    c = sp.get('crop', [0, 0, 1, 1]); asp = (c[2] - c[0]) * iw / ((c[3] - c[1]) * ih)
                    h = sp.get('h', 0.38 if n == 2 else 0.28); w = min(sp.get('w', 0.66), h * H * asp / W)
                    h = min(h, w * W / asp / H)
                    inset = sp.get('inset', 0.0 if k % 2 else 0.035)
                    x0 = 1 - w - inset if sd == 'right' else inset
                    y0 = max(tb, cy - h / 2)
                    if last_img and sp.get('bleed', False):
                        y0 = 1 - h
                    pbox = [round(x0, 4), round(y0, 4), round(w, 4), round(h, 4)]
                    pe = photo(sp, pbox, hero=(k == 0)); images.append(pe)
                    deferred.append(('photo' if sp.get('overlay', True) else 'box', pe, sp))
            # 叠压：照片和人物抠图离得远（上下有重合、左右有空隙）时，把照片往人物那边挪，压住一角
            if page.get('overlap', True) and arrange != 'stack':
                cuts = [e for t_, e, _ in deferred if t_ == 'alpha']
                for t_, pe, sp in deferred:
                    if t_ == 'alpha':
                        continue
                    x, y, w, h = pe['box']
                    for ce in cuts:
                        cx, cy_, cw, ch = ce['box']
                        if min(y + h, cy_ + ch) - max(y, cy_) < 0.04:
                            continue
                        if x > cx + cw:                                   # 照片在人物右边
                            nx = max(cx + cw * 0.78, 0.0)
                        elif x + w < cx:                                  # 照片在人物左边
                            nx = min(cx + cw * 0.22 - w, 1 - w)
                        else:
                            break
                        pe['box'][0] = round(min(max(nx, 0.0), 1 - w), 4)
                        break
            for t_, e, extra in deferred:
                if t_ == 'alpha':
                    occ.add_alpha(extra, e['box'])
                elif t_ == 'photo':
                    occ.add_photo(extra, root, e['box'])
                else:
                    occ.add_box(e['box'])
            # 照片画在人物下面
            imgs_rect = [e for t_, e, _ in deferred if t_ != 'alpha']
            imgs_cut = [e for t_, e, _ in deferred if t_ == 'alpha']
            others = [e for e in images if not any(e is z for z in imgs_rect + imgs_cut)]
            images[:] = others + imgs_rect + imgs_cut
            r = flow.run(first + rest, L, tb, BOTTOM, anchor='auto', step=step)
            if not r: ok = False
            else: texts += r[0]

        elif lay == '大图':
            # 一张大图占半页以上，贴页面上沿或下沿、边缘渐隐；字压在图的暗处或排在另一半。
            pos = page.get('pos', 'top')
            bh = page.get('band_h', 0.58)
            by = 0.0 if pos == 'top' else 1 - bh
            if pos == 'top' and page.get('title') and tb > 0.06:
                # 标题压在图上：图在标题那一段太亮就看不清字，这时把图挪到标题下面
                try:
                    _, win, _ = cover_window(hero, root, [0, by, 1, bh])
                    with Image.open(root / hero['path']) as im_:
                        im_ = im_.convert('L'); c = hero.get('crop', [0, 0, 1, 1])
                        ox, oy = c[0] * im_.width, c[1] * im_.height
                        x0, y0, x1, y1 = win
                        top = im_.crop((round(ox + x0), round(oy + y0), round(ox + x1), round(oy + y0 + (y1 - y0) * (tb - by) / bh)))
                        bright = float(np.asarray(top.resize((64, 16))).mean())
                except Exception:
                    bright = 255
                if bright * (1 - hero.get('darken', page.get('darken', 0.08))) > page.get('title_bright_max', 80):
                    by = tb - 0.03
            bd_e = {**backdrop(hero, page.get('darken', 0.08)), 'box': [0, by, 1, bh], 'fade_fraction': 0.25}
            if hero.get('label'):
                bd_e['label_text'] = hero['label']
            images.insert(0, bd_e)
            occ.add_photo({**hero, 'dark_cut': page.get('dark_cut', 60)}, root, [0, by, 1, bh])
            if second:
                kind2 = 'cut' if second.get('cut') else 'rect'
                sd = page.get('second_side', 'right')
                if kind2 == 'cut':
                    ce, alpha = place_cutout(second, root, work, sd, page.get('cut_h', 0.36), page.get('cut_w', 0.42), hero=False)
                    images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
                else:
                    with Image.open(root / second['path']) as im_:
                        iw, ih = im_.size
                    c = second.get('crop', [0, 0, 1, 1]); asp = (c[2] - c[0]) * iw / ((c[3] - c[1]) * ih)
                    h2 = page.get('rect_h', 0.24); w2 = min(page.get('rect_w', 0.40), h2 * H * asp / W); h2 = w2 * W / asp / H
                    x2 = 1 - w2 - 0.035 if sd == 'right' else 0.035
                    y2 = (1 - h2 - 0.05) if pos == 'top' else (by - h2 * 0.35)
                    pbox = [round(x2, 4), round(y2, 4), round(w2, 4), round(h2, 4)]
                    images.append(photo(second, pbox, hero=False)); occ.add_box(pbox)
            r = flow.run(first + rest, L, tb, BOTTOM, anchor='auto', step=step)
            if not r: ok = False
            else: texts += r[0]

        elif lay == '图文叠':
            r1 = flow.run(first, L, tb, 0.42, step=step)
            if not r1: ok = False
            else:
                texts += r1[0]; yr = r1[1] + 0.024
                rh, rw = page.get('rect_h', 0.27), page.get('rect_w', 0.80)
                pbox = [L if side == 'right' else R - rw, yr, rw, rh]
                images.append(photo(hero, pbox)); occ.add_box(pbox)
                if second:
                    ch = page.get('cut_h', 1.0 - (yr + rh - 0.15))
                    ce, alpha = place_cutout(second, root, work, side, max(0.30, ch), page.get('cut_w', 0.56), hero=False)
                    images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
                r2 = flow.run(rest, L if side == 'right' else R, yr + rh + 0.028, BOTTOM,
                              anchor='left' if side == 'right' else 'right', step=step)
                if not r2: ok = False
                else: texts += r2[0]

        elif lay == '立像':
            ce, alpha = place_cutout(hero, root, work, side, page.get('cut_h', 0.70), page.get('cut_w', 0.60),
                                     edge=page.get('cut_edge'))
            images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
            items = first[:]
            if second:
                sw, sh = page.get('second_w', 0.40), page.get('second_h', 0.21)
                items.append(('image', lambda x, yy, s=second, sw=sw, sh=sh: photo(s, [x, yy, sw, sh], hero=False)))
            items += rest
            anchor = 'left' if side == 'right' else 'right'
            r = flow.run(items, L if side == 'right' else R, tb, BOTTOM, anchor=anchor, step=step)
            if not r: ok = False
            else:
                for e in r[0]:
                    (images if e['kind'] == 'image' else texts).append(e)

        elif lay == '圆像':
            ow = page.get('oval_w', 0.36)
            oh = ow * W * 1.25 / H
            ox = R - ow if side == 'right' else L
            oy = page.get('oval_y', tb + 0.01)
            obox = [ox, oy, ow, oh]
            images.append(photo(hero, obox, oval=True))
            if page.get('ring', False):
                pad = 10
                images.append({'kind': 'ellipse', 'box': [ox - pad / W, oy - pad / H, ow + 2 * pad / W, oh + 2 * pad / H],
                               'outline': accent, 'width': 7})
            occ.add_ellipse([ox - 0.01, oy - 0.008, ow + 0.02, oh + 0.016]); target = obox
            if second:
                ce, alpha = place_cutout(second, root, work, 'left' if side == 'right' else 'right',
                                         page.get('cut_h', 0.42), page.get('cut_w', 0.46), hero=False)
                images.append(ce); occ.add_alpha(alpha, ce['box'])
            a1 = 'left' if side == 'right' else 'right'
            x1 = L if side == 'right' else R
            r1 = flow.run(first, x1, tb, oy + oh, anchor=a1, step=step)
            if not r1: ok = False
            else:
                texts += r1[0]
                a2 = ('right' if side == 'right' else 'left') if second else a1
                x2 = (R if a2 == 'right' else L)
                r2 = flow.run(rest, x2, max(r1[1] + 0.03, oy + oh * 0.55), BOTTOM, anchor=a2, step=step)
                if not r2: ok = False
                else: texts += r2[0]

        elif lay == '渐隐':
            if second:
                ce, alpha = place_cutout(second, root, work, side, page.get('cut_h', 0.46), page.get('cut_w', 0.46), hero=False)
                images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
            anchor = page.get('text_anchor', 'left')
            r = flow.run(first + rest, L if anchor == 'left' else R, tb, BOTTOM, anchor=anchor,
                         maxw=page.get('text_w', 0.70), step=step)
            if not r: ok = False
            else: texts += r[0]

        elif lay == '宽幅':
            r1 = flow.run(first, L, tb, 0.42, step=step)
            if not r1: ok = False
            else:
                texts += r1[0]; yr = r1[1] + 0.026
                rh = page.get('rect_h', 0.29)
                pbox = [0, yr, 1, rh]
                images.append(photo(hero, pbox)); occ.add_box(pbox)
                cside = 'left' if side == 'right' else 'right'
                if second:
                    top = yr + rh - page.get('overlap', 0.12)
                    ce, alpha = place_cutout(second, root, work, cside, page.get('cut_h', 1.0 - top), page.get('cut_w', 0.46), hero=False)
                    images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
                anchor = 'right' if cside == 'left' else 'left'
                r2 = flow.run(rest, R if anchor == 'right' else L, yr + rh + 0.03, BOTTOM, anchor=anchor,
                              align=page.get('align', 'left'), step=step)
                if not r2: ok = False
                else: texts += r2[0]

        elif lay == '错落':
            rw, rh = page.get('rect_w', 0.42), page.get('rect_h', 0.25)
            rx = R - rw if side == 'right' else L
            pbox = [rx, tb, rw, rh]
            images.append(photo(second, pbox, hero=False)); occ.add_box(pbox)
            cside = 'left' if side == 'right' else 'right'
            ce, alpha = place_cutout(hero, root, work, cside, page.get('cut_h', 0.52), page.get('cut_w', 0.50))
            images.append(ce); occ.add_alpha(alpha, ce['box']); target = ce['box']
            a1 = 'left' if side == 'right' else 'right'
            r1 = flow.run(first, L if a1 == 'left' else R,
                          tb, min(tb + rh + 0.10, ce['box'][1] - 0.01), anchor=a1, step=step)
            if not r1: ok = False
            else:
                texts += r1[0]
                a2 = 'right' if a1 == 'left' else 'left'
                r2 = flow.run(rest, R if a2 == 'right' else L, max(r1[1] + 0.028, tb + rh + 0.03), BOTTOM, anchor=a2, step=step)
                if not r2: ok = False
                else: texts += r2[0]
        else:
            raise ValueError(f'未知版式 {lay}')

        last = (images, texts, target, occ)
        if ok:
            break
    else:
        shrink = page.get('_shrink', 0)
        if lay == '拼贴' and shrink < 5:                 # 拼贴页图放不下就缩小一档再排（从放大版开始，最多五档）
            defaults = {'cut': (0.64 if len(page['images']) == 2 else 0.46, 0.56), 'rect': (0.38 if len(page['images']) == 2 else 0.28, 0.66),
                        'oval': (None, 0.34), 'band': (0.34, None)}
            imgs = []
            for sp in page['images']:
                kind = sp.get('as') or ('cut' if sp.get('cut') else 'rect')
                dh, dw = defaults.get(kind, (None, None))
                sp = dict(sp)
                if dh: sp['h'] = round(sp.get('h', dh) * 0.9, 3)
                if dw: sp['w'] = round(sp.get('w', dw) * 0.9, 3)
                imgs.append(sp)
            more = {'band_h': round(page.get('band_h', 0.48 if len(page['images']) >= 2 else 0.42) * 0.9, 3)}
            return build_page(i, {**page, 'images': imgs, '_shrink': shrink + 1, **more}, ctx, T, factor)
        if lay != '拼贴' and shrink < 4:                 # 其他版式：图的尺寸参数统一缩一档再排
            dflt = {'cut_h': 0.6, 'cut_w': 0.56, 'rect_h': 0.27, 'rect_w': 0.6, 'oval_w': 0.36, 'band_h': 0.56}
            smaller = {k: round(page.get(k, d) * 0.9, 3) for k, d in dflt.items()}
            return build_page(i, {**page, **smaller, '_shrink': shrink + 1}, ctx, T, factor)
        raise ValueError(f'第{i}张「{lay}」文字放不下：删一点正文，或调小 cut_h / rect_h')

    images, texts, target, occ = last
    if zoom_els:
        # 正式排版时图可能被缩小、挪动（文字放不下）。原图位置变了，就按最终的图和文字重新摆放大图
        zs = page['zoom'] if isinstance(page['zoom'], list) else [page['zoom']]
        final = []
        for zi, z in enumerate(zs):
            grp = [e for e in zoom_els if e.get('_zgroup') == zi]
            src = next((e for e in images if e.get('kind') in ('image', 'dark_backdrop') and not e.get('ghost')
                        and (z.get('src', '') in (e.get('source_id') or '') or z.get('src', '') in (e.get('_src_path') or ''))), None)
            old_box = grp[0].get('_zsrcbox') if grp else None
            if src is None:
                continue
            if grp and old_box and all(abs(a - b) < 0.002 for a, b in zip(old_box, src['box'])):
                final += grp
                continue
            top_ = max([t['box'][1] + t['box'][3] for t in texts if t.get('text_role') == 'heading' and t['box'][1] < 0.12] + [TOP]) + 0.01
            els, _, err = plan_zoom(z, images, texts + [e for e in final if e.get('kind') == 'image'], root, work, accent, top_)
            if err:
                ctx.setdefault('warnings', []).append(f'第{i}张：局部放大重排失败，已去掉：{err}')
            final += els
        for e in final:
            e.pop('_zgroup', None); e.pop('_zsrcbox', None)
        zoom_els = final
    images += zoom_els
    a2 = ctx.get('accent2')
    if a2:                                              # 第二强调色：约三成页面的高亮词、强调句换成它
        v2_ = vary(i, page, ctx)
        for t in texts:
            role = t.get('text_role')
            if role in ('body', 'foot') and v2_['accent2_hl']:
                t['accent'] = a2
            elif role == 'emphasis' and v2_['accent2_emph'] and t.get('fill') == accent:
                t['fill'] = a2
    v = vary(i, page, ctx)
    if v['ghost'] and not any(e.get('kind') == 'dark_backdrop' for e in images):
        # 暗影底图：把这页的主图放大、压暗、偏旧色，铺满整页当底，像原版那样不是纯黑底
        src = page['ghost'] if isinstance(page.get('ghost'), dict) else (
            page.get('hero') or next(iter(page.get('images', [])), None))
        if src:
            g = {k: v_ for k, v_ in src.items() if k not in ('cut', 'label', 'h', 'w', 'as', 'side', 'bleed', 'inset', 'dy', 'overlay')}
            ge = backdrop(g, min(0.70, page.get('ghost_darken', 0.70)))   # 检查规则：整版压暗 30–70%
            ge.update(face_boxes=[], role='background', ghost=True,
                      effects=['sepia'] if ctx.get('ghost_tone', 'sepia') == 'sepia' else [], opacity=1)
            images.insert(0, ge)
    texts += place_labels(images, texts, root, accent, ctx)
    k = 0
    for e in images:                                    # 描边/发光：按全篇设定隔张使用
        if e.get('kind') != 'image':
            continue
        apply_fx(e, 'cut' if e.get('role') == 'foreground' else 'rect', k, ctx, page, accent)
        k += 1
    ctx['fx_phase'] = ctx.get('fx_phase', 0) + 1
    if target and page.get('arrow', True) and ctx.setdefault('arrows', 0) < ctx.get('max_arrows', 6):
        emp = next((t for t in texts if t['text_role'] == 'emphasis'), None)
        if emp:
            a = arrow_to(emp, target, occ, texts, cfg, accent)
            if a:
                images.append(a); ctx['arrows'] += 1
    hero_id = next((e.get('source_id') for e in images if e.get('hero')), None) or next((e.get('source_id') for e in images if e.get('source_id')), '')
    pos = '+'.join(f"{round(t['box'][0], 2)},{round(t['box'][1], 2)}" for t in texts[:4])
    if not page.get('_dry'):
        for e in images:
            for k_ in [k_ for k_ in e if k_.startswith('_')]:
                e.pop(k_)
    p = {'layout': 'collage', 'background': '#000000', 'watermark': True, 'skeleton': lay, 'style': 'v2',
         'text_position': pos, 'visual_focus': hero_id, 'elements': images + texts}
    text_bottom = max((t['box'][1] + t['box'][3] for t in texts), default=0)
    return p, {'layout': lay, 'columns': [{'leftover': round(max(0, BOTTOM - text_bottom), 3)}]}
