# -*- coding: utf-8 -*-
"""Step 6 - build the 即梦 Seedance web packs: one folder per segment with the vocal, the reference images and a
copy-paste prompt.

usage: python scripts/seedance_packs.py <episode_dir> [--only 03]

Segments: 00 opening (3 s push-in), A's verse in 4-line packs, the break, B's verse in 4-line packs, the ending.
Each singing pack: the rapper's clean vocal for those 4 bars (from the first word to just before the next line's
first word, 0.3 s of silence in front, padded to whole seconds), the busts, the venue, the DJ, the rapper's face
sheet, and a prompt where every shot says WHICH half-line is sung in WHICH seconds (to 0.01 s, measured from the
vocal). That timed-lyric prompt is what made the lips match; lyrics without times make Seedance re-read the text
in its own rhythm. Writes seedance/<NN_...>/ and work/seedance_plan.json.
"""
import math
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, jload, jsave, load_episode  # noqa: E402
from seedance_align import LEAD, audio16, match, words  # noqa: E402

STYLE = ("画面风格：夜晚，火盆的暖色火光对上方冷白色聚光灯，烟雾，背景虚焦，电影感暗调，35mm 胶片颗粒，手持轻微晃动。"
         "两人的脸、发型、服装和参考图完全一致。无字幕，无文字，无水印。")
DEFAULT_SHOTS = ["{me}半身近景，身体侧转四分之三朝向镜头", "双人中景，膝盖以上", "{me}近景，稍微仰拍", "越过{other}肩膀拍{me}"]
DEFAULT_ACT = "跟着节奏点头，空着的手比划"


def cut(src, s0, t1, dur, out):
    """song [s0, t1] -> LEAD s of silence + that audio, padded with silence to dur seconds"""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % s0, "-to", "%.3f" % t1, "-i", src, "-af",
                    "afade=t=in:d=0.01,afade=t=out:st=%.3f:d=0.03,adelay=%d:all=1,apad=whole_dur=%d"
                    % (t1 - s0 - 0.03, int(LEAD * 1000), dur), "-ac", "2", "-ar", "44100", "-b:a", "256k", out],
                   check=True)


def phrase_times(aud, ls, work):
    """{(line index, half-line index): [start, end]} in the pack audio, from the recogniser's character times
    matched to the lyric by pinyin; unmatched characters are interpolated"""
    lyr = [(li, pi, c) for li, l in enumerate(ls) for pi, ph in enumerate(l["text"].split()) for c in ph]
    heard = words(audio16(aud, work), " ".join(l["text"] for l in ls))
    t = [None] * len(lyr)
    for i, j in match([(c, 0) for _, _, c in lyr], heard):
        t[i] = heard[j][1]
    for i in range(len(t)):
        if t[i] is None:
            prv = next((j for j in range(i - 1, -1, -1) if t[j] is not None), None)
            nxt = next((j for j in range(i + 1, len(t)) if t[j] is not None), None)
            if prv is not None and nxt is not None:
                t[i] = t[prv] + (t[nxt] - t[prv]) * (i - prv) / (nxt - prv)
            elif prv is not None:
                t[i] = t[prv] + 0.18 * (i - prv)
            else:
                t[i] = (t[nxt] if nxt is not None else LEAD) - 0.18 * ((nxt or i) - i)
    out = {}
    for k, (li, pi, _) in enumerate(lyr):
        key = (li, pi)
        end = t[k + 1] if k + 1 < len(lyr) and lyr[k + 1][:2] == key else t[k] + 0.22
        out.setdefault(key, [t[k], end])[1] = end
    keys = sorted(out)
    out[keys[0]][0] = max(out[keys[0]][0], LEAD)        # the recogniser snaps the first word to 0
    for a, b in zip(keys, keys[1:]):                     # neighbouring phrases never overlap
        out[a][1] = min(out[a][1], out[b][0] - 0.02)
    return out


def main():
    if len(sys.argv) < 2:
        die("usage: seedance_packs.py <episode_dir> [--only NN]")
    ep = sys.argv[1]
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    e = load_episode(ep)
    work = os.path.join(ep, "work")
    L = jload(os.path.join(work, "lines.json"))
    voc = os.path.join(work, "vocals_clean.wav")
    if not os.path.exists(voc):
        die("run clean_vocal.py first")
    refs = os.path.join(ep, "refs")
    for k in ("a_bust", "b_bust", "a_sheet", "b_sheet", "a_face", "b_face", "venue", "crowd", "dj"):
        if not os.path.exists(os.path.join(refs, k + ".png")):
            die("missing refs/%s.png (see references/midjourney.md)" % k)
    A, B = e["a"], e["b"]
    venue = e.get("venue_cn", "说唱擂台")
    look = {"a": A["look_cn"], "b": B["look_cn"]}
    sides = "%s永远在画面左边、朝右，%s永远在画面右边、朝左，谁都不换边。" % (A["name_cn"], B["name_cn"])
    shots_cfg = e.get("shots", {})
    plan, n = [], 0

    def pack(name):
        d = os.path.join(ep, "seedance", "%02d_%s" % (n, name))
        os.makedirs(d, exist_ok=True)
        return d

    def imgs(d, items):
        for i, (key, label) in enumerate(items, 1):
            shutil.copy(os.path.join(refs, key + ".png"), os.path.join(d, "图片%d_%s.png" % (i, label)))
        return "、".join("图片%d_%s" % (i, lab) for i, (_, lab) in enumerate(items, 1))

    full = "（三视图是同一个人的正面、侧面、背面，画面里每人只出现一个）"
    # 00 opening
    d = pack("开场")
    if not only or only == "00":
        up = imgs(d, [("venue", "场景"), ("a_sheet", "%s全身" % A["name_cn"]), ("b_sheet", "%s全身" % B["name_cn"]),
                      ("crowd", "士兵"), ("dj", "DJ")])
        txt = e.get("opening_cn") or (
            "开场镜头，一个镜头不切。机位在观众身后，前景是几只举起来指向舞台的观众的手和火把，虚焦。舞台上%s站在左边、%s站在右边，"
            "两人面对面站着对峙，互相盯着，都不说话，手里都拿着话筒。一束冷白色聚光灯从上方打在两人中间，烟雾很浓。镜头从观众头顶缓慢、平稳地"
            "向前推进，两人在画面中逐渐变大，推到膝盖以上。" % (A["name_cn"], B["name_cn"]))
        open(os.path.join(d, "提示词.txt"), "w", encoding="utf-8").write(
            "【用在】片头，成片里用最后约 2.5 秒，标题叠在上面\n【上传】%s（不传音频）\n【设置】16:9，时长选最短（4 或 5 秒）；不用对口型\n\n【提示词】\n"
            "@图片1 是场景：%s。@图片2 是%s，@图片3 是%s%s。@图片4 是观众的样子。@图片5 是 DJ：后方 DJ 台上始终站着这个 DJ 在打碟。\n\n%s\n\n%s\n"
            % (up, venue, A["name_cn"], B["name_cn"], full, txt, STYLE))
    plan.append({"folder": os.path.basename(d), "kind": "open"})

    for who, me_p, other_p in (("a", A, B), ("b", B, A)):
        ls_all = [l for l in L if l["who"] == who]
        me, other = me_p["name_cn"], other_p["name_cn"]
        for g in range(0, len(ls_all), 4):
            n += 1
            ls = ls_all[g:g + 4]
            first, last = ls[0]["n"], ls[-1]["n"]
            d = pack("%s第%d-%d句" % (me, first, last))
            s0 = ls[0]["start"] - 0.02
            nxt = ls_all[g + 4] if g + 4 < len(ls_all) else None
            t1 = nxt["start"] - 0.02 if nxt else ls[-1]["end"] + 0.4
            dur = math.ceil(LEAD + t1 - s0)
            t0 = s0 - LEAD
            aud_name = "音频1_%s人声.mp3" % me
            plan.append({"folder": os.path.basename(d), "kind": "sing", "who": who, "first": first, "last": last,
                         "song_t0": round(t0, 3), "dur": dur, "audio": aud_name})
            if only and only != "%02d" % n:
                continue
            for f in os.listdir(d):
                if f.startswith("图片") or f.startswith("音频"):
                    os.remove(os.path.join(d, f))
            up = imgs(d, [(who + "_bust", "%s半身" % me), ({"a": "b", "b": "a"}[who] + "_bust", "%s半身" % other),
                          ("venue", "场景"), ("dj", "DJ"), (who + "_face", "%s表情" % me)])
            aud = os.path.join(d, aud_name)
            cut(voc, s0, t1, dur, aud)
            pt = phrase_times(aud, ls, work)
            shot_lines = []
            for i, l in enumerate(ls):
                key = "%s%d" % (who.upper(), l["n"])
                cfg = shots_cfg.get(key, [])
                shot = (cfg[0] if len(cfg) > 0 and cfg[0] else DEFAULT_SHOTS[i % 4]).format(me=me, other=other)
                act = cfg[1] if len(cfg) > 1 and cfg[1] else DEFAULT_ACT
                a = 0.0 if i == 0 else round(l["start"] - t0 - 0.1, 1)
                b = round(ls[i + 1]["start"] - t0 - 0.1, 1) if i + 1 < len(ls) else dur
                sung = "，".join("%.2f–%.2f 秒「%s」" % (pt[(i, j)][0], pt[(i, j)][1], ph)
                                for j, ph in enumerate(l["text"].split()))
                shot_lines.append("镜头%d（%.1f–%s 秒）：%s，%s唱：%s，嘴型逐字对上 @音频1 里这几秒的声音，%s边唱边%s。" % (
                    i + 1, a, ("%.1f" % b) if i + 1 < len(ls) else str(dur), shot, me, sung, me, act))
            prompt = "\n".join([
                "【上传】%s、音频1_%s人声（%d 秒）" % (up, me, dur),
                "【设置】16:9，时长 %d 秒（和音频一样长）；先用 480p 测试，满意了用「超清」放大同一条（不要重新生成）" % dur,
                "【第二步】嘴型还不准就点「对口型」，上传 %s，不输入台词，不写提示词" % aud_name,
                "",
                "【提示词】",
                "@图片1 是%s，@图片2 是%s，@图片3 是场景：%s。@图片4 是 DJ：后方 DJ 台上始终站着这个 DJ，戴着耳机低头打碟、跟着节奏点头，"
                "镜头能拍到 DJ 台时他一定在。@图片5 是%s的表情参考。音频参考：参考 @音频1 的节奏，%s跟着 @音频1 的节拍对着话筒说唱。"
                % (me, other, venue, me, me),
                "",
                "声音和口型（最重要）：视频的声音就是 @音频1 原样，不重新配音、不重新念、不改快慢，每句在下面写的秒数开口和结束。",
                "",
                "人物：%s：%s；%s：%s。%s整段都在对着话筒说唱，嘴一直在动、口型清楚，脸不要被话筒、手和道具挡住。%s只听不说，嘴一直闭着，"
                "表情是%s。%s" % (A["name_cn"], look["a"], B["name_cn"], look["b"], me, other,
                                other_p.get("listen_cn", "冷眼看着、嘴角冷笑"), sides),
                "",
                "分镜：",
                *shot_lines,
                "",
                STYLE,
            ])
            open(os.path.join(d, "提示词.txt"), "w", encoding="utf-8").write(prompt + "\n")
            print(os.path.basename(d), "song %.2f, %ds" % (t0, dur))
        if who == "a":
            n += 1
            d = pack("间奏")
            if not only or only == "%02d" % n:
                up = imgs(d, [("venue", "场景"), ("crowd", "士兵"), ("a_sheet", "%s全身" % A["name_cn"]),
                              ("b_sheet", "%s全身" % B["name_cn"]), ("dj", "DJ")])
                txt = e.get("break_cn") or (
                    "镜头：台下观众的中景，挤在一起举着火把和拳头，整齐地一下一下往上捶，张大嘴齐声喊口号，情绪激动，火光映在脸上。镜头从观众头顶"
                    "缓慢往舞台方向推，最后一秒越过观众的头看到台上：%s站在左边，%s站在右边，慢悠悠举起话筒准备开口。" % (A["name_cn"], B["name_cn"]))
                open(os.path.join(d, "提示词.txt"), "w", encoding="utf-8").write(
                    "【用在】A 唱完到 B 开口之间的间奏，成片里用最后约 2.5 秒\n【上传】%s（不传音频）\n【设置】16:9，时长选最短（4 或 5 秒）；不用对口型\n\n"
                    "【提示词】\n@图片1 是场景：%s。@图片2 是观众的样子。@图片3 是%s，@图片4 是%s%s。@图片5 是 DJ，在后方 DJ 台上打碟。\n\n%s\n\n%s\n"
                    % (up, venue, A["name_cn"], B["name_cn"], full, txt, STYLE))
            plan.append({"folder": os.path.basename(d), "kind": "break"})
    n += 1
    d = pack("片尾")
    if not only or only == "%02d" % n:
        up = imgs(d, [("b_bust", "%s半身" % B["name_cn"]), ("a_bust", "%s半身" % A["name_cn"]), ("venue", "场景"),
                      ("crowd", "士兵"), ("dj", "DJ"), ("b_face", "%s表情" % B["name_cn"]), ("a_face", "%s表情" % A["name_cn"])])
        txt = e.get("ending_cn") or (
            "分镜：\n镜头1（0–3.5 秒）：%s半身近景，站在画面右边、身体朝左，慢慢把话筒从嘴边放下，嘴角一点点挑起，露出得意的笑，眼睛看着画面左边。"
            "背景虚焦，身后的观众举着火把欢呼。机位固定，只有很轻微的推近。\n"
            "镜头2（3.5–8 秒）：双人中景，膝盖以上，机位正对舞台、固定不动。%s站在画面左边，无奈地轻轻摇头，嘴闭着；%s站在画面右边，"
            "把话筒缓缓举过头顶，嘴闭着微笑。两人都站在原地不走动。后方 DJ 在打碟，台下观众举着火把和拳头欢呼。\n\n"
            "动作要求：两人动作幅度小、速度慢，不转身、不走路、不快速挥手，脸始终看得清楚。" % (B["name_cn"], A["name_cn"], B["name_cn"]))
        open(os.path.join(d, "提示词.txt"), "w", encoding="utf-8").write(
            "【用在】片尾，最后叠「下一场你想看谁的对决？」\n【上传】%s（不传音频）\n【设置】16:9，时长 8 秒；不用对口型\n"
            "（不要全景、不要拉远升高、不要人物走路——人一小、一转身脸就变形；近景 + 半身图 + 表情近照最稳）\n\n【提示词】\n"
            "@图片1 是%s，@图片2 是%s。@图片6 是%s的表情近照，@图片7 是%s的表情近照，四格都是同一个人的脸。两人的脸、五官、发型、胡子、"
            "帽子、服装必须和这几张图一模一样，全程清晰、不变形、不变年轻。@图片3 是场景：%s。@图片4 是台下观众的样子。@图片5 是 DJ，在后方 DJ 台上打碟。\n\n%s\n\n%s\n"
            % (up, B["name_cn"], A["name_cn"], B["name_cn"], A["name_cn"], venue, txt, STYLE))
    plan.append({"folder": os.path.basename(d), "kind": "end"})
    old = {}
    pp = os.path.join(work, "seedance_plan.json")
    if only and os.path.exists(pp):
        old = {x["folder"]: x for x in jload(pp)}
    for x in plan:
        old[x["folder"]] = x
    jsave(pp, sorted(old.values(), key=lambda x: x["folder"]))
    print("wrote %d packs into seedance/ - check each 音频1 sounds complete (first and last word)" % len(plan))


if __name__ == "__main__":
    main()
