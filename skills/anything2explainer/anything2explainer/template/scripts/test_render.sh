#!/bin/zsh
# 30 帧测渲测 fps：test_render.sh <Comp> <起始帧 1 起> [tag]   正常 30 帧 3–12 s；<3 fps 要查滤镜/DOM
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
COMP=$1; A=$2; TAG=${3:-$COMP}; B=build_dev_$TAG
[ -n "$COMP" ] && [ -n "$A" ] || { echo "usage: test_render.sh <Comp> <start_frame> [tag]"; exit 1; }
[ -d "$B" ] || npx remotion bundle src/index.ts --out-dir "$B" --log=error
OUT=$(mktemp -d "${TMPDIR:-/tmp}/explainer_test_${TAG}_XXXXXX")   # 模板里不能带点：Remotion 会把 .XXXXXX 当成图片序列的扩展名而拒渲
trap 'rm -rf "$OUT"' EXIT
time npx remotion render "$B" "$COMP" "$OUT" --sequence --image-format=jpeg --frames=$((A-1))-$((A+28)) --log=error
ls "$OUT" | wc -l
