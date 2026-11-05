"""AI 分支第 4 篇：聪明的汉斯 → 聪明汉斯效应。照 ELIZA 的做法手排（共享工具/手排.py）：
照片和纸条不倾斜、贴边出血，一页一个主角；青色大数字；问句贴条；原文纸条只截关键一两行。
输出 页面脚本.json、collage/Pxx.png；渲染：
    python3 ../../../skills/cy-carousel/scripts/render.py 页面脚本.json --out pages --assets-root .
每句文案的出处见 research/事实表.md（括号里是条目号）；书页短语框由 OCR（ocrfind）现找，论文用 PDF 文字层。"""
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'scripts'))       # 在 Skill 的 examples/ 里：用 scripts/手排.py
sys.path.insert(0, str(HERE.parent / '共享工具'))            # 在原项目里：用 AI分支/样稿/共享工具/手排.py
import 手排 as S
from 手排 import W, H, CREAM, headline, big, body, sticker, label, bottom, page, backdrop

S.init(HERE, protect=['Clever Hans', 'Fisher Vector', 'BERT', 'von Osten', 'Pfungst', 'NIH', 'AUC'])
C = 'assets/commons/'
SC = 'assets/scans/'
PF = {k: SC + v for k, v in {
    'cards': 'pfungst1911_leaf0044_p035_number_cards.png',
    'blind': 'pfungst1911_leaf0052_p043_blinders.png',
    'p40': 'pfungst1911_p040_neither_read.png',
    'mm': 'pfungst1911_leaf0113_p104_one_millimeter.png',
    'self': 'pfungst1911_leaf0245_p236_pure_self_deception.png',
    'self0': 'pfungst1911_leaf0244_p235_self_deception_lead.png',
    'sep': 'pfungst1911_leaf0263_p254_report_sept12_signatures.png',
}.items()}
FULL = 1490                      # 满宽纸条的纸面宽度（左右各越出页边约 25px）
pages = S.pages


def flow(text, y, size=84, fill=CREAM, w=0.93):
    """大字流程行（黑体，[[ ]] 里的词用电子青）。"""
    return big(text, 0.035, y, size, fill=fill, w=w)


# ---------------------------------------------------------------- 封面：院子里，马被问「楼梯上站了几个人」（照片说明）
cv = S.Canvas()
hof = S.load(C + 'Hans_auf_dem_Hof.jpg')
cw = round(hof.height * 0.75)
cov = hof.crop((hof.width - cw, 0, hof.width, hof.height)).resize((W, H), Image.LANCZOS)
S.hand_circle(cov, [40, 80, 380, 540], width=9)                 # 楼梯顶平台上的三个人
cov = cov.convert('RGBA')
grad = Image.linear_gradient('L').resize((W, H)).point(lambda v: 0 if v < 120 else min(235, int((v - 120) * 2.0)))
shade = Image.new('RGBA', (W, H), (8, 8, 8, 255)); shade.putalpha(grad)
cov.alpha_composite(shade)
cv.put(cov, 0, 0, clamp=False)
c0 = cv.save('P00')
q = {'kind': 'text', 'text': '考题：楼梯上站了几个人？\n其中几个戴着帽子？', 'box': [0.40, 0.035, 0.57, 0.105], 'size': 54,
     'font': 'sans-black', 'fill': CREAM, 'bg': '#080808', 'lineheight': 76, 'spacing': 0, 'text_role': 'note',
     'tight_punctuation': 'all'}
cover = page(c0, [q,
                  {**headline('一匹会算数的马，', 0.055, 0.735, 116), 'font': 'cover-title'},
                  {**headline('[[AI 也会这一招]]', 0.055, 0.83, 156), 'font': 'cover-title'}], layout='cover')
pages.append(cover)

# ---------------------------------------------------------------- P1 柏林有匹马（F01 F03 F04 F06 F08–F10）
cv = S.Canvas()
h = headline('柏林有匹马，\n[[会算数，还会认字]]', 0.035, 0.022, 118)
news = cv.put(S.photo(C + 'Hans_Berliner_Morgenpost.jpg', 920, crop=(0.0, 0.0, 1.0, 0.86)), 0, bottom(h) * H + 10, bleed='right')
c1 = cv.save('P01')
t1 = body('当过数学老师的冯·奥斯腾，每天中午在柏林一个院子里免费表演：他出题，马用右前蹄敲出答案。', 0.035, bottom(h) + 0.025, 0.36, 56)
t2 = body('报纸为它吵了好几个月，它还上了流行小调、明信片和酒标。', 0.035, news[1] + news[3] + 0.02, 0.93, 64)
pages.append(page(c1, [h, t1, t2,
                       big('1904', 0.035, bottom(t1) + 0.02, 170, w=0.36),
                       sticker('马真会算数？', 0.035, bottom(t2) + 0.035, 76),
                       label('1904年的柏林报纸：一匹神马', news[0] + 0.04, news[1] + news[3] - 0.075)]))

# ---------------------------------------------------------------- P2 13 人委员会（F14 F16–F18）
cv = S.Canvas()
h = headline('请人来查，\n[[也没查出破绽]]', 0.035, 0.022, 118)
sig = cv.put(S.scan_strip(PF['sep'], [0.24, 0.475, 0.92, 0.855], 820, bars=['PAUL', 'PROF. C']), 0, bottom(h) * H, bleed='right')
bg1 = big('13 人\n签字', 0.035, bottom(h) + 0.02, 170, w=0.40)
t1 = body('1904年9月，马戏团经理、动物园园长、心理学家等13人联名：没发现任何暗号。', 0.035, bottom(bg1) + 0.01, 0.36, 54)
inv = cv.put(S.scan_strip(PF['sep'], [0.10, 0.418, 0.82, 0.452], FULL, unders=['incisive investigation'], pad=70), 0,
             max(sig[1] + sig[3], bottom(t1)) * H + 20, bleed='full')
c2 = cv.save('P02')
t2 = body('可他们没说马会思考，只说这事值得认真研究。', 0.035, inv[1] + inv[3] + 0.005, 0.93, 60)
pages.append(page(c2, [h, bg1, t1, t2, sticker('连马戏团经理都没看穿？', 0.035, bottom(t2) + 0.03, 64)]))

# ---------------------------------------------------------------- P3 第一招：提问的人也不知道答案（F26 F27）
cv = S.Canvas()
h = headline('第一招：\n[[出题的人也不知道答案]]', 0.035, 0.022, 112)
b3 = big('98% → 8%', 0.035, bottom(h) + 0.005, 200)
s1 = cv.put(S.scan_strip(PF['cards'], [0.10, 0.283, 0.91, 0.338], FULL, unders=['8%', '98%'], pad=70), 0, bottom(b3) * H, bleed='full')
t1 = body('数字卡只给马看，在场的人都看不见。提问者知道答案时对98%，不知道时只对8%。', 0.035, s1[1] + s1[3] + 0.005, 0.93, 56)
tb = cv.put(S.scan_strip(PF['cards'], [0.17, 0.432, 0.91, 0.497], 1150, unders=[[0.802, 0.459, 0.832, 0.474]]), 0, bottom(t1) * H + 30, bleed='left')
st = cv.put(S.photo(C + 'Karl_Stumpf._Photogravure_by_Synnberg_Photo-gravure_Co.,_189_Wellcome_L0023071.jpg', 430,
                    crop=(0.05, 0.03, 0.95, 0.72)), 0, 0.93 * H - 470 * 0.69 / 0.9 * 1.0 - 80, bleed='right')
c3 = cv.save('P03')
els = [h, b3, t1,
       body('主人亲自出题也一样：他不知道卡上是8，马敲了14下；他知道，马就敲8下。', 0.035, tb[1] + tb[3] + 0.01, 0.62, 58),
       label('调查负责人斯图姆夫', st[0] + 0.03, st[1] + st[3] - 0.075)]
pages.append(page(c3, els))

# ---------------------------------------------------------------- P4 第二招：大眼罩（F32 F33）
cv = S.Canvas()
h = headline('第二招：\n[[给马戴上大眼罩]]', 0.035, 0.022, 118)
b4 = big('35 次\n只对 2 次', 0.035, bottom(h) + 0.01, 160, w=0.55)
ph = cv.put(S.photo(C + 'Hans_mit_Scheuklappe_und_Weichselzopf.jpg', 560), 0, bottom(h) * H + 10, bleed='right')
t1 = body('看得见提问者时，汉斯对89%；确定看不见时，35次只对2次。', 0.035, bottom(b4) + 0.01, 0.52, 56)
e1 = cv.put(S.scan_strip(PF['blind'], [0.09, 0.402, 0.95, 0.459], FULL, unders=['only two', '89%'], pad=70),
            0, max(ph[1] + ph[3], bottom(t1)) * H - 10, bleed='full')
t2 = body('它一直拼命扭头，想看到提问的人。', 0.035, e1[1] + e1[3] + 0.005, 0.93, 60)
e2 = cv.put(S.scan_strip(PF['blind'], [0.09, 0.103, 0.91, 0.131], 1250, unders=['get a view of']), 0, bottom(t2) * H, bleed='left')
c4 = cv.save('P04')
pages.append(page(c4, [h, b4, t1, t2, label('戴大眼罩的汉斯（后来拍的）', ph[0] + 0.04, ph[1] + ph[3] - 0.075),
                       sticker('它在找什么？', 0.035, e2[1] + e2[3] + 0.005, 64)]))

# ---------------------------------------------------------------- P5 破案：头轻轻一抬（F35 F40 F41）
cv = S.Canvas()
h = headline('破案：\n[[答案在提问人的头上]]', 0.035, 0.022, 118)
ph = cv.put(S.photo(C + 'Hans_lernt_offen_2.jpg', 820), 0, bottom(h) * H + 10, bleed='right')
b5 = big('很少\n达到\n1 毫米', 0.035, bottom(h) + 0.03, 120, w=0.40)
y = ph[1] + ph[3] + 0.005
f1 = flow('① 出完题，人微微前倾\n　→ 马[[开始敲]]', y, 74)
f2 = flow('② 敲到答案，人头轻轻一抬\n　→ 马[[就停]]', bottom(f1) + 0.005, 74)
m1 = cv.put(S.scan_strip(PF['mm'], [0.08, 0.613, 0.89, 0.668], FULL, unders=['one millimeter'], pad=70), 0, bottom(f2) * H + 10, bleed='full')
c5 = cv.save('P05')
els = [h, b5, f1, f2, label('出题的人和汉斯', ph[0] + 0.04, ph[1] + ph[3] - 0.075),
       body('丰斯特在实验室自己扮马，测了25个人：除了2个，人人都有这个抬头，幅度很少达到1毫米。', 0.035, m1[1] + m1[3] + 0.005, 0.93, 54)]
pages.append(page(c5, els))

# ---------------------------------------------------------------- P6 不是骗局（F11 F37 F50）
cv = S.Canvas()
h = headline('不是骗局，\n[[是会自己抬的头]]', 0.035, 0.022, 118)
por = cv.put(S.photo(C + 'Krall_Wilhelm_von_Osten.jpg', 540), 0, bottom(h) * H + 10, bleed='right')
b6 = big('每月\n3万–6万马克', 0.035, bottom(h) + 0.02, 110, w=0.60)
t1 = body('据丰斯特说，一家杂耍剧团开出这个价请汉斯演出，冯·奥斯腾和别的邀约一起全推掉了。他也从不收门票。', 0.035, bottom(b6) + 0.01, 0.58, 52)
sd0 = cv.put(S.scan_strip(PF['self0'], [0.10, 0.910, 0.92, 0.946], FULL, unders=['not'], pad=70), 0, max(por[1] + por[3], bottom(t1)) * H - 10, bleed='full')
sd = cv.put(S.scan_strip(PF['self'], [0.10, 0.083, 0.92, 0.137], FULL, unders=['pure self-', 'deception'], pad=70), 0, (sd0[1] + sd0[3]) * H - 88, bleed='full')
c6 = cv.save('P06')
els = [h, b6, t1, label('冯·奥斯腾', por[0] + 0.04, por[1] + por[3] - 0.075),
       body('丰斯特的判断：冯·奥斯腾不是想骗大家，是纯粹的自我欺骗。破案的丰斯特自己也躲不开：他已经能随意指挥这匹马，可一专心想那个数，头还是会自己抬。', 0.035, sd[1] + sd[3] + 0.005, 0.93, 52)]
pages.append(page(c6, els))

# ---------------------------------------------------------------- P7 定义（F30 F47 F86 F89）
cv = S.Canvas()
h = headline('这就叫：\n[[聪明汉斯效应]]', 0.035, 0.022, 130)
p40 = S.ocr(PF['p40'], 'calculations.')[0]['box']
nr = cv.put(S.scan_strip(PF['p40'], [0.095, 0.722, p40[2] + 0.012, 0.757], FULL, unders=['neither read, count'], pad=70), 0, bottom(h) * H + 10, bleed='full')
c7 = cv.save('P07')
y = nr[1] + nr[3] + 0.01
e1 = big('答对了', 0.035, y, 200)
e2 = big('↓ 靠的却是', 0.035, bottom(e1) - 0.01, 90, fill=CREAM)
e3 = big('提问人的小动作', 0.035, bottom(e2), 150)
t2 = body('放到 AI 身上：答对了，理由却不对。靠的是碰巧和答案一起出现的线索，线索一拿走就露馅。', 0.035, 0.80, 0.93, 58, bg='#080808')
pages.append(page(c7, [h, e1, e2, e3, t2, label('汉斯用鼻子点数字，约1907年', 0.60, 0.755)],
                  backdrop=backdrop('assets/derived/Hans_zeigt_Zahlen_an_灰度去网.jpg', 0.5, focus=(0.62, 0.7))))

# ---------------------------------------------------------------- P8 AI：跑车贴上标签变成马（F66 F67 F68）
cv = S.Canvas()
h = headline('一百多年后，\n[[AI 也学会了看暗号]]', 0.035, 0.022, 118)
t1 = body('2019年一篇论文：有个认马的模型，碰到带来源标签的马图，盯的就是角落里那个标签。', 0.035, bottom(h) + 0.015, 0.93, 58)
LAP = 'assets/papers/lapuschkin2019_fig2.png'
horse = cv.put(S.card(S.load(LAP, crop=(0.012, 0.012, 0.445, 0.236)), 940), 0, bottom(t1) * H, bleed='right')
car = cv.put(S.card(S.load(LAP, crop=(0.445, 0.012, 0.975, 0.236)), 1340), 0, (horse[1] + horse[3]) * H - 40, bleed='full')
t2 = body('给跑车图贴上同一个标签，它就判成马；拿掉标签，就不判了。论文管这叫：', 0.035, car[1] + car[3] - 0.005, 0.93, 58)
stp = cv.put(S.strip('research/pdf/lapuschkin2019.pdf', 3, [0.07, 0.285, 0.48, 0.306], FULL, circles=['Clever Hans'], pad=70, vpad=22), 0, bottom(t2) * H - 10, bleed='full')
c8 = cv.save('P08')
pages.append(page(c8, [h, t1, t2, sticker('它认的是马吗？', 0.035, horse[1] + 0.07, 66)]))

# ---------------------------------------------------------------- P9 AI：换个考场（F70–F73）
cv = S.Canvas()
h = headline('换个考场，\n[[高分缩了水]]', 0.035, 0.022, 124)
t1 = body('胸片 AI 认得出片子来自哪家医院：NIH 的片子，99.95% 认得出。可各家医院的肺炎比例差了几十倍。', 0.035, bottom(h) + 0.015, 0.93, 56)
zs = cv.put(S.strip('research/pdf/zech2018.pdf', 1, [0.3268, 0.2365, 0.895, 0.2690], FULL, unders=['99.95% NIH'], whiteout=['10×', 'P = 0.027).', 'The primary limi-'], pad=70, vpad=22), 0, bottom(t1) * H, bleed='full')
zf = cv.put(S.photo('assets/papers/zech2018_fig2_large.png', 860, crop=(0.345, 0.035, 1, 1)), 0, (zs[1] + zs[3]) * H - 20, bleed='right')
b9 = big('0.931 → 0.815', 0.035, zf[1] + zf[3] + 0.005, 120, w=0.93)
t2 = body('NIH＋西奈山合训的肺炎模型，混着考 0.931，里面有靠认医院拿的分；换到第三家医院，只剩 0.815（AUC，满分1）。', 0.035, bottom(b9) + 0.005, 0.93, 52)
t3 = body('论文里 5 组换医院对比，3 组明显变差。', 0.035, bottom(t2) + 0.01, 0.93, 48)
c9 = cv.save('P09')
pages.append(page(c9, [h, t1, label('认医院的 AI 在看哪', zf[0] + 0.03, zf[1] + 0.02),
                       sticker('它在认哪家医院？', 0.035, zf[1] + 0.04, 56),
                       body('亮的地方之一：片角技师放的金属标记。不靠它，也认得出。', 0.035, zf[1] + 0.11, 0.36, 50), b9, t2, t3]))

# ---------------------------------------------------------------- P10 收尾：三条思考（F55 F69 F75 F89）
cv = S.Canvas()
c10 = cv.save('P10')
h = headline('分数漂亮，\n[[不等于真学会了]]~', 0.035, 0.022, 124)
els = [h]
for n, (q, y0) in enumerate([('把出题的人拿走：盲测、换医院、换数据', 0.25),
                             ('有的 AI 学到真本事，有的在看暗号；光看分数分不出，要看它到底在看哪', 0.42),
                             ('越像人，越要问：线索从哪来', 0.62)]):
    els.append(big(f'0{n + 1}', 0.035, y0, 170, w=0.2))
    els.append(body(q, 0.22, y0 + 0.025, 0.74, 66, bg='#080808'))
els.append(body('ELIZA 效应是人高估了机器；聪明汉斯效应，是机器抄近路拿了高分。', 0.035, 0.80, 0.93, 58, bg='#080808'))
pages.append(page(c10, els, backdrop=backdrop('assets/derived/Hans_1910_灰度去网.jpg', 0.6, focus=(0.75, 0.5))))

print('pages', S.write_script('聪明的汉斯与 AI 的聪明汉斯效应', '制作.py'))
