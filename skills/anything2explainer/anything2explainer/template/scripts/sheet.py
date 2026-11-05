#!/usr/bin/env python3
"""把 fin_frames/f_%04d.jpg 每 step 帧抽一张，生成缩略图网格 HTML（QC 通读用）。用法：sheet.py <frames_dir> <out.html> [step=60] [cols=6]"""
import sys, os, glob, json, html
d, out = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 60
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
files = sorted(glob.glob(os.path.join(d, 'f_*.jpg')))
rel = os.path.relpath(d, os.path.dirname(os.path.abspath(out)))
tl = None
tlp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'script', 'timeline.json')
if os.path.exists(tlp):
    tl = json.load(open(tlp))
def sent_at(n):
    if not tl: return ''
    for s in tl['sentences']:
        # 解说词可能来自用户给的文章/调研摘录，转义后再进 HTML
        if s['from'] <= n <= s['to']: return html.escape(f"{s['id']} {s['text'][:18]}")
    return ''
cells = []
for i in range(0, len(files), step):
    n = i + 1
    cells.append(f'<div class="c"><img loading="lazy" src="{rel}/{os.path.basename(files[i])}"><div class="l">f{n} ({n/30:.1f}s) <span>{sent_at(n)}</span></div></div>')
html = f'''<!doctype html><meta charset="utf-8"><title>sheet</title>
<style>body{{background:#111;color:#ddd;font:12px/1.4 -apple-system,sans-serif;margin:8px}} .g{{display:grid;grid-template-columns:repeat({cols},1fr);gap:6px}} .c img{{width:100%;display:block}} .l{{padding:2px 0 6px}} .l span{{color:#9a8}}</style>
<h3>成片缩略图 · 每 {step} 帧一张 · 共 {len(files)} 帧</h3><div class="g">{''.join(cells)}</div>'''
open(out, 'w').write(html)
print('sheet', out, len(cells), 'cells')
