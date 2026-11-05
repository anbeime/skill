#!/bin/zsh
# 整片渲染：VER=v1 scripts/render.sh  → renders/<slug>_v1.mp4 + fin_frames/ + renders/sheet_v1.html
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
V=${VER:-v1}
SLUG=$(python3 -c "import re;print(re.search(r\"slug:\\s*'([^']+)'\", open('src/config.ts').read()).group(1))")
mkdir -p renders
[ "${SKIP_BUNDLE:-0}" = 1 ] && [ -d build_full ] || { rm -rf build_full && npx remotion bundle src/index.ts --out-dir build_full --log=error; }
npx remotion render build_full Video "renders/${SLUG}_${V}.mp4" --codec=h264 --crf=16 --concurrency=${CONC:-6} --timeout=${RTIMEOUT:-300000} --log=error
[ -s "renders/${SLUG}_${V}.mp4" ] || { echo "RENDER FAILED"; exit 1; }
rm -rf fin_frames && mkdir -p fin_frames
ffmpeg -v error -y -i "renders/${SLUG}_${V}.mp4" -q:v 4 fin_frames/f_%04d.jpg
ls fin_frames | wc -l > fin_count.txt
python3 scripts/sheet.py fin_frames "renders/sheet_${V}.html" 60 || true
[ "${KEEP_BUNDLE:-0}" = 1 ] || rm -rf build_full
echo done > render.done
