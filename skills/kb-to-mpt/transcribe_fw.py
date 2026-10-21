"""用 faster-whisper（项目机器人同款 STT 引擎）转写音频 -> 字幕 vtt。
权重下载根目录与项目一致：backend/data/whisper_models
用法:
  python transcribe_fw.py <audio> --out <dir> --model base|small|medium|large-v3
"""
import argparse, os, sys, time, json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DL_ROOT = os.path.join(PROJECT_ROOT, "data", "whisper_models")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", default=os.path.join(PROJECT_ROOT, "material", "audio"))
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default="zh")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    os.makedirs(DL_ROOT, exist_ok=True)

    from faster_whisper import WhisperModel
    # 直接以目录路径加载（已手动下载到 data/whisper_models/<size>/），
    # 绕开 huggingface_hub 的沙箱 safe-delete 限制，不触发任何下载。
    if os.path.isdir(args.model):
        model_path = args.model
    else:
        model_path = os.path.join(DL_ROOT, args.model)
    print(f"[fw] loading faster-whisper from {model_path}", flush=True)
    t0 = time.time()
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    print(f"[fw] model ready in {time.time()-t0:.1f}s", flush=True)

    segs, info = model.transcribe(args.audio, language=args.lang,
                                  vad_filter=True, word_timestamps=False)
    print(f"[fw] lang={info.language} dur={info.duration:.1f}s", flush=True)

    stem = os.path.splitext(os.path.basename(args.audio))[0]
    vtt = os.path.join(args.out, f"{stem}.vtt")
    txt = os.path.join(args.out, f"{stem}.txt")
    with open(vtt, "w", encoding="utf-8") as vf, open(txt, "w", encoding="utf-8") as tf:
        vf.write("WEBVTT\n\n")
        n = 0
        for s in segs:
            n += 1
            ts = f"{_t(s.start)} --> {_t(s.end)}"
            vf.write(f"{ts}\n{s.text.strip()}\n\n")
            tf.write(f"[{_t(s.start)}] {s.text.strip()}\n")
    print(f"[fw] done {n} segs -> {vtt}", flush=True)


def _t(sec):
    sec = max(0, float(sec))
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ".")


if __name__ == "__main__":
    main()
