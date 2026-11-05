"""AI 科技线手排工具（照 ELIZA 的做法；cy-carousel 的 scripts/手排.py 与项目「共享工具/手排.py」是同一份）。加了照片卡、扫描页裁条、整页压暗底图和人名标签。

用法：
    import 手排 as S
    S.init(笔记目录)                       # 素材路径都相对这个目录
    cv = S.Canvas(); cv.put(S.photo('assets/x.jpg', 900, rotate=-2), 500, 300); c = cv.save('P01')
    S.pages.append(S.page(c, [S.headline('第一行，\\n[[第二行]]', 0.035, 0.022, 118), ...], backdrop=S.backdrop('assets/y.jpg', 0.6)))
    S.write_script(topic)

约定：
- 拼贴图透明底，页面底色 #080808（红线检查按 ≤8 算纯黑）；整页压暗的照片用 render 的 dark_backdrop（darken 0.30–0.70），不烤进拼贴。
- 图片等比缩放，放大不超过 1.25 倍；毛笔标题里的英文和数字自动换成黑体（render 的 latin_font）。
- 论文 PDF 用矢量渲染（strip）；扫描书页用位图裁条（scan_strip），关键词框用 macOS Vision（ocrfind）。
- 正文字体按题材选（body(font=...)，候选见 BODY_FONTS），一篇只用一款；typo=True 打开标点与混排规则，
  justify=True 两端对齐，hscale 横向压缩（参照账号正文约 0.95）。细节见 references/排字细节.md。
- 图层顺序：Canvas(split_shadow=True) + page(..., layer_order='text-under-images') 得到「底色 → 投影 → 文字 → 图片」。
- emoji(text, size)：组合 emoji（1️⃣ 👉）用 AppKit 渲染成透明 PNG（scripts/emoji.swift，首次自动编译到 bin/）。
"""
import json, math, random, shutil, subprocess, sys
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
SK = HERE if (HERE / 'build.py').exists() else HERE.parents[2] / 'skills/cy-carousel/scripts'   # 放在 Skill 的 scripts/ 里时直接用同目录
sys.path.insert(0, str(SK))
import build as T

W, H = 1440, 1920
CREAM, CYAN, INK, RED = '#F3F1E9', '#00E5FF', '#10242B', (229, 57, 53)
PAGE_BG = '#080808'
T.CFG['accent'] = CYAN
OCR = HERE / 'bin/ocrfind'
EMOJI = HERE / 'bin/emoji'
# 正文字体候选：名字 → (render 字体 key, 默认描边加粗 px)。先做同字对比小样（font_sample）选一款，一篇只用一款。
BODY_FONTS = {
    '宋体粗': ('serif-bold', 1),        # 默认：思源宋体 Bold + 1px 描边（ELIZA 以来的正文）
    '宋体': ('songti-sc', 0),           # 宋体-简 Regular（Songti SC）：文史、旧报纸气质
    '仿宋': ('fangsong', 0),            # 华文仿宋：档案、公文、民国感
    '楷体': ('kaiti', 0),               # 楷体-简：书信、手记
    '文楷': ('wenkai', 0),              # 霞鹜文楷 Medium（需放进 assets/fonts/ 或系统字体目录）
    '苹方细': ('pingfang-light', 0),    # 苹方 Light：现代、产品、轻量
}
NOTE = OUT = None
PROTECT = []
pages = []
PDF_DOCS = {}


def _doc(pdf):
    """同一 PDF 一次手排会话只 open 一次；snap/pdf_crop/find/strip 都走这里，别每个辅助函数各开一遍。"""
    p = str(NOTE / pdf)
    d = PDF_DOCS.get(p)
    if d is None:
        d = PDF_DOCS[p] = pymupdf.open(p)
    return d


def init(note, protect=(), out='collage'):
    global NOTE, OUT, PROTECT
    for d in PDF_DOCS.values():          # 换笔记目录时关掉上一轮缓存的 PDF，句柄不累积
        d.close()
    PDF_DOCS.clear()
    NOTE = Path(note); OUT = NOTE / out; OUT.mkdir(parents=True, exist_ok=True)
    PROTECT = list(protect)


def _ensure_tool(binary, source, purpose):
    """macOS 专用的 Swift 工具，真正用到时才编译；非 macOS 或没有 swiftc 时给出明确报错。"""
    if binary.exists():
        return
    if sys.platform != 'darwin' or shutil.which('swiftc') is None:
        raise RuntimeError(f'{purpose}依赖 macOS 的 Swift 工具链（swiftc），当前环境不可用；不需要{purpose}的手排功能不受影响')
    binary.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['swiftc', '-O', str(HERE / source), '-o', str(binary)], check=True)


# ---------------------------------------------------------------- 手绘圈、纸卡

def hand_circle(im, box, color=RED, width=None):
    """在图上画手绘感的圈（两笔，略有偏移）。box 为像素坐标 [x0,y0,x1,y1]。"""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    px, py = w * 0.05 + 12, h * 0.20 + 5             # 纵向收紧，少压上下行
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, w / 2 + px, h / 2 + py
    width = width or max(5, round(h * 0.11))
    rng = random.Random(int(x0 + y0))
    for k in range(2):
        pts = []
        start = rng.uniform(-0.4, 0.2)
        for j in range(150):
            t = start + j / 140 * (2 * math.pi + 0.35)
            jr = 1 + 0.025 * math.sin(3 * t + k) + k * 0.02
            pts.append((cx + rx * jr * math.cos(t), cy + ry * jr * math.sin(t)))
        d.line(pts, fill=color, width=width, joint='curve')


def underline(im, box, color=RED, width=None):
    """手绘下划线（略带弧度的两笔）。"""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    width = width or max(5, round((y1 - y0) * 0.12))
    rng = random.Random(int(x0 * 7 + y1))
    for k in range(2):
        pts = [(x0 - 6 + (x1 - x0 + 12) * t / 40, y1 + 4 + k * 4 + 3 * math.sin(math.pi * t / 40) + rng.uniform(-1, 1)) for t in range(41)]
        d.line(pts, fill=color, width=width, joint='curve')


def card(im, target_w, rotate=0.0, shadow=True, allow_up=1.25):
    """等比缩放到 target_w（放大不超过 1.25 倍），可轻微倾斜，带柔影。"""
    s = target_w / im.width
    if s > allow_up + 1e-6:
        raise ValueError(f'放大 {s:.2f} 倍，超过 {allow_up}：换高清图或缩小')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS).convert('RGBA')
    if rotate:
        im = im.rotate(rotate, resample=Image.BICUBIC, expand=True)
    if not shadow:
        return im
    pad = 40
    sh = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad))
    a = Image.new('L', sh.size); a.paste(im.getchannel('A'), (pad + 10, pad + 14))
    a = a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: v * 0.6)
    blk = Image.new('RGBA', sh.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk)
    face = Image.new('RGBA', sh.size); face.alpha_composite(im, (pad, pad))
    sh.alpha_composite(im, (pad, pad))
    sh.cy_layers = (blk, face)                          # 阴影层、纸面层（同尺寸），Canvas(split_shadow=True) 用
    return sh


# ---------------------------------------------------------------- 照片、扫描页、论文 PDF

def load(path, crop=None):
    """crop 为 0–1 坐标 [x0,y0,x1,y1]。"""
    im = Image.open(NOTE / path); im = ImageOps.exif_transpose(im).convert('RGB')
    if crop:
        im = im.crop((round(crop[0] * im.width), round(crop[1] * im.height), round(crop[2] * im.width), round(crop[3] * im.height)))
    return im


def photo(path, target_w, crop=None, rotate=0.0, circles=(), shadow=True, sepia=False):
    """照片卡：矩形、柔影、可倾斜。circles 为原图 0–1 框，画红圈。"""
    im = load(path, crop)
    if sepia:
        im = ImageOps.colorize(ImageOps.grayscale(im), '#1a140e', '#f2e6cf')
    for c in circles:
        bx = _rel(c, crop, im.size)
        hand_circle(im, bx)
    return card(im, target_w, rotate=rotate, shadow=shadow)


def _rel(b, crop, size):
    """原图 0–1 框 → 裁后像素框。"""
    cx0, cy0, cx1, cy1 = crop or (0, 0, 1, 1)
    sx, sy = size
    return [(b[0] - cx0) / (cx1 - cx0) * sx, (b[1] - cy0) / (cy1 - cy0) * sy,
            (b[2] - cx0) / (cx1 - cx0) * sx, (b[3] - cy0) / (cy1 - cy0) * sy]


def ocr(path, *terms):
    """Vision 词框：返回 [{term,line,box:[x0,y0,x1,y1]}]，0–1 左上原点。"""
    _ensure_tool(OCR, 'ocrfind.swift', 'OCR 词框（ocrfind）')
    r = subprocess.run([str(OCR), str(NOTE / path), *terms], capture_output=True, text=True, encoding='utf-8', check=True)
    out = json.loads(r.stdout)
    for o in out:
        x, y, w, h = o['box']; o['box'] = [x, y, x + w, y + h]
    return out


def scan_strip(path, crop, target_w, circles=(), unders=(), whiteout=(), bars=(), rotate=0.0, pad=18, vpad=24, paper=None):
    """扫描书页/报纸裁一两行放大成纸条。circles/unders/whiteout 可以是 OCR 词（字符串）或原图 0–1 框。
    whiteout：把裁区里不想要的半句（例如被切开的前一句）涂成纸色。标记在加白边之后画，不会被裁掉。"""
    im = load(path, crop)
    fill = paper or _paper(im)
    ImageDraw.Draw(im).rectangle([0, 0, im.width, 5], fill=fill)            # 上下边 6px 刷成纸色：去掉相邻行露出来的笔画碎片
    ImageDraw.Draw(im).rectangle([0, im.height - 6, im.width, im.height], fill=fill)
    terms = [t for t in (*whiteout, *circles, *unders, *bars) if isinstance(t, str)]
    ocr_hits = ocr(path, *terms) if terms else []          # ocrfind 一次收多个词，别一个词跑一遍 Vision
    def box_of(c):
        if not isinstance(c, str):
            return c
        hits = [o for o in ocr_hits if o['term'] == c and _inside(o['box'], crop)]
        if not hits:
            raise ValueError(f'OCR 在裁区里找不到「{c}」')
        return hits[0]['box']
    dr = ImageDraw.Draw(im)
    for c in whiteout:
        b = _rel(box_of(c), crop, im.size)
        dr.rectangle([b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3], fill=fill)
    marks = ([('c', _rel(box_of(c), crop, im.size)) for c in circles] + [('u', _rel(box_of(c), crop, im.size)) for c in unders]
             + [('b', _rel(box_of(c), crop, im.size)) for c in bars])
    px = max(pad, math.ceil((target_w / 1.25 - im.width) / 2))      # 纸面宽、字少时，横向多留纸边，原图放大不超过 1.25 倍
    im = ImageOps.expand(im, border=(px, vpad, px, vpad), fill=fill)
    for kind, b in marks:
        b = [b[0] + px, b[1] + vpad, b[2] + px, b[3] + vpad]
        if kind == 'b':                                              # 行距太密时：在行首左边画一道红竖线
            ImageDraw.Draw(im).line([(b[0] - 18, b[1] - 2), (b[0] - 18, b[3] + 2)], fill=RED, width=9)
        else:
            (hand_circle if kind == 'c' else underline)(im, b)
    return card(im, target_w, rotate=rotate)


def _inside(b, crop):
    cx = (b[0] + b[2]) / 2; cy = (b[1] + b[3]) / 2
    return crop[0] <= cx <= crop[2] and crop[1] <= cy <= crop[3]


def _paper(im):
    """纸面颜色：每个通道取 90 分位（避开文字的深色），补的纸边才和原纸一样白。"""
    out = []
    for ch in im.convert('RGB').split():
        h = ch.histogram(); n = sum(h); acc = 0
        for v in range(256):
            acc += h[v]
            if acc >= 0.9 * n:
                out.append(v); break
    return tuple(out)


def pdf_crop(pdf, pno, rect, zoom=6):
    p = _doc(pdf)[pno]
    pw, ph = p.rect.width, p.rect.height
    clip = pymupdf.Rect(rect[0] * pw, rect[1] * ph, rect[2] * pw, rect[3] * ph)
    pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    def to_px(b):
        return [(b[0] - rect[0]) * pw * zoom, (b[1] - rect[1]) * ph * zoom, (b[2] - rect[0]) * pw * zoom, (b[3] - rect[1]) * ph * zoom]
    return im, to_px


def find(pdf, pno, phrase, nth=0):
    p = _doc(pdf)[pno]
    r = p.search_for(phrase)[nth]
    return [r.x0 / p.rect.width, r.y0 / p.rect.height, r.x1 / p.rect.width, r.y1 / p.rect.height]


def snap(pdf, pno, rect):
    """左右边挪到最近的词间空白，不切半个词。"""
    p = _doc(pdf)[pno]
    pw, ph = p.rect.width, p.rect.height
    ws = [(w[0] / pw, w[2] / pw) for w in p.get_text('words') if rect[1] < (w[1] + w[3]) / 2 / ph < rect[3]]
    ok = lambda x: not any(a < x < b for a, b in ws)
    def near(x):
        c = [x + d / 1000 for d in range(-50, 51) if ok(x + d / 1000)]
        return min(c, key=lambda v: abs(v - x)) if c else x
    return [near(rect[0]), rect[1], near(rect[2]), rect[3]]


def strip(pdf, pno, rect, target_w, circles=(), cyan=(), unders=(), whiteout=(), rotate=0.0, pad=18, vpad=None):
    """论文里一两行原文，按目标宽度矢量渲染，关键词画红圈，做成白色纸条。边上切开的半个词涂白。"""
    rect = snap(pdf, pno, rect)
    pg = _doc(pdf)[pno]
    zoom = (target_w - 2 * pad) / ((rect[2] - rect[0]) * pg.rect.width)
    im, f = pdf_crop(pdf, pno, rect, zoom=zoom)
    dr = ImageDraw.Draw(im)
    for w in pg.get_text('words'):
        b = [w[0] / pg.rect.width, w[1] / pg.rect.height, w[2] / pg.rect.width, w[3] / pg.rect.height]
        if not rect[1] < (b[1] + b[3]) / 2 < rect[3]:
            continue
        x0, y0, x1, y1 = f(b)
        if b[0] < rect[2] < b[2]:
            dr.rectangle([x0 - 4, y0 - 2, im.width, y1 + 2], fill='white')
        if b[0] < rect[0] < b[2]:
            dr.rectangle([0, y0 - 2, x1 + 4, y1 + 2], fill='white')
    for w in pg.get_text('words'):                      # 上下被切进来的半行也涂白
        b = [w[0] / pg.rect.width, w[1] / pg.rect.height, w[2] / pg.rect.width, w[3] / pg.rect.height]
        cy = (b[1] + b[3]) / 2
        if rect[0] < b[2] and b[0] < rect[2] and not rect[1] < cy < rect[3] and b[1] < rect[3] and b[3] > rect[1]:
            x0, y0, x1, y1 = f(b)
            dr.rectangle([x0 - 2, max(0, y0 - 2), x1 + 2, min(im.height, y1 + 2)], fill='white')
    for ph in whiteout:                                 # 不想要的半句（例如上一句的尾巴）涂白
        for r in pg.search_for(ph):
            bb = [r.x0 / pg.rect.width, r.y0 / pg.rect.height, r.x1 / pg.rect.width, r.y1 / pg.rect.height]
            if bb[2] > rect[0] and bb[0] < rect[2] and bb[3] > rect[1] and bb[1] < rect[3]:
                x0, y0, x1, y1 = f(bb)
                dr.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], fill='white')
    vp = pad if vpad is None else vpad
    im = ImageOps.expand(im, border=(pad, vp, pad, vp), fill='white')
    def g(c):
        b = f(find(pdf, pno, c) if isinstance(c, str) else c)
        return [b[0] + pad, b[1] + vp, b[2] + pad, b[3] + vp]
    for c in circles:
        hand_circle(im, g(c))
    for c in cyan:
        hand_circle(im, g(c), color=(0, 229, 255))
    for c in unders:
        underline(im, g(c))
    return card(im, im.width, rotate=rotate)


class Canvas:
    """透明底拼贴层；页面底色和整页压暗底图交给 render。
    split_shadow=True：卡片的柔影单独存成 名字_shadow.png，配合 page(..., layer_order='text-under-images')
    得到「底色 → 投影 → 文字 → 图片」，图片可以压住文字边缘。默认 False，与原来逐张叠放完全一样。"""
    def __init__(self, split_shadow=False):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.split = split_shadow
        self.shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)) if split_shadow else None

    def put(self, img, x, y, clamp=True, bleed=None):
        """bleed='right'/'left'：贴页边出血（卡片自带 40px 阴影边，纸面越出页边约 24px）；'full'：左右都出血、水平居中。"""
        x = round(x); y = round(y)
        if bleed == 'right':
            x = W - img.width + 64
        elif bleed == 'left':
            x = -64
        elif bleed == 'full':
            x = (W - img.width) // 2
        elif clamp:                                     # 不出页面右边：纸面离右边至少 48px
            x = min(x, W - img.width + 40 - 48)
        layers = getattr(img, 'cy_layers', None) if self.split else None
        if layers:
            self.shadow.alpha_composite(layers[0], (x, y)); self.im.alpha_composite(layers[1], (x, y))
        else:
            self.im.alpha_composite(img, (x, y))
        return [x / W, y / H, img.width / W, img.height / H]

    def save(self, name):
        p = OUT / f'{name}.png'; self.im.save(p)
        if self.split:
            self.shadow.save(OUT / f'{name}_shadow.png')
        return str(p.relative_to(NOTE))


# ---------------------------------------------------------------- 文字元素

def _hs(e, hscale):
    """文字层横向压缩（1.0 = 不压缩；参照账号正文约 0.95）。"""
    if hscale != 1:
        e['hscale'] = hscale
    return e


def headline(text, x, y, size, w=0.92, font='headline', hscale=1.0):
    e = {'kind': 'text', 'text': text, 'box': [x, y, w, 0.3], 'size': size, 'font': font, 'fill': CREAM,
         'accent': CYAN, 'spacing': 0, 'lineheight': round(size * 1.26), 'text_role': 'headline',
         'effect': '3d', 'depth': 7, 'bold': 1, 'shadow_color': '#0C0C0C', 'tight_punctuation': 'all',
         'latin_font': 'sans-black', 'latin_scale': 0.92}          # 毛笔字里的英文、数字用黑体
    e['box'][3] = round((text.count('\n') + 1) * e['lineheight'] / H + 12 / H, 4)
    return _hs(e, hscale)


def big(text, x, y, size, fill=CYAN, w=0.92, align='left', hscale=1.0):
    e = {'kind': 'text', 'text': text, 'box': [x, y, w, 0.3], 'size': size, 'font': 'sans-black', 'fill': fill,
         'spacing': 0, 'lineheight': round(size * 1.22), 'text_role': 'emphasis', 'align': align,
         'effect': '3d', 'depth': 7, 'bold': 1, 'shadow_color': '#0C0C0C'}
    e['box'][3] = round((text.count('\n') + 1) * e['lineheight'] / H + 12 / H, 4)
    return _hs(e, hscale)


def _fill_wrap(e, para):
    """两端对齐用的满行断行：按词（jieba/保护词）往行里塞，塞不下才换行；行首避开收尾标点（交给 render 悬挂）。
    T.wrap 按分句断，行尾参差大，拉齐会出现大窟窿。"""
    latin = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%.+-/')
    atoms = []
    for a in T.atoms(para, PROTECT):                          # 「12+7」「GPT-4o」不拆；开引号、【 不留在行尾
        if atoms and ((atoms[-1][-1] in latin and a[0] in latin) or atoms[-1][-1] in T.OPENING | set('【')):
            atoms[-1] += a
        else:
            atoms.append(a)
    lines, cur = [], ''
    for a in atoms:
        if not cur or T.fits(e, cur + a) or a[0] in T.CLOSING:
            cur += a; continue
        if not T.fits(e, a):                                  # 单个词就放不下：按字拆
            for ch in a:
                if T.fits(e, cur + ch) or ch in T.CLOSING:
                    cur += ch
                else:
                    lines.append(cur.rstrip()); cur = ch
            continue
        lines.append(cur.rstrip()); cur = a.lstrip()
    if cur:
        lines.append(cur.rstrip())
    while len(lines) >= 2 and T.visible_len(lines[-1]) < 3 and len(lines[-2]) > 3:   # 防孤字：挪一个字下来
        lines[-2], lines[-1] = lines[-2][:-1], lines[-2][-1] + lines[-1]
    return lines


def body(text, x, y, w, size=60, fill=CREAM, bg=None, font='宋体粗', hscale=1.0, typo=False, justify=False,
         stroke=None, latin_scale=None, tight=None):
    """正文。font：BODY_FONTS 里的名字（宋体粗/宋体/仿宋/楷体/文楷/苹方细）或 render 的字体 key。
    typo=True：破折号画两段细线、省略号画三个等距圆点、【】约 0.44em、「·」约 0.3em、数字和拉丁字母换 Times 并放大
    1.07（latin_scale 可改，建议 1.05–1.10）。justify=True：两端对齐（段末行不动；含空格的行只拉空格）。
    hscale：横向压缩。stroke：描边加粗 px，默认按字体（宋体粗 1，其他 0）。
    tight：标点按墨迹收紧（'all'）；默认宋体粗收紧（原样），换了字体就用字库自带的全角标点（False）。
    不传这些参数时与原来完全一样。"""
    key, st = BODY_FONTS.get(font, (font, 0))
    e = {'kind': 'text', 'text': text, 'box': [x, y, w, 0.5], 'size': size, 'font': key, 'fill': fill,
         'accent': CYAN, 'stroke': st if stroke is None else stroke, 'spacing': 0, 'lineheight': round(size * (1.45 if bg else 1.3)), 'text_role': 'body',
         'tight_punctuation': ('all' if key == 'serif-bold' else False) if tight is None else tight}
    if bg:
        e['bg'] = bg
    if typo:
        e['typo'] = True
        if latin_scale:
            e['latin_scale'] = latin_scale
    _hs(e, hscale)
    e['box'][2] = w * 0.97
    if justify:
        out, soft = [], []
        for para in text.split('\n'):
            ls = _fill_wrap(e, para)
            soft += [len(out) + k for k in range(len(ls) - 1)]
            out += ls
        e['text'], e['justify'], e['soft_breaks'] = '\n'.join(out), True, soft
    else:
        e['text'] = T.wrap(e, text, PROTECT)
    e['box'][2] = w
    e['box'][3] = round((e['text'].count('\n') + 1) * e['lineheight'] / H + 10 / H, 4)
    return e


def sticker(text, x, y, size=64):
    """青色问句贴条，黑字。"""
    return {'kind': 'text', 'text': text, 'box': [x, y, 0.9, round(size * 1.3 / H + 10 / H, 4)], 'size': size,
            'font': 'sans-black', 'fill': INK, 'bg': CYAN, 'spacing': 0, 'lineheight': round(size * 1.3),
            'text_role': 'note', 'tight_punctuation': 'all'}


def label(text, x, y, size=32):
    """人名/物件标签：黑底白字小块（不写出处）。"""
    return {'kind': 'text', 'text': text, 'box': [x, y, len(text) * (size + 2) / W + 0.02, round(size * 1.4) / H], 'size': size,
            'font': 'sans-bold', 'fill': '#FFFFFF', 'bg': '#000000', 'lineheight': round(size * 1.4), 'spacing': 1,
            'tight_punctuation': 'all', 'text_role': 'label'}


def bottom(e):
    return e['box'][1] + e['box'][3]


# ---------------------------------------------------------------- 页面

def backdrop(path, darken, focus=(0.5, 0.4), crop=None, faces=(), y=0.0, h=1.0, fade=None):
    """整页（或上半页带羽化）压暗照片，darken 0.30–0.70。faces 为原图 0–1 [x,y,w,h]。"""
    e = {'kind': 'dark_backdrop', 'path': path, 'box': [0, y, 1, h], 'fit': 'cover', 'darken': darken, 'role': 'background',
         'cover_only': True, 'focus': list(focus), 'source_id': Path(path).stem,
         'face_boxes': [list(f) for f in faces], 'face_detection_method': 'vision+manual'}
    if fade is not None or h < 1:
        e['fade_fraction'] = fade if fade is not None else 0.25
    else:
        e['fade_fraction'] = 0
    if crop:
        e['crop'] = list(crop)
    return e


def page(collage, els, layout='collage', backdrop=None, layer_order='default'):
    """layer_order='text-under-images'：底色 → 整页底图 → 卡片投影 → 文字 → 拼贴图片（图片可压文字边缘）。
    拼贴要用 Canvas(split_shadow=True) 存，投影才会单独在文字下面；否则投影跟着图片压在文字上。"""
    bgs = [backdrop] if backdrop else []
    img = lambda path, **kw: {'kind': 'image', 'path': path, 'box': [0, 0, 1, 1], 'fit': 'cover', 'role': 'background',
                              'source_id': Path(path).stem, 'face_boxes': [], 'face_detection_method': 'manual-verified', **kw}
    col = [img(collage)] if collage else []
    if layer_order == 'text-under-images' and collage:
        sh = str(Path(collage).with_name(Path(collage).stem + '_shadow.png'))
        if (NOTE / sh).exists():
            under = [img(sh, coverage=False)]
        else:
            print(f'提示：{sh} 不存在（Canvas 要 split_shadow=True 存），这页拼贴没有投影层', file=sys.stderr)
            under = []
        return {'layout': layout, 'background': PAGE_BG, 'watermark': layout != 'cover', 'layer_order': layer_order,
                'elements': bgs + under + els + [img(collage, above_text=True)]}
    if layer_order not in ('default', 'text-under-images'):
        raise ValueError('layer_order 只能是 default 或 text-under-images')
    return {'layout': layout, 'background': PAGE_BG, 'watermark': layout != 'cover', 'elements': bgs + col + els}


def emoji(text, size):
    """组合 emoji（1️⃣ 2️⃣ 👉 ⚠️ …）→ 透明 RGBA 图，墨迹裁边，高度约等于字号 size（px）。用 Canvas.put 摆。
    PIL 画不全 keycap 等组合序列，所以交给 AppKit（scripts/emoji.swift，首次自动编译到 bin/emoji）。"""
    import tempfile
    _ensure_tool(EMOJI, 'emoji.swift', '组合 emoji 渲染')
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'e.png'
        subprocess.run([str(EMOJI), text, str(out), str(size * 2)], check=True, capture_output=True)
        im = Image.open(out).convert('RGBA'); im.load()
    bb = im.getchannel('A').getbbox()
    if not bb:
        raise ValueError(f'emoji 渲染为空：{text!r}')
    im = im.crop(bb)
    return im.resize((max(1, round(im.width / 2)), max(1, round(im.height / 2))), Image.LANCZOS)


def font_sample(text, out, fonts=tuple(BODY_FONTS), size=60, w=1360, bg=PAGE_BG, fill=CREAM, **kw):
    """同字对比小样：同一句话用几款正文字体各排一行（左边标字体名），存成 PNG，先看再选，一篇只用一款。
    kw 传给 body（typo/hscale/justify 等）。找不到的字体标「本机没有」。"""
    import render as RD
    from PIL import ImageFont
    rows = []
    for name in fonts:
        try:
            e = body(text, 0.02, 0.0, w / W, size=size, fill=fill, font=name, **kw)
            lay = Image.new('RGBA', (W, round(e['box'][3] * H) + 20)); RD.draw_text(lay, e, T.CFG, W, H, [])
            rows.append((name, lay))
        except (OSError, ValueError, FileNotFoundError) as ex:
            rows.append((name, None))
    lab = ImageFont.truetype(str(HERE.parent / 'assets/fonts/NotoSansSC[wght].ttf'), 28)
    hh = sum((r.height if r else 60) + 50 for _, r in rows) + 20
    c = Image.new('RGBA', (W, hh), bg); d = ImageDraw.Draw(c); y = 16
    for name, r in rows:
        d.text((28, y), name + ('' if r else '：本机没有'), font=lab, fill='#8A8A8A'); y += 44
        if r:
            c.alpha_composite(r, (0, y)); y += r.height
        else:
            y += 60
    c.convert('RGB').save(out)
    return out


def write_script(topic, built_by, path='页面脚本.json', account=None):
    """account：水印和署名用的账号名。不传就写占位符 {账号名}，打包清单会标 placeholder_account。"""
    if not account:
        print('提示：write_script 没传 account，水印会印占位符「账号名」；发布前用 account=\'你的账号名\' 重新生成', file=sys.stderr)
    script = {'schema_version': 1, 'built_by': built_by, 'topic': topic, 'tone': '暗', 'mode': 'production',
              'config': {'tone': '暗', 'accent': CYAN, 'background': PAGE_BG,
                         'account_name': account or '{账号名}', 'watermark_text': account or '账号名',
                         'watermark_style': 'neutral', 'bookmark': False, 'cover_only': False, 'require_face_every_page': False},
              'delivery': {'main_cover': 'D', 'size': [W, H]}, 'pages': pages}
    (NOTE / path).write_text(json.dumps(script, ensure_ascii=False, indent=1),encoding='utf-8')
    return len(pages)


def preview(pages_dir, out):
    ps = sorted(Path(pages_dir).glob('p*.png'))
    tw, th, g = 460, 613, 14
    rows = math.ceil(len(ps) / 4)
    c = Image.new('RGB', (4 * tw + 5 * g, rows * th + (rows + 1) * g), (230, 230, 230))
    for i, p in enumerate(ps):
        im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
        c.paste(im, (g + (i % 4) * (tw + g), g + (i // 4) * (th + g)))
    c.save(out, quality=88)
