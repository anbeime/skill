# -*- coding: utf-8 -*-
"""Step 5 - shots, prompts and the edit list, from the shot template (references/shot-template.md).

usage: python scripts/make_clips.py <episode_dir>
needs: work/lines.json (analyze_song.py), refs/*.png (Midjourney)
writes: work/clips.json (one entry per H3 generation), work/edl.json (what plays when),
        分镜表.md (Chinese storyboard with every prompt), work/a_bust.png / b_bust.png
Rules baked in (all learned the hard way): one lyric line per lip-sync clip, waist-up refs for close shots,
framing rule first, exact-audio rule, rapper three-quarters to camera holding the mic, whoever raps stands
on the LEFT in two-shots, stage never empty, hecklers at most 3 times, no shot used twice in a row.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, die, jload, jsave, load_episode, ref  # noqa: E402

# ---------------------------------------------------------------- camera moves (M1-M14)
MOVES = {
    "M1": ("Starts as a wide shot from just behind the front row of the crowd: the two men face each other about three meters "
           "apart in the spotlit circle, the DJ booth glowing behind them. The camera then pushes in fast past {B}'s shoulder, "
           "which ends up out of focus in the left foreground, and settles on a medium shot of {A} on the right, who lifts his "
           "microphone, eyes locked on his rival, while {B} calmly holds his {PROP}. Both men are silent with mouths closed."),
    "M1b": ("Starts as a wide view of both men in the spotlit circle seen from the crowd, then the camera pushes in fast to a close "
            "two-shot, both framed from the chest up. Audio 1 begins with half a second of silence: during it {X} calmly lifts the "
            "microphone to his mouth, then raps Audio 1 with exact lip sync, {ACTION}; {Y} listens, silent and stiff."),
    "M2": ("Extreme close-up for the whole shot, never starting wider: frontal, eye level, a very slow push-in. {X}'s face fills "
           "the upper two thirds of the frame, the silver microphone at his chin; he raps Audio 1 with exact lip sync straight into "
           "the lens, {ACTION}. Behind him only blurred blue-white LED tubes and red lantern bokeh; the overhead spotlight carves "
           "his cheekbones."),
    "M3": ("Waist-up medium shot, three-quarter front view, eye level, gentle push-in. {X} raps Audio 1 with exact lip sync, "
           "{ACTION}. Dark, blurred crowd and red lantern bokeh behind him."),
    "M3d": ("Waist-up medium shot, three-quarter front view, eye level. {X} raps Audio 1 with exact lip sync, {ACTION}. Dark, "
            "blurred crowd and red lantern bokeh behind him. Near the end the camera drifts right, revealing {Y}, silent, at the "
            "right edge of frame."),
    "M4": ("Medium shot, eye level. {X} center-left raps Audio 1 with exact lip sync while {ACTION}. {Y} stands in profile in the "
           "right third of the frame, watching silently with a faint smile."),
    "M5": ("Medium two-shot at eye level, both framed from the waist up. {X} raps Audio 1 with exact lip sync, {ACTION}; {Y} stays "
           "silent and still. The DJ booth and the spotlight beam sit in the center background between them."),
    "M6": ("Close two-shot, both framed from the chest up, faces about half a meter apart. {X} raps Audio 1 with exact lip sync, "
           "{ACTION}. {Y} listens, mouth closed."),
    "M7": ("Low-angle medium shot with the overhead spotlight lamp visible at the top of frame, haze glowing in its beam. {X} raps "
           "Audio 1 with exact lip sync, raising his microphone arm high, then on the last words points sharply at {Y}, who "
           "stands silent in the right third of the frame, and holds the pose."),
    "M7b": ("Medium-wide frontal shot from a slightly low angle, standing alone in the circle with the overhead spotlight beam "
            "pouring down on him through the haze. {X} raps Audio 1 with exact lip sync, {ACTION}, while the crowd erupts behind "
            "him; on the very last words the camera punches in fast to an extreme close-up of his face."),
    "M8": ("Medium close-up, frontal, eye level, slow push-in, crowd blurred behind him. {X} listens, silent with mouth closed, "
           "slowly {ACTION}, utterly unbothered. In the last second he calmly lifts his microphone toward his mouth."),
    "M9": ("The camera swings in quickly from his side and settles into a frontal medium shot at eye level, the packed crowd "
           "blurred behind him and the spotlight above. {X} raps Audio 1 with exact lip sync, {ACTION}."),
    "M10": ("Wide shot from behind the crowd at head height, looking over the backs of heads and raised fists toward the spotlit "
            "circle and the DJ booth beyond. In the circle, small in frame but clearly visible, {X} on the left raps into his "
            "microphone, {ACTION}, while {Y} on the right stands listening. Slow handheld drift from left to right. The circle is "
            "never empty: both men stay in it the whole time. The crowd is seen only from behind; no face is clearly visible."),
    "M11": ("Medium shot, frontal, in the packed crowd: the three commoners from their reference image, arms over each other's "
            "shoulders, laugh hysterically, point toward the circle off-screen and slap their thighs; red lanterns behind them."),
    "M11b": ("Close medium shot, shaky handheld, slight motion blur. The three commoners from their reference image jump and "
             "scream together, pumping fists toward the camera, euphoric, the crowd going wild around them."),
    "M12": ("Starts on {B}'s grinning face, blurred in the left foreground, holding the tip of his {PROP} near {A}'s nose; the "
            "camera pans right and focuses on a close-up profile of {A} facing left, silent with mouth closed, jaw clenched; his "
            "eye twitches, then he forces a tight, furious smile. Lantern bokeh behind."),
    "M13": ("Medium shot from a slightly low angle of the DJ from his reference image at the raised booth, blue-white LED tubes "
            "behind him, scratching a vinyl record, head nodding to the beat; the camera then pushes in to his hands on the "
            "turntable and the glowing mixer."),
    "M14": ("Starts at eye level in the spotlit circle: {B} walks calmly toward the camera, then stops and spreads his arms wide "
            "with the {PROP} raised like a champion; {A} stands behind him on the left, turned half away, arms crossed, sulking. "
            "The camera rises and pulls back into a high wide view looking down over the whole cheering crowd, the two men small in "
            "the center of the circle. Fists in the air everywhere. Both men's mouths are closed."),
}
WIDE = {"M1", "M10", "M14"}
DEFAULT_ACTION = "fierce and confident, his free hand chopping the air on the beat"

# rap move for every line (positions follow references/shot-template.md); missing lines are cutaways
RAP_A = {1: "M2", 2: "M5", 3: "M3d", 7: "M4", 8: "M2", 9: "M5", 10: "M3", 11: "M6", 13: "M3", 14: "M2", 15: "M3", 16: "M7"}
RAP_B = {1: "M1b", 2: "M3", 3: "M9", 4: "M3", 5: "M6", 6: "M2", 9: "M3", 10: "M5", 11: "M3", 12: "M2",
         14: "M3", 15: "M6", 16: "M3", 17: "M5", 18: "M7b"}
# still clips: id, move, refs, seconds
STILLS = {
    "OPEN": ("M1", ["a_sheet", "b_sheet", "venue", "crowd"], 5),
    "CROWD": ("M10", ["a_sheet", "b_sheet", "venue", "crowd"], 10),
    "B_REACT": ("M8", ["b_bust", "b_face", "venue"], 5),
    "LAUGH": ("M11", ["hecklers", "venue", "crowd"], 5),
    "A_REACT": ("M12", ["a_bust", "a_face", "b_bust", "venue"], 5),
    "DJ": ("M13", ["dj", "venue"], 5),
    "CHANT": ("M11b", ["hecklers", "venue", "crowd"], 5),
    "END": ("M14", ["a_sheet", "b_sheet", "venue", "crowd"], 5),
}
REF_DESC = {
    "a_sheet": "the full-body turnaround sheet of {A}", "b_sheet": "the full-body turnaround sheet of {B}",
    "a_bust": "a waist-up reference of {A} (face, hair, costume)", "b_bust": "a waist-up reference of {B} (face, hair, costume, {PROP})",
    "a_face": "{A}'s face and expressions", "b_face": "{B}'s face and expressions",
    "venue": "the venue, a {ERA} era wooden hall turned into an underground rap battle club",
    "dj": "the DJ", "hecklers": "the three commoners who always cheer together",
    "crowd": ("the look of the crowd: their faces, clothing and colors (the three cheering commoners in it are the same three "
              "people as in the commoners image; each of them appears at most once in any shot)"),
}

FRAMING = ("FRAMING (most important): this is NOT a wide shot. Keep the camera close, exactly at the framing described below "
           "(extreme close-up, close-up, chest-up or waist-up); the characters' legs, feet and the floor never appear in frame, "
           "and faces stay large enough that every mouth movement is clearly readable.")
FRAMING_KNEES = ("FRAMING (most important): frame him from the knees up for most of the shot, never a full-body wide shot; his "
                 "face stays clearly readable, and the final push-in ends on his face.")
SOUND = ("SOUND (most important): the soundtrack is Audio 1 exactly as given - the same voice, every word unchanged, with "
         "identical timing from the first frame to the last. Do not re-sing, re-time, speed up, slow down or replace any part of "
         "it, and add no music or crowd noise over it. The lips follow Audio 1 syllable by syllable.")
STYLE = ("This shot must cut seamlessly with the rest of the film: same venue, same overhead spotlight as the key light from "
         "above, eye-level camera and gentle handheld movement unless a different camera move is described above, 35-50mm lens "
         "look. Setting: the wooden hall rap club from the venue image - dark timber pillars, balconies packed with cheering "
         "commoners, rows of red lanterns, a raised DJ booth with blue-white LED tubes at the back, a cold white spotlight beam "
         "cutting through thick haze onto the circular floor. The crowd are {COMMONERS} in rough hemp cross-collar tunics in earth "
         "tones, with cloth headbands, head wraps or topknots; nobody wears modern clothing except the DJ. Nobody else stands "
         "inside the circle: the crowd is packed only beyond its edge, and behind the main characters it stays dark and out of "
         "focus, every person dressed differently, never matching uniforms. Low-key cinematic lighting with deep shadows, thick "
         "haze, high contrast, warm orange lanterns against cool blue-white light, shallow depth of field, gritty 35mm film grain; "
         "not glossy, not brightly lit.")
TAIL = ("Keep every character's face, hairstyle, costume and colors exactly as in their reference images. {B}'s {PROP} is always "
        "{PROP_DESC}, exactly as in his reference images. No subtitles, no on-screen text, no logos, no watermark.")


def crop_busts(ep):
    """waist-up crops of the front view (left third of the turnaround) - full-body refs make H3 shoot wide"""
    for who in ("a", "b"):
        own = os.path.join(ep, "refs", who + "_bust.png")
        out = ref(ep, who + "_bust")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.exists(own):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", own, out], check=True)
            continue
        sheet = ref(ep, who + "_sheet")
        if not os.path.exists(sheet):
            die("missing " + sheet)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", sheet, "-vf",
                        "crop=iw*0.27:ih*0.44:iw*0.075:0,scale=-2:1024:flags=lanczos", out], check=True)


def main():
    if len(sys.argv) < 2:
        die("usage: make_clips.py <episode_dir>")
    ep = sys.argv[1]
    e = load_episode(ep)
    lines = jload(os.path.join(ep, "work", "lines.json"))
    L = {(l["who"], l["n"]): l for l in lines}
    na, nb = len(e["lyrics"]["a"]), len(e["lyrics"]["b"])
    if (na, nb) != (16, 18):
        print("note: the shot template is laid out for 16 + 18 lines; extra lines become 3/4 medium shots, "
              "missing ones are skipped")
    A, B = e["a"], e["b"]
    sub = {"{A}": A["name_en"], "{B}": B["name_en"], "{PROP}": B.get("prop", "prop"),
           "{PROP_DESC}": B.get("prop_desc", "the same prop as in his reference images"),
           "{ERA}": e.get("era_en", "ancient Chinese"), "{COMMONERS}": e.get("commoners_en", "ancient Chinese commoners")}
    acts = e.get("actions", {})

    def fill(s, X=None, Y=None, action=None):
        if X:
            s = s.replace("{X}", X).replace("{Y}", Y)
        s = s.replace("{ACTION}", action or DEFAULT_ACTION)
        for k, v in sub.items():
            s = s.replace(k, v)
        return s

    def two_rule(left, right):
        return ("{L} ({LL}) stays on the left of frame facing right and {R} ({RL}) stays on the right facing left for the "
                "whole shot; never swap or mix them.").format(L=left["name_en"], LL=left["look"], R=right["name_en"],
                                                              RL=right["look"])

    def build(move, refs, x=None, y=None, action=None, two=None, rapping=False):
        """x = the character the move centres on ({X}), y = the other one ({Y}); rapping adds the audio rules"""
        head = " ".join("Image %d is %s." % (i + 1, fill(REF_DESC[r])) for i, r in enumerate(refs))
        if rapping:
            head += " Audio 1 is %s's rap vocal for this shot; use it as his voice." % x["name_en"]
        parts = [head]
        if move == "M7b":
            parts.append(FRAMING_KNEES)
        elif move not in WIDE and move not in ("M11", "M11b", "M13"):
            parts.append(FRAMING)
        parts.append("Cinematic photoreal shot, 16:9. " + fill(MOVES[move], x and x["name_en"], y and y["name_en"], action))
        if two:
            parts.append(two)
        if rapping:
            parts.append(SOUND)
            if two:
                parts.append("%s, who is rapping, is turned three-quarters toward the camera so his face and lips are clearly "
                             "visible the whole time; the listener is seen in profile." % x["name_en"])
            parts.append("%s holds the silver corded microphone at his mouth in his right hand the whole time he raps. Only %s "
                         "is rapping; every other mouth in the shot stays closed." % (x["name_en"], x["name_en"]))
        parts += [fill(STYLE), fill(TAIL)]
        return "\n\n".join(parts)

    crop_busts(ep)
    clips = []
    for who, n_lines, rap, me, them in (("a", na, RAP_A, A, B), ("b", nb, RAP_B, B, A)):
        tag = who.upper()
        cut_lines = {4, 5, 6, 12} if who == "a" else {7, 8, 13}
        for n in range(1, n_lines + 1):
            if n in cut_lines:
                continue
            move = rap.get(n, "M3")
            l = L[(who, n)]
            lead = 0.5 if move == "M1b" else 0.0
            two_moves = {"M1b", "M5", "M6", "M3d", "M4", "M7"}
            if move in {"M1b", "M5", "M6"}:
                refs = ["a_bust", "a_face", "b_bust", "b_face", "venue"]
            elif move in {"M3d", "M4", "M7"}:
                refs = [who + "_bust", who + "_face", ("b" if who == "a" else "a") + "_bust", "venue"]
            else:
                refs = [who + "_bust", who + "_face", "venue"] + (["crowd"] if move in {"M7b", "M9"} else [])
            two = two_rule(me, them) if move in two_moves else None
            a0 = l["start"] - 0.08 - lead
            clips.append({"id": "%s%02d" % (tag, n), "kind": "rap", "who": who, "line": n, "move": move,
                          "dur": 5, "lead": lead, "audio": [round(l["start"] - 0.08, 3), round(min(l["end"], a0 + 5 - lead), 3)],
                          "image_keys": refs, "text": l["text"],
                          "prompt": build(move, refs, me, them, acts.get("%s%d" % (tag, n)), two, rapping=True)})
    for sid, (move, refs, dur) in STILLS.items():
        if sid == "CROWD":
            prompt = build(move, refs, A, B, acts.get("CROWD"), two_rule(A, B))
        elif sid == "B_REACT":
            prompt = build(move, refs, B, A, acts.get("B_REACT", "fanning himself"))
        else:
            prompt = build(move, refs, A, B)
        clips.append({"id": sid, "kind": "still", "move": move, "dur": dur, "image_keys": refs, "prompt": prompt})
    for c in clips:
        c["images"] = [ref(ep, k) for k in c["image_keys"]]
    jsave(os.path.join(ep, "work", "clips.json"), clips)

    # ------------------------------------------------------------ edit list (timeline -> clip, in-point)
    s = lambda who, n: L[(who, n)]["start"] - 0.08          # noqa: E731  cut just before the first word
    end_a, end_b = L[("a", na)]["end"], L[("b", nb)]["end"]
    total = jload(os.path.join(ep, "work", "grid.json"))["length"]
    edl = [{"t0": 0.0, "t1": s("a", 1), "clip": "OPEN", "in": 1.2}]
    cut_map = {("a", 4): ("CROWD", 0.3), ("a", 5): ("B_REACT", 0.0), ("a", 6): ("LAUGH", 0.0), ("a", 12): ("CROWD", 3.5),
               ("b", 7): ("A_REACT", 0.0), ("b", 8): ("LAUGH", 2.6), ("b", 13): ("A_REACT", 2.55)}
    for who, n_lines in (("a", na), ("b", nb)):
        for n in range(1, n_lines + 1):
            t0 = s(who, n) - (0.5 if (who, n) == ("b", 1) else 0.0)
            t1 = s(who, n + 1) if n < n_lines else L[(who, n)]["end"] + 0.25
            if (who, n) in cut_map:
                cid, inp = cut_map[(who, n)]
                edl.append({"t0": t0, "t1": t1, "clip": cid, "in": inp})
            else:
                edl.append({"t0": t0, "t1": t1, "clip": "%s%02d" % (who.upper(), n), "in": None})
        if who == "a":                                       # interlude: DJ, then B calmly lifts the mic
            i0, i1 = edl[-1]["t1"], s("b", 1) - 0.5
            mid = i0 + (i1 - i0) * 0.55
            edl += [{"t0": i0, "t1": mid, "clip": "DJ", "in": 0.5}, {"t0": mid, "t1": i1, "clip": "B_REACT", "in": 2.6}]
    end0 = max(edl[-1]["t1"], total - 5.1)
    edl += [{"t0": edl[-1]["t1"], "t1": end0, "clip": "CHANT", "in": 1.0}, {"t0": end0, "t1": total, "clip": "END", "in": 0.0}]
    edl = [x for x in edl if x["t1"] - x["t0"] > 0.04]
    jsave(os.path.join(ep, "work", "edl.json"), edl)

    # ------------------------------------------------------------ Chinese storyboard for the user
    secs = sum(c["dur"] for c in clips)
    md = ["# 分镜表：%s" % e["title"], "",
          "共 %d 条素材、%d 秒，768P 约 $%.2f（参考图每条不超过 5 张，不额外收费）。说唱镜头一句一条。" % (len(clips), secs, secs * 0.08), "",
          "## 剪辑顺序", "", "| 时间 | 素材 | 内容 |", "| --- | --- | --- |"]
    for x in edl:
        c = next(c for c in clips if c["id"] == x["clip"])
        what = c.get("text") or {"OPEN": "开场对峙", "CROWD": "观众背影，台上两人在对唱", "B_REACT": "%s淡定反应" % B["name_cn"],
                                 "LAUGH": "气氛组哄笑", "A_REACT": "%s侧脸咬牙" % A["name_cn"], "DJ": "DJ 搓碟",
                                 "CHANT": "气氛组喊口号", "END": "片尾全景"}[c["id"]]
        md.append("| %.1f–%.1f | %s（%s） | %s |" % (x["t0"], x["t1"], c["id"], c["move"], what))
    md += ["", "## 每条素材的提示词", ""]
    for c in clips:
        md += ["### %s · %s · %d 秒" % (c["id"], c["move"], c["dur"]), "",
               "参考图：" + "、".join(c["image_keys"]) + ("　音频：%.2f–%.2f 秒" % tuple(c["audio"]) if c["kind"] == "rap" else ""),
               "", "```", c["prompt"], "```", ""]
    with open(P(ep, "分镜表.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("%d clips, %d s, about $%.2f at 768P -> 分镜表.md, work/clips.json, work/edl.json" % (len(clips), secs, secs * 0.08))


if __name__ == "__main__":
    main()
