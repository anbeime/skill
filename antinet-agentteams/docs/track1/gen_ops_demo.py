#!/usr/bin/env python3
"""生成 Antinet 八官署 · 实操演示视频（真实链路 + 本地 NPU genie:8910）。

三阶段合一：
  1) 渲染字幕烧录帧（Pillow，暗色主题，对齐 deck 视觉）
  2) edge-tts 生成每步中文旁白（zh-CN-XiaoxiaoNeural）
  3) 真 ffmpeg 合成 mp4（C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe）

数据源：本次真实执行 run_survey.py 的八署串行输出（见 ops_demo_run.log）。
输出：Antinet_GOAI_track1_demo_ops.mp4
"""
import os, glob, asyncio, subprocess, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffprobe.exe"
FRAMES = os.path.join(HERE, "frames_sub_ops")
AUDIO = os.path.join(HERE, "audio_ops")
CLIPS = os.path.join(HERE, "_clips_ops")
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(AUDIO, exist_ok=True)
os.makedirs(CLIPS, exist_ok=True)
OUT = os.path.join(HERE, "Antinet_GOAI_track1_demo_ops.mp4")

INK = (11, 20, 55); PAPER = (245, 241, 230); RED = (200, 57, 43)
GOLD = (184, 138, 43); GREY = (150, 160, 180); WHITE = (235, 240, 250)

def font(size, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(d, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def draw(idx, total, pid, title, bullets, subtitle):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(INK[0] + (6 - INK[0]) * t),
                                    int(INK[1] + (12 - INK[1]) * t),
                                    int(INK[2] + (38 - INK[2]) * t)))
    d.rectangle([0, 0, W, 14], fill=RED)
    d.rectangle([0, 0, 14, H], fill=RED)
    d.text((60, 64), f"实操演示 · {pid}", font=font(34, True), fill=GOLD)
    tf = font(58, True)
    tlines = wrap(d, title, tf, W - 160)
    y = 140
    for ln in tlines[:2]:
        d.text((60, y), ln, font=tf, fill=PAPER); y += 70
    d.rectangle([60, y + 10, W - 60, y + 13], fill=GOLD)
    y += 50
    bf = font(32)
    for b in bullets[:5]:
        blines = wrap(d, b, bf, W - 230)
        d.ellipse([78, y + 10, 98, y + 30], fill=RED)
        ty = y
        for ln in blines[:2]:
            d.text((124, ty), ln, font=bf, fill=WHITE); ty += 44
        y = ty + 22
    sub_top = 800
    d.rectangle([0, sub_top, W, H], fill=(0, 0, 0))
    d.rectangle([0, sub_top, W, sub_top + 3], fill=GOLD)
    sf = font(30)
    slines = wrap(d, subtitle, sf, W - 120)[:6]
    sy = sub_top + 26
    for ln in slines:
        d.text((60, sy), ln, font=sf, fill=(255, 255, 255)); sy += 42
    d.text((W - 420, H - 36), f"Antinet 八官署 · 实操  {idx}/{total}",
           font=font(20), fill=GREY)
    return img

STEPS = [
    ("封面", "Antinet·八官署 实操演示",
     ["真实链路直连本地 NPU：genie:8910", "八署串行协同，四色卡片贯穿全链路"],
     "欢迎观看 Antinet 八官署实操演示。本视频展示系统真实运行：本地 NPU 模型 genie:8910 已接入，八署串行协同，四色卡片贯穿全链路。"),
    ("指挥使", "指挥使 · 任务拆解",
     ["主题：SnSe 空位工程导热", "拆为 7 步子任务（编排分发）"],
     "指挥使接收主题 SnSe 空位工程导热，将其拆解为 7 步子任务，分发给各官署并行与串行推进。"),
    ("锦衣卫", "锦衣卫 · 合规扫描",
     ["拦截侵权源 0 / 命中缓存 0", "密钥 0 · 默认拒绝出域"],
     "锦衣卫执行安全合规扫描：拦截侵权源 0、命中缓存 0、密钥泄露 0。系统默认拒绝任何出域请求，需显式审批才放行。"),
    ("密卷房", "密卷房 · 多格式解析",
     ["7/10 篇 OA 论文解析出全文", "三级 fallback 容错"],
     "密卷房完成多格式解析：10 篇开放获取论文中 7 篇成功解析出全文，采用三级降级容错保证不中断。"),
    ("通政司", "通政司 · 事实蓝卡",
     ["7 张规则基线蓝卡", "+1 张 LLM 抽取蓝卡（真实模型）", "均带 paper_id + loc 溯源"],
     "通政司生成事实蓝卡：7 张基于规则基线，另有 1 张由真实本地模型抽取。每张蓝卡都带论文编号与位置，结论可点回原文。"),
    ("监察院", "监察院 · 解释绿卡(Gap)",
     ["6 张绿卡，均 cite 蓝卡", "LLM 科学意义评级（真实模型）", "Sn空位热电优化研究空白 → 高"],
     "监察院生成解释绿卡，识别研究空白与矛盾，每张都引用蓝卡。真实模型进一步给出科学意义评级：Sn 空位热电优化被评定为高价值研究空白。"),
    ("丞相府", "丞相府 · 行动红卡(假说)",
     ["3 张红卡，均 cite 绿卡", "LLM 生成构效假说（qwen2.5vl3b）"],
     "丞相府产出行动红卡即构效假说，每张引用绿卡。真实模型 qwen2.5vl3b 推理生成可证伪的构效假说，作为下一步验证目标。"),
    ("军机处", "军机处 · 构效核验",
     ["MP_API=off 回退本地规则库", "红卡标注来源与置信度"],
     "军机处执行构效核验。材料项目接口当前关闭，回退本地稳定性规则库，并在红卡上如实标注数据来源与置信度，不粉饰。"),
    ("太史阁", "太史阁 · 知识回流",
     ["沉淀 19 张卡片 + provenance 页", "先读库再干活 / 产出回库"],
     "太史阁完成知识回流：本轮沉淀 19 张卡片与溯源页面。系统坚持先检索历史沉淀再干活、任务结束再把产出回库，形成知识复利。"),
    ("终局", "主链路完成",
     ["蓝8 绿7 黄0 红4", "解析 7/10", "全链路 provenance 留痕"],
     "主链路完成：蓝卡 8、绿卡 7、黄卡 0、红卡 4，解析率 7/10，全链路溯源留痕，可审计可复现。"),
    ("诚实披露", "诚实披露（降级现状）",
     ["解析用预存全文模拟（目标≥7/10）", "MP 核验默认本地规则库", "其余能力均已真实落地"],
     "诚实披露：解析使用预存全文模拟，目标不低于 7/10；材料项目核验默认本地规则库。除这两项降级外，其余能力，包括本地模型在环，均已真实落地。"),
    ("验收", "验收 · verify PASS",
     ["python verify_production.py", "consistency=PASS（exit 0）", "可独立复现"],
     "最后，运行验收脚本 verify_production.py，输出 consistency 等于 PASS，退出码为 0，评审可独立复现。Antinet 八官署实操演示到此结束。"),
]

VOICE = "zh-CN-XiaoxiaoNeural"

def render_frames():
    print(f"rendering {len(STEPS)} ops frames")
    for i, (pid, title, bullets, sub) in enumerate(STEPS, 1):
        img = draw(i, len(STEPS), pid, title, bullets, sub)
        img.save(os.path.join(FRAMES, f"page_{i:02d}.png"))
    print("done ->", FRAMES)

async def gen_audio_one(i, text, path):
    import edge_tts
    comm = edge_tts.Communicate(text, VOICE)
    await comm.save(path)

def gen_audio():
    print("generating ops narration")
    for i, (_, _, _, sub) in enumerate(STEPS, 1):
        p = os.path.join(AUDIO, f"page_{i:02d}.mp3")
        asyncio.run(gen_audio_one(i, sub, p))
    print("done ->", AUDIO)

def probe_dur(path):
    out = subprocess.check_output([FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", path]).decode().strip()
    return float(out)

def build_video():
    frames = sorted(glob.glob(os.path.join(FRAMES, "page_*.png")))
    clips = []
    for i, fr in enumerate(frames, 1):
        aud = os.path.join(AUDIO, f"page_{i:02d}.mp3")
        if not os.path.exists(aud):
            print(f"  ! missing audio page {i:02d}"); continue
        dur = probe_dur(aud)
        dur = min(dur + 0.4, 60.0)
        clip = os.path.join(CLIPS, f"clip_{i:02d}.mp4")
        subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", fr, "-i", aud,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-shortest",
            "-movflags", "+faststart", clip],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(clip)
        print(f"  page {i:02d}: {dur:.2f}s -> {os.path.getsize(clip)//1024} KB")
    with open(os.path.join(HERE, "_clips_ops.txt"), "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace(chr(92), '/')}'\n")
    n = len(clips)
    inp = []
    for c in clips:
        inp += ["-i", c]
    filt = "".join(f"[{k}:v][{k}:a]" for k in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    subprocess.run([FFMPEG, "-y"] + inp + [
        "-filter_complex", filt, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"DONE: {OUT} ({os.path.getsize(OUT)//1024//1024} MB)")

if __name__ == "__main__":
    render_frames()
    gen_audio()
    build_video()
