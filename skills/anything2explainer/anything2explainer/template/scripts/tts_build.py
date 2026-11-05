#!/usr/bin/env python3
"""配音 + 时间轴生成。项目根 = 本脚本所在 scripts/ 的上级目录。
输入 narration.txt：
  # CHAPTER <n> <标题>      章节标记（章节前自动加 chapter_gap 帧空白）
  空行                     段落分隔：空行前那句是**段末**（= 一个镜头讲完 / 切下一页），下一句前额外加 PARA_GAP 帧。
                           段内小句之间只有 GAP 帧（一口气），停顿只出现在段末——每句都停会让整片显得拖。
  ## gap <帧数>             在下一句前再额外插入空白帧（段末句的末块 <45 帧时加 15–30，给末拍元素落位停留；本脚本跑完会列出这些句）
  一句话|按竖线分成字幕短句            → 竖线只切字幕，不影响朗读
                                       每块预算：中文 ≤16 字 / 英文 ≤48 字符（超了会打 ⚠ 并自动缩字号）
                                       块首尾空格会去掉；英文片把块用空格拼回整句给 TTS（"a|b" 与 "a | b" 等价），中文直接拼接
输出：
  public/assets/<slug>/audio.wav（48k 立体声 16bit；slug 读 src/config.ts）
  script/timeline.json / timeline.md
  src/common/subs.ts（字幕表）、src/common/timeline.ts（TOTAL_FRAMES / CHAPTER_STARTS / SENTENCES）
逐句（或逐字幕块）缓存于 audio/cache/，改一句只重合成一句；缓存键含引擎参数与本地模型文件的指纹（路径 + 大小 + mtime + 内容头），换模型自动失效。

TTS 引擎（`TTS_ENGINE`，默认 `auto` = 按解说词语言选；**跑之前先问用户有没有偏好的 TTS**，见 SKILL.md 确认点 3）：
  edge     中文默认。edge-tts 云端合成，有词级边界 → 字幕节拍最准。VOICE=zh-CN-YunxiNeural RATE=+0%（原速，默认不加速）
           词边界要显式请求（boundary='WordBoundary'，7.2.0 起的默认值不给），否则字幕起点会静默退化成插值。
  kokoro   英文默认。kokoro-82m 本地推理（`pip install kokoro soundfile` + espeak-ng：macOS `brew install espeak-ng` / Linux `apt install espeak-ng`）。
           KOKORO_VOICE=am_liam（Liam，男声，与中文云希同定位）KOKORO_LANG=a KOKORO_SPEED=1.0
  kokoro 没有词边界 → 改为「逐字幕块分别合成再拼接」，块起始帧因此也是精确的（CHUNK_PAD 调块间静音）。
  piper       Linux/ARM（含树莓派）本地配音。onnxruntime 版 VITS，无 torch/spacy。`pip install piper-tts` +
              一个 .onnx 语音，路径经 PIPER_MODEL 传入；无词边界，同 kokoro 逐块合成。装得最快，音色一般。
  kokoro_onnx Linux/ARM 本地配音，音色自然。onnxruntime 版 kokoro，无 torch/spacy（比 `kokoro` 引擎好装）。
              `pip install kokoro-onnx` + 模型 KOKORO_ONNX_MODEL / 声音库 KOKORO_ONNX_VOICES；KOKORO_ONNX_VOICE 默认 am_michael。
  读音覆写表 PRONOUNCE（见下）只作用于 `kokoro` 引擎（misaki 的 [词](/音标/) 语法）；piper / kokoro_onnx 不认这个语法，
  缩写读错时改写解说词或换引擎。
  用户有别的 TTS 偏好时不走本脚本：让他给成品配音 wav，按逐句/逐块时间轴手填 timeline.ts 与 subs.ts。
其它环境变量：GAP/CHAPTER_GAP/LEAD/TAIL（帧）、EDGE_TRIES（edge 每句最多试几次，端点会间歇性返回空音频）。
"""
import asyncio, hashlib, json, os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REM = ROOT
_cfg = open(f'{ROOT}/src/config.ts', encoding='utf-8').read()
SLUG = re.search(r"slug:\s*'([^']+)'", _cfg).group(1)
_m = re.search(r"lang:\s*'(zh|en)'", _cfg)
CFG_LANG = _m.group(1) if _m else 'zh'
FPS = 30
SR = 48000
ENGINE = os.environ.get('TTS_ENGINE', 'auto')
VOICE = os.environ.get('VOICE', 'zh-CN-YunxiNeural')
RATE = os.environ.get('RATE', '+0%')          # 原速：默认不给语音加速（用户裁定）。+8% 会把中文语速从 ≈5.5 抬到 ≈6 字/秒，听着赶
KOKORO_VOICE = os.environ.get('KOKORO_VOICE', 'am_liam')
KOKORO_LANG = os.environ.get('KOKORO_LANG', 'a')       # a=American English, b=British
KOKORO_SPEED = float(os.environ.get('KOKORO_SPEED', 1.0))
KOKORO_SR = 24000
# piper（TTS_ENGINE=piper）：本地/ARM 友好，模型路径经环境变量传入（无默认，缺省即报错提示）
PIPER_MODEL = os.environ.get('PIPER_MODEL', '')
PIPER_VOICE_NAME = os.path.basename(PIPER_MODEL).replace('.onnx', '') if PIPER_MODEL else 'piper'
# kokoro_onnx（TTS_ENGINE=kokoro_onnx）：onnxruntime 版 kokoro，无 torch/spacy
KOKORO_ONNX_MODEL = os.environ.get('KOKORO_ONNX_MODEL', '')     # 例：kokoro-v1.0.onnx
KOKORO_ONNX_VOICES = os.environ.get('KOKORO_ONNX_VOICES', '')  # 例：voices-v1.0.bin
KOKORO_ONNX_VOICE = os.environ.get('KOKORO_ONNX_VOICE', 'am_michael')
KOKORO_ONNX_LANG = os.environ.get('KOKORO_ONNX_LANG', 'en-us')
CHUNK_PAD = float(os.environ.get('CHUNK_PAD', 0.06))  # 无词边界引擎：块间静音秒


def _file_fp(path):
    """模型文件指纹（进缓存键）：真实路径 + 大小 + mtime + 前 1MB 内容的 sha1 前 12 位。
    换目录下的同名模型、原地替换模型文件都会让旧缓存失效；只按文件名区分会把不同声音的缓存混在一起。
    路径为空返回 'none'；路径设了但文件不存在返回 'missing:<路径>'（合成时另有报错）。"""
    if not path:
        return 'none'
    rp = os.path.realpath(path)
    try:
        st = os.stat(rp)
        with open(rp, 'rb') as f:
            head = f.read(1 << 20)
    except OSError:
        return f'missing:{rp}'
    return hashlib.sha1(f'{rp}|{st.st_size}|{st.st_mtime_ns}|'.encode() + head).hexdigest()[:12]


PIPER_FP = _file_fp(PIPER_MODEL)
KOKORO_ONNX_FP = f'{_file_fp(KOKORO_ONNX_MODEL)}+{_file_fp(KOKORO_ONNX_VOICES)}'
EDGE_TRIES = int(os.environ.get('EDGE_TRIES', 4))     # edge-tts 每句最多试几次（端点会间歇性返回空音频）
GAP = int(os.environ.get('GAP', 10))          # 段内句间空白帧：只留一口气，不做停顿（用户反馈：小句之间加停顿会显得拖）
PARA_GAP = int(os.environ.get('PARA_GAP', 20)) # 段末额外空白（narration.txt 用空行分段）：一段话讲完 / 切下一页才停，合计 GAP+PARA_GAP = 30 帧 ≈ 1 s
                                              # —— 这是「末拍元素落位后停 1–1.5 s 再切」的时间来源（composition-and-light.md §7）
CHAPTER_GAP = int(os.environ.get('CHAPTER_GAP', 45))  # 章节前空白帧
LEAD = int(os.environ.get('LEAD', 40))        # 片头静音帧
TAIL = int(os.environ.get('TAIL', 90))        # 片尾静音帧
SHORT_TAIL = 45                               # 段末句的末块短于此帧数就要补停留（22 帧入场 + 8 帧离场后停不满 30 帧）；段内句不判
CACHE = f'{ROOT}/audio/cache'
os.makedirs(CACHE, exist_ok=True)
if ENGINE not in ('auto', 'edge', 'kokoro', 'piper', 'kokoro_onnx'):
    raise SystemExit(f'未知 TTS_ENGINE={ENGINE}（可选 auto / edge / kokoro / piper / kokoro_onnx）')


def parse(path):
    items = []
    chap = 0
    chap_title = ''
    pending_gap = 0
    para_break = False

    def last_sent():
        for it in reversed(items):
            if it['type'] == 'sent':
                return it
        return None
    for raw in open(path, encoding='utf-8'):
        line = raw.strip()
        if not line:   # 空行 = 段落分隔：空行前那句是段末（镜头末，该停一下），下一句前额外 PARA_GAP 帧
            s = last_sent()
            if s is not None:
                s['para_end'] = True
                para_break = True
            continue
        m = re.match(r'^#\s*CHAPTER\s+(\d+)\s+(.*)$', line)
        if m:
            chap = int(m.group(1)); chap_title = m.group(2).strip()
            s = last_sent()
            if s is not None:
                s['para_end'] = True     # 章末也是段末；章前已有 CHAPTER_GAP，不再叠 PARA_GAP
            items.append({'type': 'chapter', 'chapter': chap, 'title': chap_title})
            para_break = False
            continue
        m = re.match(r'^##\s*gap\s+(\d+)', line)
        if m:
            pending_gap += int(m.group(1)); continue
        if line.startswith('#'):
            continue
        items.append({'type': 'sent', 'chapter': chap, 'raw': line, 'gap_before': pending_gap + (PARA_GAP if para_break else 0), 'para_end': False})
        pending_gap = 0
        para_break = False
    s = last_sent()
    if s is not None:
        s['para_end'] = True             # 片末也是段末
    return items


def cache_path(text, ext):
    # 本地模型引擎用文件指纹而不是文件名：不同目录下的同名 model.onnx、原地换掉的模型都要各自缓存
    sig = f'{ENGINE}|{VOICE}|{RATE}|{KOKORO_VOICE}|{KOKORO_ONNX_VOICE}|{KOKORO_ONNX_LANG}|{KOKORO_ONNX_FP}|{PIPER_FP}|{KOKORO_LANG}|{KOKORO_SPEED}|{text}'
    return f'{CACHE}/{hashlib.sha1(sig.encode()).hexdigest()[:16]}{ext}'


def detect_lang(items):
    """解说词里 CJK 占比 ≥20% → 'zh'，否则 'en'。"""
    txt = ''.join(it['raw'] for it in items if it['type'] == 'sent')
    cjk = sum(1 for c in txt if '一' <= c <= '鿿')
    return 'zh' if cjk >= 0.2 * max(1, len(txt)) else 'en'


# 字幕块宽度预判：与 src/common/textfit.ts 用同一张 em 宽表（字体 fontTools 实测），
# 直接算「44px 下会不会超过安全区 1160px」——比按字数判准，中英混排（如「几百个 token 一块」）不会误报。
# 授稿建议仍是每块中文 ≤16 字 / 英文 ≤48 字符（见 narration-storyboard.md）。
SUB_MAX_W = 1160
SUB_SIZE = 44
SUB_BUDGET = {'zh': '16 字', 'en': '48 字符'}


def text_em(s):
    """与 src/common/textfit.ts 的 textEm() 同一张表（改一处要同步另一处）。"""
    t = 0.0
    for ch in s:
        c = ord(ch)
        if c >= 0x2000:
            t += 1.0                     # CJK / 全角，以及 U+2000 起的标点 / 箭头 / 数学符号（— … “ ” → ∑ 在 Noto 里都是 1em）
        elif ch == ' ':
            t += 0.227
        elif 'A' <= ch <= 'Z':
            t += 0.668
        elif '0' <= ch <= '9':
            t += 0.59
        elif 'a' <= ch <= 'z':
            t += 0.566
        elif 0xc0 <= c < 0x250:
            t += 0.58                    # 带重音的拉丁字母
        else:
            t += 0.325                   # 半角标点
    return t


def write_wav(path, x, sr):
    """x：float32 单声道 (n,) 或立体声 (n,2) → 16bit PCM wav。"""
    import wave
    a = np.asarray(x, dtype=np.float32)
    pcm = (np.clip(a, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1 if a.ndim == 1 else a.shape[1]); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())


async def synth_edge(text):
    """edge-tts：整句合成 + 词级边界（会把 text 发送到微软云端端点）。
    boundary='WordBoundary' 必须显式传：edge-tts 7.2.0 起该参数默认 'SentenceBoundary'，
    不传就一个 WordBoundary 事件都收不到，chunk_starts() 会静默退化成按字数插值（字幕能偏半秒）。
    端点会间歇性返回空音频（NoAudioReceived）：50 句的片子里随机一两句中招，同一句重试多半就过，
    所以试 EDGE_TRIES 次；试完还拿不到就报错退出，不把空 mp3 当成品往下传。"""
    import edge_tts
    mp3 = cache_path(text, '.mp3'); js = cache_path(text, '.json')
    if os.path.exists(mp3) and os.path.exists(js):
        return mp3, json.load(open(js))
    for attempt in range(1, EDGE_TRIES + 1):
        audio = bytearray(); words = []
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
            async for ch in comm.stream():
                if ch['type'] == 'audio':
                    audio += ch['data']
                elif ch['type'] == 'WordBoundary':
                    words.append({'t': ch['offset'] / 1e7, 'd': ch['duration'] / 1e7, 'text': ch['text']})
            if audio:
                break
            why = '端点返回空音频'
        except TypeError:                # boundary 参数是 edge-tts 7.2.0 才有的
            raise SystemExit("edge-tts 版本过旧：pip install 'edge-tts==7.2.8'")
        except Exception as e:
            why = f'{type(e).__name__}: {e}'
        if attempt == EDGE_TRIES:
            raise SystemExit(f'edge-tts 试了 {EDGE_TRIES} 次仍拿不到音频（{why}）：{text[:30]}…')
        print(f'  ⚠ edge-tts 第 {attempt} 次失败（{why}），{1.5 * attempt:.1f}s 后重试：{text[:16]}…')
        await asyncio.sleep(1.5 * attempt)
    open(mp3, 'wb').write(audio)
    json.dump(words, open(js, 'w'), ensure_ascii=False)
    return mp3, words


_kokoro = None

# kokoro 读音覆写（只影响送给 TTS 的文本，字幕仍显示原词）。语法是 kokoro/misaki 的 [词](/音标/)，
# **只对 `kokoro` 引擎生效**（piper / kokoro_onnx 走 espeak 音素化，不认这个语法，会把括号读出来）。
# 模板默认为空，按本片增补：kokoro 常把生僻缩写逐字母拼读、把 "v5.0" 读成 "v five zero"，合成前 dump 音素检查。
# 写法示例：'CUDA': '[CUDA](/kˈudə/)'，'v5.0': '[v5.0](/vˈi fˈIv pYnt ˈO/)'
PRONOUNCE = {}


def apply_pronounce(text):
    for k, v in PRONOUNCE.items():
        text = re.sub(r'(?<![A-Za-z0-9])' + re.escape(k) + r'(?![A-Za-z0-9])', v, text)
    return text


def synth_kokoro(text):
    """kokoro-82m：本地推理，24kHz，无词边界。"""
    global _kokoro
    text = apply_pronounce(text)
    au = cache_path(text, '.wav')
    if os.path.exists(au):
        return au
    if _kokoro is None:
        try:
            from kokoro import KPipeline
        except ImportError:
            raise SystemExit('TTS_ENGINE=kokoro 需要 kokoro：pip install kokoro soundfile；英文 G2P 另需 espeak-ng（macOS brew / Linux apt install espeak-ng）。'
                             'ARM / Python 3.13 上装不动 kokoro 就换 TTS_ENGINE=kokoro_onnx 或 piper（见文件头）')
        _kokoro = KPipeline(lang_code=KOKORO_LANG)
    parts = []
    for r in _kokoro(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED):
        a = getattr(r, 'audio', None)
        if a is None:
            a = r[2]                                    # 旧版 yield (graphemes, phonemes, audio)
        if hasattr(a, 'detach'):
            a = a.detach().cpu().numpy()                # torch tensor
        parts.append(np.asarray(a, dtype=np.float32).reshape(-1))
    if not parts:
        raise SystemExit(f'kokoro 没有产出音频：{text[:24]}…')
    write_wav(au, np.concatenate(parts), KOKORO_SR)
    return au


_piper = None


def synth_piper(text):
    """piper-tts：本地推理（onnxruntime，Linux/ARM/树莓派友好，无 torch/spacy），无词边界 → 逐块合成。
    模型原生采样率写 wav；decode() 再用 ffmpeg 重采样到 SR。需 PIPER_MODEL 指向一个 .onnx 语音。
    不套 PRONOUNCE 读音覆写（那是 kokoro/misaki 语法，piper 会把括号读出来）。"""
    global _piper
    if not PIPER_MODEL:
        raise SystemExit('TTS_ENGINE=piper 需要 PIPER_MODEL 指向一个 piper .onnx 语音'
                         '（pip install piper-tts；语音见 github.com/rhasspy/piper voices）')
    au = cache_path(text, '.wav')
    if os.path.exists(au):
        return au
    if _piper is None:
        try:
            from piper import PiperVoice
        except ImportError:
            raise SystemExit('TTS_ENGINE=piper 需要 piper：pip install piper-tts')
        _piper = PiperVoice.load(PIPER_MODEL)
    import wave
    with wave.open(au, 'wb') as w:
        _piper.synthesize_wav(text, w)
    return au


_kokoro_onnx = None


def synth_kokoro_onnx(text):
    """kokoro-onnx：onnxruntime 版 kokoro（Linux/ARM 友好，无 torch/spacy；比 `kokoro` 引擎好装、音色自然），
    24kHz，无词边界 → 逐块合成。需 KOKORO_ONNX_MODEL / KOKORO_ONNX_VOICES 两个模型文件。
    不套 PRONOUNCE 读音覆写（kokoro-onnx 用 espeak 音素化，不认 misaki 的 [词](/音标/) 语法）。"""
    global _kokoro_onnx
    if not (KOKORO_ONNX_MODEL and KOKORO_ONNX_VOICES):
        raise SystemExit('TTS_ENGINE=kokoro_onnx 需要 KOKORO_ONNX_MODEL 与 KOKORO_ONNX_VOICES'
                         '（pip install kokoro-onnx；模型见 github.com/thewh1teagle/kokoro-onnx releases）')
    au = cache_path(text, '.wav')
    if os.path.exists(au):
        return au
    if _kokoro_onnx is None:
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            raise SystemExit('TTS_ENGINE=kokoro_onnx 需要 kokoro-onnx：pip install kokoro-onnx')
        _kokoro_onnx = Kokoro(KOKORO_ONNX_MODEL, KOKORO_ONNX_VOICES)
    s, sr = _kokoro_onnx.create(text, voice=KOKORO_ONNX_VOICE, speed=KOKORO_SPEED, lang=KOKORO_ONNX_LANG)
    write_wav(au, np.asarray(s, dtype=np.float32).reshape(-1), sr)
    return au


def decode(mp3):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def trim_edges(x, thr=0.004):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] - int(0.03 * SR)); b = min(len(x), idx[-1] + int(0.12 * SR))
    return x[a:b], a / SR


def chunk_starts(tts_text, chunks, words, lead_cut, dur, sep=''):
    """按 | 切出的字幕短句 → 每块在句内的起始秒。word 边界按字符游标对到原句。
    tts_text == sep.join(chunks)：英文 sep=' '，游标要跳过块间的那个空格。"""
    # 每个字符的起始时间（按 word 边界填充）
    char_t = [None] * len(tts_text)
    cur = 0
    for w in words:
        wt = re.sub(r'[\s，。、！？：；“”（）,.!?:;()\-—…]', '', w['text'])
        if not wt:
            continue
        p = tts_text.find(wt, cur)
        if p < 0:
            p = tts_text.find(wt[0], cur)
            if p < 0:
                continue
        for i in range(p, min(len(tts_text), p + len(wt))):
            char_t[i] = (w['t'] - lead_cut, w['d'])
        cur = p + len(wt)
    # 每块首字时间
    starts = []
    pos = 0
    for c in chunks:
        seg = tts_text[pos:pos + len(c)]
        st = None
        for i in range(pos, pos + len(c)):
            if char_t[i] is not None:
                st = char_t[i][0]; break
        starts.append(st)
        pos += len(c) + len(sep)
    # 兜底：无边界的块按字数线性插值
    for i, st in enumerate(starts):
        if st is None:
            prev = starts[i - 1] if i > 0 and starts[i - 1] is not None else 0.0
            starts[i] = prev + dur * len(chunks[i - 1]) / max(1, len(tts_text)) if i > 0 else 0.0
    starts[0] = 0.0
    return [max(0.0, s) for s in starts]


async def synth_sentence(chunks, sep=''):
    """一句 → (音频 float32 单声道, 每个字幕块在句内的起始秒, 句长秒)。sep 是块之间的连接符（英文 ' '，中文 ''）。
    edge：整句合成一次，块起点按词边界对齐（最准）。
    kokoro：无词边界 → 逐字幕块分别合成再拼接，块起点因此是精确的，代价是块界断句略生硬。"""
    text = sep.join(chunks)
    if ENGINE == 'edge':
        au, words = await synth_edge(text)
        x, lead_cut = trim_edges(decode(au))
        dur = len(x) / SR
        return x, chunk_starts(text, chunks, words, lead_cut, dur, sep), dur
    chunk_synth = {'piper': synth_piper, 'kokoro_onnx': synth_kokoro_onnx}.get(ENGINE, synth_kokoro)
    pad = np.zeros(int(CHUNK_PAD * SR), dtype=np.float32)
    parts = []; starts = []; pos = 0.0
    for i, c in enumerate(chunks):
        xi, _ = trim_edges(decode(chunk_synth(c)))
        if i:
            parts.append(pad); pos += len(pad) / SR
        starts.append(pos)
        parts.append(xi); pos += len(xi) / SR
    x = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
    return x, starts, len(x) / SR


async def main(narr):
    global ENGINE
    items = parse(narr)
    lang = detect_lang(items)
    if ENGINE == 'auto':
        ENGINE = 'edge' if lang == 'zh' else 'kokoro'
        print(f'解说词语言 {lang} → TTS_ENGINE={ENGINE}（有偏好请显式传 TTS_ENGINE=…）')
    if lang != CFG_LANG:
        print(f"⚠ src/config.ts 的 lang: '{CFG_LANG}' 与解说词语言 {lang} 不一致——改过来，"
              f"否则标题压窄与居中基线会按错的语言算")
    # 字幕块拼回整句给 TTS 时的连接符：英文词与词之间要有空格（否则 "powerful|but" 会被念成 powerfulbut），中文直接拼
    sep = ' ' if lang == 'en' else ''
    t = LEAD / FPS
    audio_parts = []  # (start_sec, np.array)
    sentences = []; chapters = []
    sid = 0
    total_chars = 0; total_words = 0; speech_sec = 0.0
    for it in items:
        if it['type'] == 'chapter':
            t += CHAPTER_GAP / FPS
            chapters.append({'n': it['chapter'], 'title': it['title'], 'from': int(round(t * FPS)) + 1})
            continue
        t += it['gap_before'] / FPS
        raw = it['raw']
        chunks = [c.strip() for c in raw.split('|') if c.strip()]
        if not chunks:
            continue
        tts_text = sep.join(chunks)
        x, starts, dur = await synth_sentence(chunks, sep)
        sid += 1
        subs = [(t + starts[i], t + (starts[i + 1] if i + 1 < len(starts) else dur)) for i in range(len(chunks))]
        f0 = int(round(t * FPS)) + 1; f1 = int(round((t + dur) * FPS))
        sentences.append({'id': f'S{sid:02d}', 'chapter': it['chapter'], 'from': f0, 'to': f1, 'text': tts_text, 'para': bool(it.get('para_end')),
                          'subs': [{'from': int(round(a * FPS)) + 1, 'to': int(round(b * FPS)), 'text': c} for c, (a, b) in zip(chunks, subs)]})
        audio_parts.append((t, x))
        total_chars += len(re.sub(r'[，。、！？：；“”（）,.!?:;()\-—…\s]', '', tts_text))
        total_words += len(tts_text.split()); speech_sec += dur
        t += dur + GAP / FPS
    t += TAIL / FPS
    total = int(np.ceil(t * FPS))
    # 合成音轨
    y = np.zeros(int(total / FPS * SR) + SR, dtype=np.float32)
    for st, x in audio_parts:
        a = int(st * SR); y[a:a + len(x)] += x
    y = y[: int(total / FPS * SR)]
    peak = float(np.max(np.abs(y))) or 1.0
    y = y / peak * 0.89
    os.makedirs(f'{REM}/public/assets/{SLUG}', exist_ok=True)
    wav = f'{REM}/public/assets/{SLUG}/audio.wav'
    write_wav(wav, np.stack([y, y], 1), SR)
    # 修正字幕：相邻句字幕不重叠；同句块间连续
    all_subs = []
    for s in sentences:
        for k, sb in enumerate(s['subs']):
            if sb['to'] < sb['from']:
                sb['to'] = sb['from']
            all_subs.append(dict(sb))
    for i in range(len(all_subs) - 1):
        if all_subs[i]['to'] >= all_subs[i + 1]['from']:
            all_subs[i]['to'] = all_subs[i + 1]['from'] - 1
    # 字幕块宽度体检：超安全区的块会被 Subtitle.tsx 缩字号（>1.3 倍还会折两行压进内容区），正确做法是回去切文案
    over = [(sb, text_em(sb['text']) * SUB_SIZE) for sb in all_subs]
    over = [(sb, w) for sb, w in over if w > SUB_MAX_W]
    if over:
        print(f'⚠ {len(over)}/{len(all_subs)} 块字幕在 {SUB_SIZE}px 下超过安全区 {SUB_MAX_W}px'
              f'（会自动缩字号；建议每块 {SUB_BUDGET[lang]}，用 | 再切一刀）：')
        for sb, w in over[:5]:
            print(f"    f{sb['from']} (≈{w:.0f}px{'，会折两行' if w > SUB_MAX_W * 1.3 else ''}) {sb['text']}")
    # 输出
    tl = {'fps': FPS, 'total_frames': total, 'engine': ENGINE,
          'voice': {'edge': VOICE, 'piper': PIPER_VOICE_NAME, 'kokoro_onnx': KOKORO_ONNX_VOICE}.get(ENGINE, KOKORO_VOICE),
          'rate': RATE if ENGINE == 'edge' else KOKORO_SPEED,
          'gap': GAP, 'para_gap': PARA_GAP, 'chapter_gap': CHAPTER_GAP, 'lead': LEAD, 'tail': TAIL,
          'lang': lang, 'chapters': chapters, 'sentences': sentences, 'chars': total_chars, 'words': total_words,
          'speech_sec': round(speech_sec, 2)}
    unit, cnt = ('字', total_chars) if lang == 'zh' else ('词', total_words)
    os.makedirs(f'{ROOT}/script', exist_ok=True)
    json.dump(tl, open(f'{ROOT}/script/timeline.json', 'w'), ensure_ascii=False, indent=1)
    with open(f'{ROOT}/script/timeline.md', 'w') as f:
        f.write(f"# 时间轴（{ENGINE} · {tl['voice']} {tl['rate']}，共 {total} 帧 = {total/FPS:.1f}s，{cnt} {unit}，语速 {cnt/max(1e-6,speech_sec):.2f} {unit}/s）\n\n")
        f.write('| 句 | 章 | 帧 from–to | 时长 | 末块 | 段末 | 文本（| 为字幕切分） |\n|---|---|---|---|---|---|---|\n')
        ci = {c['from']: c for c in chapters}
        for s in sentences:
            for c in chapters:
                if s['from'] >= c['from'] and (not any(s['from'] >= c2['from'] > c['from'] for c2 in chapters)):
                    pass
            last = s['to'] - s['subs'][-1]['from'] + 1
            warn = '⚠' if s['para'] and last < SHORT_TAIL else ''
            f.write(f"| {s['id']} | {s['chapter']} | {s['from']}–{s['to']} | {(s['to']-s['from']+1)/FPS:.1f}s | {last}{warn} | {'¶' if s['para'] else ''} | {'｜'.join(sb['text'] for sb in s['subs'])} |\n")
        f.write('\n## 章节起始帧\n')
        for c in chapters:
            f.write(f"- 第{c['n']}章 {c['title']}：f{c['from']}\n")
        f.write(f'\n段末 ¶ = narration.txt 里空行/章界前的那句（一个镜头讲完，画面在这里停 1–1.5 s 再切；段内句只隔 {GAP} 帧，不停顿）。\n')
        f.write(f'末块 = 末尾字幕块的帧数（段末句 ⚠ <{SHORT_TAIL}：末拍元素 22 帧入场 + 8 帧离场后停不满 30 帧）。补法：该句后加 `## gap 15–30` 重跑（缓存命中），或分镜时把末拍元素前挂到上一块。\n')
    # 段末句的末块体检（composition-and-light.md §7 落位停留）；段内句不判——它们不换镜头，不需要停留
    short = [(s['id'], s['to'] - s['subs'][-1]['from'] + 1) for s in sentences if s['para'] and s['to'] - s['subs'][-1]['from'] + 1 < SHORT_TAIL]
    paras = sum(1 for s in sentences if s['para'])
    if short:
        print(f'⚠ {len(short)}/{paras} 个段末句的末块 <{SHORT_TAIL} 帧（末拍元素落位后停不满 30 帧）：' + ' '.join(f'{i}({n})' for i, n in short))
        print('    → 在这些句后加 `## gap 15–30` 重跑（不改词、缓存命中），或分镜时把末拍元素前挂到上一块')
    print(f'{len(sentences)} 句分成 {paras} 段（空行分段 → 每段一个镜头；段末停 {GAP + PARA_GAP} 帧，段内 {GAP} 帧）')
    print(f'成片 {total/FPS:.1f}s，其中纯语音 {speech_sec:.1f}s（段末与章前留白是停留预算，成片比语音长 {(total/FPS/max(speech_sec,1e-6)-1)*100:.0f}% 属正常）')
    # 文本一律走 json.dumps：JSON 字符串就是合法的 TS 字面量，且会转义 " \ 与控制字符
    # （手工拼引号会被解说词里的 \ ' ` ${} 破坏语法，甚至把文本写成代码）
    def lit(s):
        return json.dumps(s, ensure_ascii=False)
    with open(f'{REM}/src/common/subs.ts', 'w') as f:
        f.write('// 自动生成：scripts/tts_build.py（词边界 / 逐块合成 → 字幕块）。手改请改 script/narration.txt 后重跑。\n')
        f.write("export type SubEntry = {from: number; to: number; text: string};\nexport const SUBS: SubEntry[] = [\n")
        for sb in all_subs:
            f.write(f"  {{from: {sb['from']}, to: {sb['to']}, text: {lit(sb['text'])}}},\n")
        f.write('];\n')
    with open(f'{REM}/src/common/timeline.ts', 'w') as f:
        f.write('// 自动生成：scripts/tts_build.py。帧号 1 起含端点。\n')
        f.write(f'export const TOTAL_FRAMES = {total};\n')
        f.write('export const CHAPTER_STARTS: Array<{n: number; title: string; from: number}> = [\n')
        for c in chapters:
            f.write(f"  {{n: {c['n']}, title: {lit(c['title'])}, from: {c['from']}}},\n")
        f.write('];\n')
        f.write('export type Sentence = {id: string; chapter: number; from: number; to: number; text: string};\n')
        f.write('export const SENTENCES: Sentence[] = [\n')
        for s in sentences:
            f.write(f"  {{id: {lit(s['id'])}, chapter: {s['chapter']}, from: {s['from']}, to: {s['to']}, text: {lit(s['text'])}}},\n")
        f.write('];\n')
    print(f'lang={lang} engine={ENGINE} voice={tl["voice"]} total_frames={total} ({total/FPS:.1f}s) '
          f'sentences={len(sentences)} {"chars" if lang == "zh" else "words"}={cnt} speech={speech_sec:.1f}s '
          f'rate={cnt/max(1e-6,speech_sec):.2f} {unit}/s')
    for c in chapters:
        print(f"  chapter {c['n']} {c['title']} from f{c['from']}")

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/script/narration.txt'))
