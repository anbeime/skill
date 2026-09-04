#!/usr/bin/env bash
# Run every geometry gate against a live model and write a baseline you can diff against later.
#
# The point of a baseline is that "before and after" becomes a number instead of an impression. Run
# this once before touching a model, run it again after, and diff the JSON: 49 -> 0 vertices inside
# the skull is an argument; "it looks better" is not.
#
# Usage:
#   scripts/character_audit.sh <page-url> <output-dir> [mesh-name-regex] [--allow a,b]...
#
# Anything after the regex is forwarded to the penetration gate, which is where `--allow` belongs:
# parts that SHOULD share space (an ear root embedded in a skull, a rim wrapping the shell it binds,
# a hand gripping a staff) are contact, not defects, and a gate without an exemption list flags them
# forever until someone switches it off.
#
# Example:
#   scripts/character_audit.sh \
#     'http://localhost:5175/img2threejs-showcase/zbrush-mouse-warrior.html?view=front&clean=1' \
#     baseline/ '' --allow ear-l-paper-thin-shell,craniofacial-unified-shell
set -uo pipefail

URL="${1:-}"
OUT="${2:-baseline}"
FILTER="${3:-}"
shift 3 2>/dev/null || shift $#
PENETRATION_ARGS=("$@")
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -z "$URL" ]; then
  echo "usage: $0 <page-url> <output-dir> [mesh-name-regex]" >&2
  exit 2
fi

mkdir -p "$OUT"
MESHES="$OUT/meshes.json"

echo "== exporting meshes =="
if [ -n "$FILTER" ]; then
  node "$ROOT/runtime/scripts/export_mesh_geometry.mjs" --url "$URL" --out "$MESHES" --include "$FILTER" || exit 2
else
  node "$ROOT/runtime/scripts/export_mesh_geometry.mjs" --url "$URL" --out "$MESHES" || exit 2
fi

# Every gate's exit code is captured rather than allowed to abort the run. A failing gate is the
# expected outcome on a model with defects, and stopping at the first one would hide the rest --
# which is the opposite of what an audit is for.
declare -A STATUS

run_gate() {
  local name="$1"; shift
  echo
  echo "== $name =="
  "$@" --json > "$OUT/$name.json" 2> "$OUT/$name.err"
  STATUS[$name]=$?
  # Human-readable copy alongside the JSON, since the JSON is for diffing and this is for reading.
  "$@" > "$OUT/$name.txt" 2>/dev/null
  head -20 "$OUT/$name.txt" 2>/dev/null || cat "$OUT/$name.err"
}

run_gate self-intersection python3 "$ROOT/forge/stage4_review/self_intersection.py" "$MESHES"
run_gate penetration       python3 "$ROOT/forge/stage4_review/pairwise_penetration.py" "$MESHES" "${PENETRATION_ARGS[@]+"${PENETRATION_ARGS[@]}"}"
run_gate uv                python3 "$ROOT/forge/stage3_build/uv_unwrap.py" "$MESHES"

echo
echo "== summary =="
FAILED=0
for name in "${!STATUS[@]}"; do
  code="${STATUS[$name]}"
  case "$code" in
    0) verdict="clean" ;;
    1) verdict="GATE FAILURE"; FAILED=1 ;;
    *) verdict="ERROR (could not run)"; FAILED=1 ;;
  esac
  printf '  %-20s %s\n' "$name" "$verdict"
done
echo
echo "baseline written to $OUT/ -- diff these JSON files after your next change"
echo "read sampledVertexCount and skippedMeshes before trusting any clean verdict:"
echo "a zero because the defect is gone and a zero because the check never ran look identical."
exit $FAILED
