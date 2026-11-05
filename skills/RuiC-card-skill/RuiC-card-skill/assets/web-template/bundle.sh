#!/usr/bin/env bash
# Rebuild app.bundle.js after editing app.js / icons.data.js.
# The page must be served as a SINGLE js file: per-module URLs under
# node_modules/ (e.g. .../fingerprint.js) are blocked by ad blockers.
#
# bun is the original tool; esbuild produces an equivalent self-contained ESM
# bundle when bun is not installed. Either way the bundle inlines three.js and
# icons.data.js, so the served page needs no node_modules/ at runtime.
cd "$(dirname "$0")"
BUN_BIN="${BUN:-$(command -v bun || echo "$HOME/.bun/bin/bun")}"
if [ -x "$BUN_BIN" ]; then
  "$BUN_BIN" build ./app.js --outfile=./app.bundle.js --target=browser
else
  # esbuild resolves "three" from node_modules: npm install --ignore-scripts first.
  npx --no-install esbuild app.js --bundle --format=esm --target=es2020 --outfile=app.bundle.js
fi
