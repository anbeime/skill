#!/bin/zsh
# 前 N 秒样片（确认点 3：先给用户看风格，别等整片渲完）：preview.sh [秒数=30] [起始秒=0]
#   → renders/<slug>_preview_<a>-<b>s.mp4（含配音/字幕/进度条；还没建的组是空画面，正常）
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
SEC=${1:-30}; FROM=${2:-0}
SLUG=$(python3 -c "import re;print(re.search(r\"slug:\\s*'([^']+)'\", open('src/config.ts').read()).group(1))")
TOTAL=$(python3 -c "import re;print(re.search(r'TOTAL_FRAMES\s*=\s*(\d+)', open('src/common/timeline.ts').read()).group(1))")
A=$((FROM * 30)); B=$((A + SEC * 30 - 1))
[ $B -gt $((TOTAL - 1)) ] && B=$((TOTAL - 1))
mkdir -p renders
OUTF="renders/${SLUG}_preview_${FROM}-$((FROM + SEC))s.mp4"
[ "${SKIP_BUNDLE:-0}" = 1 ] && [ -d build_prev ] || { rm -rf build_prev && npx remotion bundle src/index.ts --out-dir build_prev --log=error; }
npx remotion render build_prev Video "$OUTF" --codec=h264 --crf=18 --frames=$A-$B --concurrency=${CONC:-6} --timeout=${RTIMEOUT:-300000} --log=error
[ -s "$OUTF" ] || { echo "PREVIEW FAILED"; exit 1; }
[ "${KEEP_BUNDLE:-0}" = 1 ] || rm -rf build_prev
echo "$OUTF"
