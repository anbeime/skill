"""AI 科技线第 5 篇：律师问 ChatGPT「这是真案子吗」→ 什么是 AI 幻觉。照 ELIZA / Dots 的标准手排（cy-carousel/scripts/手排.py）。
素材全部来自 Mata v. Avianca 案公开卷宗、NIST AI 600-1（公有领域）、Charlotin 数据库（CC BY 4.0）、美国法院系统发布的法官照片（公有领域）。
事实出处见 research/事实表.md（括号里是条目号）。渲染：
    python3 ../../../skills/cy-carousel/scripts/render.py 页面脚本.json --out pages --assets-root ."""
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'skills/cy-carousel/scripts'))
import 手排 as S
from 手排 import W, H, CREAM, headline, big, body, sticker, label, bottom, page, backdrop
from PIL import ImageOps

S.init(HERE, protect=['ChatGPT', 'Westlaw', 'LexisNexis', 'Avianca', 'NIST', 'Varghese', 'Charlotin', 'AI'])
A = 'assets/'
PDF = 'research/pdf/'
FULL = 1490
pages = S.pages
COURT = A + 'bg_Daniel_Patrick_Moynihan_United_States_Co.jpg'   # 纽约南区联邦法院（Moynihan 法院大楼），CC BY 4.0
CABIN = A + 'bg_Dentro_de_una_avion_airbus_a_320_de_avia.jpg'    # Avianca A320 客舱，CC BY-SA 3.0
BOOKS = A + 'bg_Canadian_law_books_on_shelf.jpg'                 # 法律书架，CC0
GAVEL = A + 'bg_gavel.jpg'                                        # 法槌，CC BY 2.0
HALL = A + 'bg_courtroom.jpg'                                     # 美国联邦上诉法院的法庭，公有领域
JUDGE_CROP = (0.0, 0.08, 0.5, 1.0)          # 视频截图左半边是法官


def chat(name, crop, w, **kw):
    """ChatGPT 截图卡（律师宣誓书附件，已转正）。"""
    return S.scan_strip(A + name, crop, w, pad=26, vpad=26, **kw)


# ---------------------------------------------------------------- 封面（F06）
cv = S.Canvas()
ct = ImageOps.fit(S.load(COURT), (W, H), centering=(0.45, 0.35))
ct = Image.eval(ct, lambda v: int(v * 0.42)).convert('RGBA')
cv.put(ct, 0, 0, clamp=False)
qa = cv.put(chat('chat_p4.png', [0.035, 0.09, 1.0, 0.57], FULL, circles=['is a real case']), 0, 70, bleed='full')
jd = cv.put(S.photo(A + 'Judge_Kevin_Castel.jpg', 640, crop=JUDGE_CROP), 0, (qa[1] + qa[3]) * H - 30, bleed='right')
c0 = cv.save('P00')
cover = page(c0, [label('律师和 ChatGPT 的对话', 0.05, qa[1] + qa[3] - 0.035),
                  label('审这个案子的法官', jd[0] + 0.04, jd[1] + jd[3] - 0.07),
                  {**headline('律师问 AI：', 0.055, 0.74, 112), 'font': 'cover-title'},
                  {**headline('[[这案子是真的吗？]]', 0.055, 0.83, 140), 'font': 'cover-title'}], layout='cover')
pages.append(cover)

# ---------------------------------------------------------------- P1 6 个不存在的案子（F01 F02 F03）
cv = S.Canvas()
h = headline('一份交给法院的文书，\n[[引了 6 个不存在的案子]]', 0.035, 0.022, 108)
b1 = big('6 个', 0.035, bottom(h) + 0.01, 220, w=0.5)
t1 = body('乘客马塔告 Avianca 航空：飞纽约的航班上，金属餐车撞伤了他的左膝。', 0.40, bottom(h) + 0.03, 0.56, 56)
lst = cv.put(S.scan_strip(A + 'affidavit_p2.png', [0.11, 0.093, 0.88, 0.243], FULL, unders=['Varghese v. China Southern'], pad=60), 0,
             max(bottom(b1), bottom(t1)) * H + 10, bleed='full')
c1 = cv.save('P01')
t2 = body('航空公司说早过了诉讼时效。2023年3月，原告律师交上反驳意见，引的判例里，这 6 个根本不存在。', 0.035, lst[1] + lst[3] + 0.005, 0.93, 58)
pages.append(page(c1, [h, b1, t1, t2, sticker('判例也能编？', 0.035, bottom(t2) + 0.03, 72), label('Avianca 的客舱', 0.70, 0.93)],
                  backdrop=backdrop(CABIN, 0.62, focus=(0.5, 0.6))))

# ---------------------------------------------------------------- P2 法官：前所未有（F04）
cv = S.Canvas()
h = headline('法官写下：\n[[前所未有]]', 0.035, 0.022, 124)
jd = cv.put(S.photo(A + 'Judge_Kevin_Castel.jpg', 760, crop=JUDGE_CROP), 0, bottom(h) * H + 10, bleed='right')
s1 = cv.put(S.strip(PDF + 'doc31.pdf', 0, [0.118, 0.383, 0.88, 0.444], FULL, unders=['unprecedented circumstance', 'non-existent'], pad=70, vpad=24),
            0, (jd[1] + jd[3]) * H, bleed='full')
c2 = cv.save('P02')
t1 = body('2023年5月，纽约南区联邦法院。', 0.035, bottom(h) + 0.04, 0.40, 58)
t2 = body('卡斯特尔法官在命令开头写：本庭面对的是前所未有的情况，这份文书里满是不存在的案子。', 0.035, s1[1] + s1[3] + 0.005, 0.93, 58)
pages.append(page(c2, [h, t1, t2, big('谁编的？', 0.035, bottom(t1) + 0.03, 120, w=0.42),
                       label('P. Kevin Castel 法官', jd[0] + 0.04, jd[1] + jd[3] - 0.07)],
                  backdrop=backdrop(COURT, 0.62, focus=(0.4, 0.3))))

# ---------------------------------------------------------------- P3 它说：复查过了，确实存在（F05 F06）
cv = S.Canvas()
h = headline('律师问它，\n[[它说：复查过了，是真的]]', 0.035, 0.022, 112)
p5 = cv.put(chat('chat_p5.png', [0.035, 0.11, 1.0, 0.80], 980, circles=['double-checking']), 0, bottom(h) * H + 10, bleed='right')
p6 = cv.put(chat('chat_p6.png', [0.035, 0.27, 1.0, 0.81], 980, unders=['are real']), 0, (p5[1] + p5[3]) * H - 20, bleed='left')
c3 = cv.save('P03')
t1 = body('追问出处时，它先为「之前的混淆」道歉，又说复查过，能在 Westlaw、LexisNexis 查到；问其他几个是不是假的，它说：都是真的。', 0.035, p6[1] + p6[3] + 0.005, 0.93, 54)
pages.append(page(c3, [h, t1, sticker('它怎么这么肯定？', 0.035, bottom(t1) + 0.02, 66)]))

# ---------------------------------------------------------------- P4 超级搜索引擎（F07 F08）
cv = S.Canvas()
h = headline('他以为它是\n[[超级搜索引擎]]', 0.035, 0.022, 124)
x0 = S.find(PDF + 'doc54.pdf', 14, 'I falsely')[0]
e1 = cv.put(S.strip(PDF + 'doc54.pdf', 14, [x0 - 0.004, 0.851, 0.866, 0.880], FULL, unders=['super search engine'], pad=70, vpad=22), 0, bottom(h) * H + 230, bleed='full')
x1 = S.find(PDF + 'doc54.pdf', 5, 'I just never')[0]
e2a = cv.put(S.strip(PDF + 'doc54.pdf', 5, [x1 - 0.004, 0.399, 0.857, 0.426], 760, unders=['never thought'], pad=30, vpad=18), 0, (e1[1] + e1[3]) * H + 190, bleed='left')
x2 = S.find(PDF + 'doc54.pdf', 5, 'be made up')[2]
e2 = cv.put(S.strip(PDF + 'doc54.pdf', 5, [0.116, 0.433, x2 + 0.012, 0.461], 760, unders=['made up'], pad=30, vpad=18), 330, (e2a[1] + e2a[3]) * H - 30)
c4 = cv.save('P04')
els = [h, body('律师施瓦茨执业约 30 年，之前从没用过 ChatGPT，是从新闻和家人那儿听说的。', 0.035, bottom(h) + 0.02, 0.93, 58),
       body('他在庭上说：我误以为它像一个超级搜索引擎。', 0.035, e1[1] + e1[3] + 0.005, 0.93, 58),
       big('我从没想过\n那个案子会是编的', 0.035, e2[1] + e2[3] + 0.005, 120, w=0.93),
       body('法官没有全信他的解释，认定他们有主观恶意。', 0.035, e2[1] + e2[3] + 0.17, 0.93, 52)]
pages.append(page(c4, els))

# ---------------------------------------------------------------- P5 连判决书都是编的（F10）
cv = S.Canvas()
h = headline('连判决书\n[[都是编出来的]]', 0.035, 0.022, 124)
fk = cv.put(S.photo(A + 'fake_varghese_p36.png', 820, crop=(0.0, 0.08, 1.0, 0.86)), 0, bottom(h) * H + 10, bleed='right')
g = cv.put(S.strip(PDF + 'doc54.pdf', 10, [0.118, 0.19, 0.86, 0.252], FULL, circles=['gibberish'], pad=70, vpad=22), 0, (fk[1] + fk[3]) * H - 30, bleed='full')
c5 = cv.save('P05')
els = [h, body('它还编出了像模像样的「判决」：有三位法官的名字、有案情、有引文。', 0.035, bottom(h) + 0.03, 0.40, 56),
       body('可读下去，原告一会儿是替死者家属打官司的人，一会儿又成了被超售拒载的乘客。', 0.035, bottom(h) + 0.22, 0.40, 56),
       label('假「判决」（判决书附录）', fk[0] + 0.04, fk[1] + fk[3] - 0.07),
       body('法官的评语：它的法律分析是一派胡言。', 0.035, g[1] + g[3] + 0.005, 0.93, 60)]
pages.append(page(c5, els, backdrop=backdrop(BOOKS, 0.66, focus=(0.4, 0.5))))

# ---------------------------------------------------------------- P6 罚款＋写信；错不在用 AI（F11 F12）
cv = S.Canvas()
h = headline('罚 5000 美元，\n[[还要给法官写信]]', 0.035, 0.022, 116)
t0 = body('2023年6月22日判决：两位律师和律所共同罚款 5000 美元，还要给每一位被冒名「写了」假判决的法官寄信。', 0.035, bottom(h) + 0.02, 0.93, 56)
l1 = cv.put(S.strip(PDF + 'doc54.pdf', 33, [0.118, 0.364, 0.84, 0.391], FULL, unders=['each judge falsely identified'], pad=70, vpad=22), 0, bottom(t0) * H, bleed='full')
l2 = cv.put(S.strip(PDF + 'doc54.pdf', 0, [0.118, 0.507, 0.872, 0.533], FULL, unders=['nothing inherently improper'], pad=70, vpad=22), 0, (l1[1] + l1[3]) * H + 150, bleed='full')
c6 = cv.save('P06')
els = [h, t0,
       body('可法官也写明：用可靠的 AI 工具帮忙，本身没有不妥。', 0.035, l1[1] + l1[3] + 0.005, 0.93, 58),
       big('错在没核对，\n被质疑了还坚持', 0.035, l2[1] + l2[3] + 0.01, 120, w=0.93)]
pages.append(page(c6, els, backdrop=backdrop(GAVEL, 0.68, focus=(0.55, 0.55))))

# ---------------------------------------------------------------- P7 定义（F13）
cv = S.Canvas()
h = headline('这就叫：\n[[AI 幻觉]]', 0.035, 0.022, 140)
nd0 = cv.put(S.strip(PDF + 'nist_ai_600-1.pdf', 7, [0.288, 0.149, 0.786, 0.172], 1300, unders=['erroneous or false content'], pad=40, vpad=18), 0, bottom(h) * H + 10, bleed='right')
nd = cv.put(S.strip(PDF + 'nist_ai_600-1.pdf', 7, [0.174, 0.168, 0.53, 0.191], 1000, unders=['hallucinations'], pad=40, vpad=18), 0, (nd0[1] + nd0[3]) * H - 40, bleed='left')
c7 = cv.save('P07')
y = nd[1] + nd[3] + 0.01
e1 = big('说得很肯定', 0.035, y, 190)
e2 = big('↓ 内容却是', 0.035, bottom(e1) - 0.01, 90, fill=CREAM)
e3 = big('编出来的', 0.035, bottom(e2), 190)
t1 = body('美国国家标准与技术研究院（NIST）的定义：生成式 AI 自信地给出错误或虚假的内容，俗称「幻觉」，可能误导用户。', 0.035, bottom(e3) + 0.02, 0.93, 56)
pages.append(page(c7, [h, e1, e2, e3, t1]))

# ---------------------------------------------------------------- P8 为什么那么肯定（F14）
cv = S.Canvas()
h = headline('它为什么\n[[说得那么肯定？]]', 0.035, 0.022, 124)
nw = cv.put(S.strip(PDF + 'nist_ai_600-1.pdf', 9, [0.369, 0.234, 0.818, 0.257], 1300, unders=['predict the next token or word'], pad=40, vpad=18), 0, bottom(h) * H + 10, bleed='right')
c8 = cv.save('P08')
y = nw[1] + nw[3] + 0.01
t1 = body('NIST 说，这是生成式模型的工作方式自带的：按训练数据的统计规律，一个词一个词往下猜。', 0.035, y, 0.93, 56)
f1 = big('你问：有没有类似判例？', 0.035, bottom(t1) + 0.02, 74, fill=CREAM)
f2 = big('↓ 它猜：「Varghese v.」', 0.035, bottom(f1), 74, fill=CREAM)
f3 = big('↓ 再猜：「China Southern…」', 0.035, bottom(f2), 74, fill=CREAM)
f4 = big('↓ 一段[[很像判例]]的话', 0.035, bottom(f3), 74, fill=CREAM)
t2 = body('猜得通顺，不等于猜得对。它语气越肯定，人越容易信。', 0.035, bottom(f4) + 0.02, 0.93, 60)
pages.append(page(c8, [h, t1, f1, f2, f3, f4, t2, label('示意', 0.80, bottom(t1) + 0.03)]))

# ---------------------------------------------------------------- P9 2149 起（F15）
cv = S.Canvas()
h = headline('三年后，\n[[同样的事还在发生]]', 0.035, 0.022, 116)
b9 = big('2149 起', 0.035, bottom(h) + 0.005, 220)
db = cv.put(S.photo(A + 'charlotin_db.png', 1240, crop=(0.03, 0.095, 0.69, 0.33)), 0, bottom(b9) * H, bleed='full')
c9 = cv.save('P09')
t1 = body('学者 Damien Charlotin 的公开数据库，截至2026年10月5日更新，已收录 2149 起：法院裁决里认定或指出，有人在文书里用了 AI 编出的内容。', 0.035, db[1] + db[3] + 0.005, 0.93, 56)
t2 = body('写文书的有律师，也有自己打官司的普通人。', 0.035, bottom(t1) + 0.02, 0.93, 58)
pages.append(page(c9, [h, b9, t1, t2, sticker('你也这样信过它吗？', 0.035, bottom(t2) + 0.03, 66)],
                  backdrop=backdrop(HALL, 0.62, focus=(0.5, 0.5))))

# ---------------------------------------------------------------- P10 收尾
cv = S.Canvas()
c10 = cv.save('P10')
h = headline('AI 敢说，\n[[你得敢查]]~', 0.035, 0.022, 140)
els = [h]
for n, (q, y0) in enumerate([('它说得越肯定，越要去查原文', 0.25),
                             ('让它给出处，再自己点开出处', 0.42),
                             ('错的不是用 AI，是不核对就交出去', 0.59)]):
    els.append(big(f'0{n + 1}', 0.035, y0, 170, w=0.2))
    els.append(body(q, 0.22, y0 + 0.03, 0.74, 70))
els.append(body('问 AI「这是真的吗」，不算核对；自己点开原文，才算。', 0.035, 0.80, 0.93, 60))
pages.append(page(c10, els, backdrop=backdrop(BOOKS, 0.6, focus=(0.7, 0.4))))

print('pages', S.write_script('律师问 ChatGPT「这是真案子吗」：什么是 AI 幻觉', '制作.py'))
