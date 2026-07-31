import json, os

REPO = r"C:\D\skill\skillhub-collection\installed-skills"
JSON_PATH = os.path.join(REPO, "installed-skills.json")

FULL = [
    "aihot","auto-trading","cloudbase","deck-generator","douyin-video-download",
    "earnings-tracker","mcp-builder","multi-search-engine","remotion-animator",
    "skill_2053082904354750464","stock-analysis-team","stock-analysis",
    "video-frames","wechat-miniprogram","wechatpay-basic-payment",
]

BINARY_EXT = {".png",".jpg",".jpeg",".gif",".ico",".bmp",".tiff",
              ".ttf",".otf",".woff",".woff2",".eot",".mp4",".mp3",
              ".zip",".pdf",".exe",".dll",".so",".bin"}

def rel(p, base):
    return os.path.relpath(p, base).replace(os.sep, "/")

data = json.load(open(JSON_PATH, encoding="utf-8"))
skills = data["skills"]
by_dir = {s["dir"]: s for s in skills}

for d in FULL:
    base = os.path.join(REPO, d)
    if not os.path.isdir(base):
        print("MISSING:", d); continue
    files = []
    scripts, references, others, binary = [], [], [], 0
    for root, dirs, fnames in os.walk(base):
        # skip hidden meta files from counts but keep them listed as others
        for f in fnames:
            fp = os.path.join(root, f)
            r = rel(fp, base)
            files.append(r)
            ext = os.path.splitext(f)[1].lower()
            low = f.lower()
            if ext in BINARY_EXT:
                binary += 1
            if r.lower().startswith("scripts/"):
                scripts.append(r)
            elif r.lower().startswith("references/") or r.lower().startswith("reference/"):
                references.append(r)
    # others = top-level non-SKILL.md resource files + nested non script/ref
    others = [r for r in files if r not in scripts and r not in references
              and r != "SKILL.md" and not r.lower().startswith("scripts/")
              and not r.lower().startswith("references/") and not r.lower().startswith("reference/")]
    s = by_dir[d]
    s["full_copy"] = True
    s["files_total"] = len(files)
    s["scripts"] = sorted(scripts)
    s["references"] = sorted(references)
    s["other_resources"] = sorted(others)
    s["binary_assets"] = binary
    print(f"{d}: {len(files)} files, {len(scripts)} scripts, {len(references)} refs, {binary} binary")

json.dump(data, open(JSON_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("WROTE", JSON_PATH)
