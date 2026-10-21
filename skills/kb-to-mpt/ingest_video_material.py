# -*- coding: utf-8 -*-
"""
ingest_video_material.py — 把 yt-dlp 下载技能的产物(字幕.vtt/.srt / 元数据.json)入库为 Antinet 蓝卡。

链路： dl.py subs/info 下载文本 → 本脚本 → 密卷房式归一化 → 通政司蓝卡(project 66 外贸作战室)
适用：YouTube/TikTok/有字幕的B站视频直接 subs 入库；无字幕视频先本地 whisper-large-v3 转写再喂本脚本。

用法：
  python ingest_video_material.py <path> --url "<视频URL>" [--project-id 66]
  path 可为 .vtt/.srt/.json 单文件，或含这些文件的目录。
"""
import sqlite3, json, os, sys, time, re, argparse

DB = 'backend/data/antinet.db'
CHUNK = 700  # 单卡字数上限

def vtt_to_text(path):
    """解析 vtt/srt 为 [(ts, text), ...]，去时间戳与空行。"""
    raw = open(path, encoding='utf-8', errors='ignore').read()
    # 去掉 WEBVTT 头
    raw = re.sub(r'^WEBVTT.*?(\n\n|\Z)', '', raw, flags=re.S)
    blocks = re.split(r'\n\s*\n', raw)
    out = []
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        if not lines:
            continue
        # 跳过纯时间戳行 / cue 编号
        txt = []
        for l in lines:
            if re.match(r'^\d{2}:\d{2}[:.]\d{2}', l) or re.match(r'^\d+$', l) or '-->' in l:
                continue
            txt.append(l.strip())
        if txt:
            # 取首行的时间戳(若有)做标注
            ts = ''
            for l in lines:
                m = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)', l)
                if m:
                    ts = m.group(1); break
            out.append((ts, ' '.join(txt)))
    return out

def info_to_cards(path):
    d = json.load(open(path, encoding='utf-8'))
    title = d.get('title', '')
    desc = d.get('description', '')
    dur = d.get('duration')
    chap = d.get('chapters') or []
    meta = f"标题：{title}\n时长：{dur}s\n简介：{desc}\n"
    if chap:
        meta += "章节：\n" + "\n".join(f"  {c.get('start_time')}s {c.get('title','')}" for c in chap)
    return [(title or '视频元数据', meta, '视频元数据/选题')]

def chunk_text(text, label, src):
    """把长文本切成 ≤CHUNK 的卡。"""
    segs = []
    buf = ''
    for line in text.split('\n'):
        if len(buf) + len(line) + 1 <= CHUNK:
            buf += line + '\n'
        else:
            if buf.strip():
                segs.append(buf.strip())
            buf = line + '\n'
    if buf.strip():
        segs.append(buf.strip())
    return [(f"{label} · 片段{i+1}/{len(segs)}", s, src) for i, s in enumerate(segs)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--url', default='')
    ap.add_argument('--project-id', type=int, default=66)
    ap.add_argument('--category', default='外贸')
    a = ap.parse_args()

    now = int(time.time())
    c = sqlite3.connect(DB); cur = c.cursor()

    # 收集待入库 (title, content, tag)
    items = []
    if os.path.isdir(a.path):
        for fn in sorted(os.listdir(a.path)):
            fp = os.path.join(a.path, fn)
            if fn.endswith(('.vtt', '.srt')):
                items += [(f"{os.path.splitext(fn)[0]} 字幕", t, '视频字幕') for _, t in vtt_to_text(fp)]
            elif fn.endswith('.json'):
                items += info_to_cards(fp)
    else:
        if a.path.endswith(('.vtt', '.srt')):
            items += [(f"{os.path.splitext(os.path.basename(a.path))[0]} 字幕", t, '视频字幕') for _, t in vtt_to_text(a.path)]
        elif a.path.endswith('.json'):
            items += info_to_cards(a.path)
        else:
            print("不支持的文件类型:", a.path); sys.exit(1)

    # 字幕长文本切片
    final = []
    for title, content, tag in items:
        if tag == '视频字幕' and len(content) > CHUNK:
            final += chunk_text(content, title, tag)
        else:
            final.append((title, content, tag))

    n_new = 0; n_skip = 0
    for title, content, tag in final:
        # 去重：同 project 同内容已存在则跳过
        ex = cur.execute("SELECT id FROM knowledge_cards WHERE project_id=? AND content=?", (a.project_id, content)).fetchone()
        if ex:
            n_skip += 1; continue
        cur.execute("""INSERT INTO knowledge_cards (title,content,card_type,type,category,created_at,updated_at,project_id,tags,source_url)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, content, 'blue', 'blue', a.category, now, now, a.project_id,
             json.dumps([tag, '视频入库'], ensure_ascii=False), a.url))
        n_new += 1
    cur.execute("COMMIT")
    print(f"[ingest] 新增蓝卡 {n_new} 张, 跳过重复 {n_skip} 张 → project {a.project_id}")

if __name__ == '__main__':
    main()
