#!/bin/sh
# Self-check for the publish skip list and project-root guard.
# Runs publish.sh and publish-large.mjs in --dry-run and compares them.
set -eu

cd "$(dirname "$0")"
PUBLISH=./publish.sh
LARGE=./publish-large.mjs
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export DEEDPAGE_TOKEN=
export DEEDPAGE_TOKEN_FILE="$TMP/no-token"
export DEEDPAGE_URL="http://127.0.0.1:9"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

RESULT_EC=0
RESULT_OUT=$TMP/empty.out
RESULT_ERR=$TMP/empty.err
: > "$RESULT_OUT"
: > "$RESULT_ERR"

run_both() {
  label=$1
  dir=$2
  shift 2
  sh_out=$TMP/sh.out
  sh_err=$TMP/sh.err
  node_out=$TMP/node.out
  node_err=$TMP/node.err
  set +e
  sh "$PUBLISH" "$dir" --dry-run --base-url "$DEEDPAGE_URL" "$@" >"$sh_out" 2>"$sh_err"
  sh_ec=$?
  node "$LARGE" "$dir" --dry-run --base-url "$DEEDPAGE_URL" "$@" >"$node_out" 2>"$node_err"
  node_ec=$?
  set -e
  if [ "$sh_ec" != "$node_ec" ]; then
    echo "--- sh ($sh_ec) stdout ---" >&2
    cat "$sh_out" >&2
    echo "--- sh stderr ---" >&2
    cat "$sh_err" >&2
    echo "--- node ($node_ec) stdout ---" >&2
    cat "$node_out" >&2
    echo "--- node stderr ---" >&2
    cat "$node_err" >&2
    fail "$label: exit sh=$sh_ec node=$node_ec"
  fi
  if ! cmp -s "$sh_out" "$node_out"; then
    diff -u "$sh_out" "$node_out" >&2 || true
    fail "$label: stdout mismatch"
  fi
  if ! cmp -s "$sh_err" "$node_err"; then
    diff -u "$sh_err" "$node_err" >&2 || true
    fail "$label: stderr mismatch"
  fi
  RESULT_EC=$sh_ec
  cp "$sh_out" "$TMP/last.out"
  cp "$sh_err" "$TMP/last.err"
  RESULT_OUT=$TMP/last.out
  RESULT_ERR=$TMP/last.err
  echo "ok $label (exit $sh_ec)"
}

assert_exit() {
  if [ "$RESULT_EC" != "$1" ]; then
    echo "stdout:" >&2
    cat "$RESULT_OUT" >&2
    echo "stderr:" >&2
    cat "$RESULT_ERR" >&2
    fail "expected exit $1, got $RESULT_EC"
  fi
}

assert_stdout() {
  if ! cmp -s "$1" "$RESULT_OUT"; then
    diff -u "$1" "$RESULT_OUT" >&2 || true
    fail "stdout did not match $1"
  fi
}

assert_stderr() {
  if ! cmp -s "$1" "$RESULT_ERR"; then
    diff -u "$1" "$RESULT_ERR" >&2 || true
    fail "stderr did not match $1"
  fi
}

write_lines() {
  dest=$1
  shift
  : > "$dest"
  for line in "$@"; do
    printf '%s\n' "$line" >> "$dest"
  done
  LC_ALL=C sort -o "$dest" "$dest"
}

join_skip() {
  src=$1
  dest=$2
  if [ ! -s "$src" ]; then
    printf '%s\n' "skipped 0" > "$dest"
    return
  fi
  _n=$(wc -l < "$src" | tr -d '[:space:]')
  _items=""
  while IFS= read -r _line; do
    if [ -z "$_items" ]; then
      _items=$_line
    else
      _items="$_items, $_line"
    fi
  done < "$src"
  printf 'skipped %s: %s\n' "$_n" "$_items" > "$dest"
}

# --- output folder: every denied name is skipped, safe files stay ---
OUT=$TMP/output
mkdir -p "$OUT/.github/workflows" "$OUT/.ssh" "$OUT/node_modules/pkg" \
  "$OUT/.well-known" "$OUT/nested/.git" "$OUT/sub" "$OUT/keep"
printf 'x\n' > "$OUT/.github/workflows/ci.yml"
printf 'x\n' > "$OUT/.ssh/id_rsa"
printf 'x\n' > "$OUT/.ssh/config"
printf 'x\n' > "$OUT/node_modules/pkg/index.js"
printf 'x\n' > "$OUT/nested/.git/config"
printf 'x\n' > "$OUT/.env"
printf 'x\n' > "$OUT/.env.local"
printf 'x\n' > "$OUT/.npmrc"
printf 'x\n' > "$OUT/.netrc"
printf 'x\n' > "$OUT/.DS_Store"
printf 'x\n' > "$OUT/.gitignore"
printf 'x\n' > "$OUT/credentials.json"
printf 'x\n' > "$OUT/secrets.json"
printf 'x\n' > "$OUT/secrets.yaml"
printf 'x\n' > "$OUT/nested/secrets.yaml"
printf 'x\n' > "$OUT/id_rsa"
printf 'x\n' > "$OUT/id_rsa.pub"
printf 'x\n' > "$OUT/cert.pem"
printf 'x\n' > "$OUT/server.key"
printf 'x\n' > "$OUT/sub/id_rsa"
printf 'x\n' > "$OUT/.well-known/.env"
printf 'ok\n' > "$OUT/.well-known/security.txt"
printf 'ok\n' > "$OUT/index.html"
printf 'ok\n' > "$OUT/keep/app.js"
printf 'ok\n' > "$OUT/keyboard.txt"
printf 'x\n' > "$OUT/secrets.bak"
printf 'ok\n' > "$OUT/notes.txt"
printf 'ok\n' > "$OUT/not_id_rsa.txt"
ln -s index.html "$OUT/extra-link"

write_lines "$TMP/expect-files" \
  ".well-known/security.txt" \
  "index.html" \
  "keep/app.js" \
  "keyboard.txt" \
  "notes.txt" \
  "not_id_rsa.txt"
write_lines "$TMP/expect-skip-names" \
  ".DS_Store" \
  ".env" \
  ".env.local" \
  ".github/" \
  ".gitignore" \
  ".netrc" \
  ".npmrc" \
  ".ssh/" \
  ".well-known/.env" \
  "cert.pem" \
  "credentials.json" \
  "extra-link" \
  "id_rsa" \
  "id_rsa.pub" \
  "nested/.git/" \
  "nested/secrets.yaml" \
  "node_modules/" \
  "secrets.bak" \
  "secrets.json" \
  "secrets.yaml" \
  "server.key" \
  "sub/id_rsa"
join_skip "$TMP/expect-skip-names" "$TMP/expect-skip"

run_both "output folder exclusions" "$OUT"
assert_exit 0
assert_stdout "$TMP/expect-files"
assert_stderr "$TMP/expect-skip"

run_both "allow-root is a no-op on an output folder" "$OUT" --allow-root
assert_exit 0
assert_stdout "$TMP/expect-files"
assert_stderr "$TMP/expect-skip"

# --- secrets only: nothing left to publish ---
ONLY=$TMP/only-secrets
mkdir -p "$ONLY"
printf 'x\n' > "$ONLY/.env"
printf 'x\n' > "$ONLY/credentials.json"
printf 'x\n' > "$ONLY/secrets.json"
write_lines "$TMP/only-names" ".env" "credentials.json" "secrets.json"
join_skip "$TMP/only-names" "$TMP/only-err"
printf '%s\n' "nothing to publish after exclusions" >> "$TMP/only-err"
run_both "secrets only" "$ONLY"
assert_exit 1
assert_stderr "$TMP/only-err"

# --- project root via .git, no build folder ---
GITROOT=$TMP/git-root
mkdir -p "$GITROOT/.git" "$GITROOT"
printf 'ref: refs/heads/main\n' > "$GITROOT/.git/HEAD"
printf 'ok\n' > "$GITROOT/index.html"
printf 'x\n' > "$GITROOT/.env"
printf '%s\n' \
  "refusing to publish $GITROOT: it looks like a project root (it has .git), not an output folder." \
  "No dist, build, out, public, or _site directory was found." \
  "Pass --allow-root to publish this folder anyway. Sensitive files are still excluded." \
  > "$TMP/git-refuse"
run_both "git root refused" "$GITROOT"
assert_exit 2
assert_stderr "$TMP/git-refuse"

write_lines "$TMP/git-files" "index.html"
write_lines "$TMP/git-skip-names" ".env" ".git/"
join_skip "$TMP/git-skip-names" "$TMP/git-allow"
{
  printf '%s\n' "$GITROOT looks like a project root (it has .git). Publishing it because --allow-root was set."
  cat "$TMP/git-allow"
} > "$TMP/git-allow-err"
run_both "git root allow-root" "$GITROOT" --allow-root
assert_exit 0
assert_stdout "$TMP/git-files"
assert_stderr "$TMP/git-allow-err"

# .git as a file (worktree gitdir) is still a project root
GITFILE=$TMP/git-file
mkdir -p "$GITFILE"
printf 'gitdir: /tmp/example.git\n' > "$GITFILE/.git"
printf 'ok\n' > "$GITFILE/index.html"
printf '%s\n' \
  "refusing to publish $GITFILE: it looks like a project root (it has .git), not an output folder." \
  "No dist, build, out, public, or _site directory was found." \
  "Pass --allow-root to publish this folder anyway. Sensitive files are still excluded." \
  > "$TMP/gitfile-refuse"
run_both "gitdir file refused" "$GITFILE"
assert_exit 2
assert_stderr "$TMP/gitfile-refuse"

# --- package.json + src prefers dist over build, public, and _site ---
APP=$TMP/app
mkdir -p "$APP/src" "$APP/dist/.well-known" "$APP/build" "$APP/public" "$APP/_site" "$APP/.git"
printf '{}\n' > "$APP/package.json"
printf 'x\n' > "$APP/src/main.js"
printf 'x\n' > "$APP/.git/HEAD"
printf 'x\n' > "$APP/.env"
printf 'ok\n' > "$APP/dist/index.html"
printf 'ok\n' > "$APP/dist/.well-known/security.txt"
printf 'x\n' > "$APP/dist/.env"
printf 'build\n' > "$APP/build/from-build.txt"
printf 'public\n' > "$APP/public/only-public.txt"
printf 'site\n' > "$APP/_site/index.html"
write_lines "$TMP/dist-files" ".well-known/security.txt" "index.html"
write_lines "$TMP/dist-skip-names" ".env"
join_skip "$TMP/dist-skip-names" "$TMP/dist-skip"
{
  printf '%s\n' "$APP looks like a project root (it has .git, and package.json with src/). Publishing $APP/dist instead."
  cat "$TMP/dist-skip"
} > "$TMP/dist-err"
run_both "project root prefers dist" "$APP"
assert_exit 0
assert_stdout "$TMP/dist-files"
assert_stderr "$TMP/dist-err"

# allow-root publishes the root, still skipping secrets, and includes the build folders
write_lines "$TMP/root-files" \
  "_site/index.html" \
  "build/from-build.txt" \
  "dist/.well-known/security.txt" \
  "dist/index.html" \
  "package.json" \
  "public/only-public.txt" \
  "src/main.js"
write_lines "$TMP/root-skip-names" ".env" ".git/" "dist/.env"
join_skip "$TMP/root-skip-names" "$TMP/root-skip"
{
  printf '%s\n' "$APP looks like a project root (it has .git, and package.json with src/). Publishing it because --allow-root was set."
  cat "$TMP/root-skip"
} > "$TMP/root-err"
run_both "allow-root publishes the root" "$APP" --allow-root
assert_exit 0
assert_stdout "$TMP/root-files"
assert_stderr "$TMP/root-err"

# package.json + src, no .git, no build folder
SRCROOT=$TMP/src-root
mkdir -p "$SRCROOT/src"
printf '{}\n' > "$SRCROOT/package.json"
printf 'x\n' > "$SRCROOT/src/main.js"
printf 'ok\n' > "$SRCROOT/index.html"
printf 'x\n' > "$SRCROOT/.env"
printf '%s\n' \
  "refusing to publish $SRCROOT: it looks like a project root (it has package.json and src/), not an output folder." \
  "No dist, build, out, public, or _site directory was found." \
  "Pass --allow-root to publish this folder anyway. Sensitive files are still excluded." \
  > "$TMP/src-refuse"
run_both "package.json and src refused" "$SRCROOT"
assert_exit 2
assert_stderr "$TMP/src-refuse"

write_lines "$TMP/src-files" "index.html" "package.json" "src/main.js"
write_lines "$TMP/src-skip-names" ".env"
join_skip "$TMP/src-skip-names" "$TMP/src-skip"
{
  printf '%s\n' "$SRCROOT looks like a project root (it has package.json and src/). Publishing it because --allow-root was set."
  cat "$TMP/src-skip"
} > "$TMP/src-err"
run_both "package.json and src allow-root" "$SRCROOT" --allow-root
assert_exit 0
assert_stdout "$TMP/src-files"
assert_stderr "$TMP/src-err"

# package.json without src/ is not a project root
PKG=$TMP/pkg-only
mkdir -p "$PKG/source"
printf '{}\n' > "$PKG/package.json"
printf 'x\n' > "$PKG/source/app.js"
printf 'ok\n' > "$PKG/index.html"
printf 'x\n' > "$PKG/readme.txt"
write_lines "$TMP/pkg-files" "index.html" "package.json" "readme.txt" "source/app.js"
printf '%s\n' "skipped 0" > "$TMP/pkg-err"
run_both "package.json without src is not a root" "$PKG"
assert_exit 0
assert_stdout "$TMP/pkg-files"
assert_stderr "$TMP/pkg-err"

# src/ without package.json is not a project root
SRCONLY=$TMP/src-only
mkdir -p "$SRCONLY/src"
printf 'x\n' > "$SRCONLY/src/main.js"
printf 'ok\n' > "$SRCONLY/index.html"
write_lines "$TMP/srconly-files" "index.html" "src/main.js"
printf '%s\n' "skipped 0" > "$TMP/srconly-err"
run_both "src without package.json is not a root" "$SRCONLY"
assert_exit 0
assert_stdout "$TMP/srconly-files"
assert_stderr "$TMP/srconly-err"

# public is used when it is the only build folder; a symlinked dist is ignored
PUB=$TMP/public-app
mkdir -p "$PUB/src" "$PUB/public" "$TMP/elsewhere"
printf '{}\n' > "$PUB/package.json"
printf 'x\n' > "$PUB/src/main.js"
printf 'ok\n' > "$PUB/public/only-public.txt"
printf 'x\n' > "$PUB/public/.env"
printf 'nope\n' > "$TMP/elsewhere/index.html"
ln -s "$TMP/elsewhere" "$PUB/dist"
write_lines "$TMP/pub-files" "only-public.txt"
write_lines "$TMP/pub-skip-names" ".env"
join_skip "$TMP/pub-skip-names" "$TMP/pub-skip"
{
  printf '%s\n' "$PUB looks like a project root (it has package.json and src/). Publishing $PUB/public instead."
  cat "$TMP/pub-skip"
} > "$TMP/pub-err"
run_both "symlink dist is not a build folder" "$PUB"
assert_exit 0
assert_stdout "$TMP/pub-files"
assert_stderr "$TMP/pub-err"

# only a symlinked dist: refuse
LINKONLY=$TMP/link-only
mkdir -p "$LINKONLY/src" "$TMP/elsewhere2"
printf '{}\n' > "$LINKONLY/package.json"
printf 'x\n' > "$LINKONLY/src/main.js"
printf 'ok\n' > "$TMP/elsewhere2/index.html"
ln -s "$TMP/elsewhere2" "$LINKONLY/dist"
printf '%s\n' \
  "refusing to publish $LINKONLY: it looks like a project root (it has package.json and src/), not an output folder." \
  "No dist, build, out, public, or _site directory was found." \
  "Pass --allow-root to publish this folder anyway. Sensitive files are still excluded." \
  > "$TMP/link-refuse"
run_both "only a symlinked build folder is refused" "$LINKONLY"
assert_exit 2
assert_stderr "$TMP/link-refuse"

# publishing the output folder directly does not redirect
DIRECT=$TMP/direct-dist
mkdir -p "$DIRECT"
printf 'ok\n' > "$DIRECT/index.html"
printf 'x\n' > "$DIRECT/.env.production"
write_lines "$TMP/direct-files" "index.html"
write_lines "$TMP/direct-skip-names" ".env.production"
join_skip "$TMP/direct-skip-names" "$TMP/direct-err"
run_both "direct output folder" "$DIRECT"
assert_exit 0
assert_stdout "$TMP/direct-files"
assert_stderr "$TMP/direct-err"

# single files
HTML=$TMP/report.html
printf '<h1>hi</h1>\n' > "$HTML"
printf '%s\n' "index.html" > "$TMP/html-out"
printf '%s\n' "skipped 0" > "$TMP/html-err"
run_both "html file becomes index.html" "$HTML"
assert_exit 0
assert_stdout "$TMP/html-out"
assert_stderr "$TMP/html-err"

TXT=$TMP/notes.txt
printf 'hi\n' > "$TXT"
printf '%s\n' "notes.txt" > "$TMP/txt-out"
run_both "plain file keeps its name" "$TXT"
assert_exit 0
assert_stdout "$TMP/txt-out"
assert_stderr "$TMP/html-err"

ENVF=$TMP/.env
printf 'TOKEN=1\n' > "$ENVF"
printf '%s\n' "refusing to publish .env: sensitive or repo-metadata file" > "$TMP/env-err"
run_both "refuse .env file" "$ENVF"
assert_exit 2
assert_stderr "$TMP/env-err"

CREDS=$TMP/credentials.json
printf '{}\n' > "$CREDS"
printf '%s\n' "refusing to publish credentials.json: sensitive or repo-metadata file" > "$TMP/creds-err"
run_both "refuse credentials.json file" "$CREDS"
assert_exit 2
assert_stderr "$TMP/creds-err"

KEY=$TMP/id_rsa
printf 'key\n' > "$KEY"
printf '%s\n' "refusing to publish id_rsa: sensitive or repo-metadata file" > "$TMP/key-err"
run_both "refuse id_rsa file" "$KEY"
assert_exit 2
assert_stderr "$TMP/key-err"

PEM=$TMP/cert.pem
printf 'pem\n' > "$PEM"
printf '%s\n' "refusing to publish cert.pem: sensitive or repo-metadata file" > "$TMP/pem-err"
run_both "refuse pem file" "$PEM"
assert_exit 2
assert_stderr "$TMP/pem-err"

NM=$TMP/node_modules
mkdir -p "$NM"
printf 'ok\n' > "$NM/index.html"
printf '%s\n' "refusing to publish node_modules: sensitive or repo-metadata path" > "$TMP/nm-err"
run_both "refuse node_modules directory" "$NM"
assert_exit 2
assert_stderr "$TMP/nm-err"

# help mentions the guard
sh "$PUBLISH" --help >"$TMP/sh-help" 2>&1
node "$LARGE" --help >"$TMP/node-help" 2>&1
grep -q -- '--allow-root' "$TMP/sh-help" || fail "publish.sh --help missing --allow-root"
grep -q -- '--dry-run' "$TMP/sh-help" || fail "publish.sh --help missing --dry-run"
grep -q -- '--allow-root' "$TMP/node-help" || fail "publish-large.mjs --help missing --allow-root"
grep -q -- '--dry-run' "$TMP/node-help" || fail "publish-large.mjs --help missing --dry-run"
echo "ok help text"

# Success JSON has more than one "url". The live site is the first one.
HTML=$TMP/url-pick.html
printf '<!doctype html><h1>hi</h1>\n' > "$HTML"
cat > "$TMP/url-server.js" << 'EOF'
const http = require("http");
const server = http.createServer((req, res) => {
  res.writeHead(200, { "content-type": "application/json" });
  res.end(
    '{"ok":true,"url":"https://example.deed.page/","visit_analytics":{"url":"https://deed.page/analytics?slug=example"},"token":"deed_tok_testtokenvalue"}',
  );
});
server.listen(0, "127.0.0.1", () => {
  console.log(server.address().port);
});
EOF
node "$TMP/url-server.js" >"$TMP/url-port" &
URL_PID=$!
i=0
while [ ! -s "$TMP/url-port" ]; do
  i=$((i + 1))
  if [ "$i" -gt 50 ]; then
    kill "$URL_PID" 2>/dev/null || true
    fail "url mock server did not start"
  fi
  sleep 0.05
done
URL_PORT=$(tr -d ' \r\n' < "$TMP/url-port")
sh "$PUBLISH" "$HTML" --slug url-pick --base-url "http://127.0.0.1:$URL_PORT" >"$TMP/url-out" 2>"$TMP/url-err" || fail "publish against url mock failed"
kill "$URL_PID" 2>/dev/null || true
wait "$URL_PID" 2>/dev/null || true
URL_GOT=$(tr -d ' \r\n' < "$TMP/url-out")
if [ "$URL_GOT" != "https://example.deed.page/" ]; then
  echo "stdout: $URL_GOT" >&2
  cat "$TMP/url-err" >&2
  fail "publish.sh printed $URL_GOT, want the site url"
fi
if grep -q 'deed_tok_testtokenvalue' "$TMP/url-err"; then
  fail "publish.sh printed the owner token"
fi
echo "ok first url field is the live site"

echo "all checks passed"
