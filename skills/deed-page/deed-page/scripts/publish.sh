#!/bin/sh
# deed.page publish — POSIX sh, plus `local` (dash, bash, busybox). No GNU seq.
# Token: $DEEDPAGE_TOKEN, else ~/.config/deed-page/token (override with
# $DEEDPAGE_TOKEN_FILE). A newly minted token is saved there (mode 600) so the
# next publish, in this session or a later one, stays under the same owner.
# The token is never printed.
#
# Only a clean output folder is uploaded. Sensitive and repo-metadata paths are
# skipped (see name_excluded; keep in sync with publish-large.mjs). A project
# root (package.json together with src/, or .git) publishes dist, build, out,
# public, or _site when one exists; otherwise it stops unless --allow-root.
set -eu

usage() {
  cat <<'EOF'
publish.sh {file-or-dir} [--slug SLUG] [--client NAME] [--ref REF] [--ttl SECONDS] [--spa] [--base-url URL] [--allow-root] [--dry-run]

Uses $DEEDPAGE_TOKEN, else the token file ~/.config/deed-page/token.
Saves a newly minted token to that file (mode 600). Sends X-Client
(default $DEEDPAGE_CLIENT or deed-page-skill) and ref (default skill-script).
Prints the live URL on the last line of stdout.
Skips sensitive and repo-metadata paths and prints a short summary.
A project root (package.json with src/, or .git) publishes dist, build, out,
public, or _site when one of those directories exists. Pass --allow-root to
publish that root anyway. --dry-run prints the file list and does not upload.
An archive over ${DEEDPAGE_SPLIT_BYTES:-4000000} bytes (about 4 MB), or a
non-JSON 413 from /v1/sites, is published with publish-large.mjs instead.
EOF
}

# True (0) when this path component must not be uploaded.
# .well-known is the only dotfile that is kept. "." and ".." are not names we skip.
name_excluded() {
  case "$1" in
    .|..)
      return 1
      ;;
    .well-known)
      return 1
      ;;
    .env|.env.*)
      return 0
      ;;
    .git|.github|.ssh|node_modules)
      return 0
      ;;
    .npmrc|.netrc|.DS_Store)
      return 0
      ;;
    credentials.json|secrets.*|id_rsa*|*.pem|*.key)
      return 0
      ;;
    .*)
      return 0
      ;;
  esac
  return 1
}

root_reason() {
  _has_git=0
  _has_pkg=0
  if [ -L "$1/.git" ] || [ -e "$1/.git" ]; then
    _has_git=1
  fi
  if [ -f "$1/package.json" ] && [ -d "$1/src" ]; then
    _has_pkg=1
  fi
  if [ "$_has_git" -eq 0 ] && [ "$_has_pkg" -eq 0 ]; then
    ROOT_REASON=""
    return 1
  fi
  if [ "$_has_git" -eq 1 ] && [ "$_has_pkg" -eq 1 ]; then
    ROOT_REASON="it has .git, and package.json with src/"
  elif [ "$_has_git" -eq 1 ]; then
    ROOT_REASON="it has .git"
  else
    ROOT_REASON="it has package.json and src/"
  fi
  return 0
}

pick_build() {
  _root=${1%/}
  for _b in dist build out public _site; do
    if [ -d "$_root/$_b" ] && [ ! -L "$_root/$_b" ]; then
      printf '%s/%s\n' "$_root" "$_b"
      return 0
    fi
  done
  return 1
}

stage_tree() {
  local src="$1" dst="$2" rel="$3" entry name child list
  STAGE_SEQ=$((STAGE_SEQ + 1))
  list="$WORKDIR/list.$STAGE_SEQ"
  find "$src" -mindepth 1 -maxdepth 1 -print | LC_ALL=C sort > "$list"
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    name=${entry##*/}
    if [ -n "$rel" ]; then
      child="$rel/$name"
    else
      child=$name
    fi
    if name_excluded "$name"; then
      if [ -d "$entry" ] && [ ! -L "$entry" ]; then
        printf '%s\n' "$child/" >> "$SKIPFILE"
      else
        printf '%s\n' "$child" >> "$SKIPFILE"
      fi
      continue
    fi
    if [ -L "$entry" ]; then
      printf '%s\n' "$child" >> "$SKIPFILE"
      continue
    fi
    if [ -d "$entry" ]; then
      mkdir -p "$dst/$name"
      stage_tree "$entry" "$dst/$name" "$child"
      continue
    fi
    if [ -f "$entry" ]; then
      cp "$entry" "$dst/$name"
    fi
  done < "$list"
  rm -f "$list"
}

print_skipped() {
  if [ ! -s "$SKIPFILE" ]; then
    echo "skipped 0" >&2
    return
  fi
  LC_ALL=C sort -u "$SKIPFILE" -o "$SKIPFILE"
  _n=$(wc -l < "$SKIPFILE" | tr -d '[:space:]')
  _items=""
  while IFS= read -r _line; do
    if [ -z "$_items" ]; then
      _items=$_line
    else
      _items="$_items, $_line"
    fi
  done < "$SKIPFILE"
  echo "skipped $_n: $_items" >&2
}

list_staged() {
  (cd "$STAGE" && find . -type f -print | sed 's|^\./||' | LC_ALL=C sort)
}

BASE_URL="${DEEDPAGE_URL:-https://deed.page}"
SLUG=""
CLIENT="${DEEDPAGE_CLIENT:-deed-page-skill}"
REF="skill-script"
TOKEN_FILE="${DEEDPAGE_TOKEN_FILE:-${HOME:-.}/.config/deed-page/token}"
TTL=""
SPA=0
ALLOW_ROOT=0
DRY_RUN=0
PATH_ARG=""
ROOT_REASON=""
STAGE_SEQ=0

while [ $# -gt 0 ]; do
  case "$1" in
    --slug)
      SLUG="${2:-}"
      shift 2
      ;;
    --client)
      CLIENT="${2:-}"
      shift 2
      ;;
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    --ttl)
      TTL="${2:-}"
      shift 2
      ;;
    --spa)
      SPA=1
      shift
      ;;
    --base-url)
      BASE_URL="${2:-}"
      shift 2
      ;;
    --allow-root)
      ALLOW_ROOT=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -n "$PATH_ARG" ]; then
        echo "unexpected argument: $1" >&2
        exit 2
      fi
      PATH_ARG="$1"
      shift
      ;;
  esac
done

if [ -z "$PATH_ARG" ]; then
  echo "usage: publish.sh {file-or-dir}" >&2
  exit 2
fi

if [ ! -e "$PATH_ARG" ]; then
  echo "not found: $PATH_ARG" >&2
  exit 2
fi

TMPDIR="${TMPDIR:-/tmp}"
STAMP=$$
i=0
while [ -e "$TMPDIR/deedpage-$STAMP-$i.tar.gz" ]; do
  i=$((i + 1))
done
ARCHIVE="$TMPDIR/deedpage-$STAMP-$i.tar.gz"
WORKDIR="$TMPDIR/deedpage-$STAMP-$i.work"
SKIPFILE="$WORKDIR/skipped"
STAGE="$WORKDIR/stage"

cleanup() {
  rm -f "$ARCHIVE" "$TMPDIR/deedpage-$STAMP-$i.body"
  rm -rf "$WORKDIR"
}
trap cleanup EXIT INT HUP TERM

mkdir -p "$WORKDIR"
: > "$SKIPFILE"

PUBLISH_PATH=${PATH_ARG%/}

if [ -d "$PUBLISH_PATH" ]; then
  _base=$(basename -- "$PUBLISH_PATH")
  if name_excluded "$_base"; then
    echo "refusing to publish $_base: sensitive or repo-metadata path" >&2
    exit 2
  fi
  if root_reason "$PUBLISH_PATH"; then
    _build=$(pick_build "$PUBLISH_PATH" || true)
    if [ -n "$_build" ] && [ "$ALLOW_ROOT" -eq 0 ]; then
      echo "$PUBLISH_PATH looks like a project root ($ROOT_REASON). Publishing $_build instead." >&2
      PUBLISH_PATH=$_build
    elif [ -z "$_build" ] && [ "$ALLOW_ROOT" -eq 0 ]; then
      echo "refusing to publish $PUBLISH_PATH: it looks like a project root ($ROOT_REASON), not an output folder." >&2
      echo "No dist, build, out, public, or _site directory was found." >&2
      echo "Pass --allow-root to publish this folder anyway. Sensitive files are still excluded." >&2
      exit 2
    else
      echo "$PUBLISH_PATH looks like a project root ($ROOT_REASON). Publishing it because --allow-root was set." >&2
    fi
  fi
fi

if [ -d "$PUBLISH_PATH" ]; then
  mkdir -p "$STAGE"
  stage_tree "$PUBLISH_PATH" "$STAGE" ""
  print_skipped
  if [ -z "$(find "$STAGE" -type f -print)" ]; then
    echo "nothing to publish after exclusions" >&2
    exit 1
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    list_staged
    exit 0
  fi
  tar -C "$STAGE" -czf "$ARCHIVE" .
elif [ -f "$PUBLISH_PATH" ]; then
  _base=$(basename -- "$PUBLISH_PATH")
  if name_excluded "$_base"; then
    echo "refusing to publish $_base: sensitive or repo-metadata file" >&2
    exit 2
  fi
  echo "skipped 0" >&2
  if [ "$DRY_RUN" -eq 1 ]; then
    case "$PUBLISH_PATH" in
      *.html|*.htm)
        printf '%s\n' "index.html"
        ;;
      *)
        printf '%s\n' "$_base"
        ;;
    esac
    exit 0
  fi
  case "$PUBLISH_PATH" in
    *.html|*.htm)
      mkdir -p "$STAGE"
      cp "$PUBLISH_PATH" "$STAGE/index.html"
      tar -C "$STAGE" -czf "$ARCHIVE" .
      ;;
    *)
      PARENT=$(dirname -- "$PUBLISH_PATH")
      BASE=$(basename -- "$PUBLISH_PATH")
      tar -C "$PARENT" -czf "$ARCHIVE" "$BASE"
      ;;
  esac
else
  echo "not a file or directory: $PATH_ARG" >&2
  exit 2
fi

BYTES=$(wc -c < "$ARCHIVE" | tr -d '[:space:]')
SPLIT_AT="${DEEDPAGE_SPLIT_BYTES:-4000000}"

use_large() {
  LARGE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/publish-large.mjs
  if ! command -v node >/dev/null 2>&1 || [ ! -f "$LARGE" ]; then
    echo "site is ${BYTES} bytes; over 4 MB needs Node 18+ and the bundled scripts/publish-large.mjs (it ships next to this script)" >&2
    exit 2
  fi
  set -- node "$LARGE" "$PUBLISH_PATH" --client "$CLIENT" --ref "$REF" --base-url "$BASE_URL"
  if [ -n "$SLUG" ]; then
    set -- "$@" --slug "$SLUG"
  fi
  if [ -n "$TTL" ]; then
    set -- "$@" --ttl "$TTL"
  fi
  if [ "$SPA" -eq 1 ]; then
    set -- "$@" --spa
  fi
  if [ "$ALLOW_ROOT" -eq 1 ]; then
    set -- "$@" --allow-root
  fi
  # exec replaces this shell, so the EXIT trap never runs: remove the archive now.
  cleanup
  trap - EXIT INT HUP TERM
  exec "$@"
  exit 2
}

if [ "$BYTES" -gt "$SPLIT_AT" ]; then
  use_large
fi

QUERY=""
if [ -n "$SLUG" ]; then
  QUERY="slug=$SLUG"
fi
if [ -n "$REF" ]; then
  QUERY="${QUERY:+$QUERY&}ref=$REF"
fi
ENDPOINT="$BASE_URL/v1/sites${QUERY:+?$QUERY}"

TOKEN_IN="${DEEDPAGE_TOKEN:-}"
if [ -z "$TOKEN_IN" ] && [ -f "$TOKEN_FILE" ]; then
  TOKEN_IN=$(tr -d ' \r\n' < "$TOKEN_FILE")
fi

set -- -sS -X PUT --data-binary @"$ARCHIVE" -H "Content-Type: application/gzip"
if [ -n "$TOKEN_IN" ]; then
  set -- "$@" -H "Authorization: Bearer ${TOKEN_IN}"
fi
if [ -n "$CLIENT" ]; then
  set -- "$@" -H "X-Client: $CLIENT"
fi
if [ -n "$TTL" ]; then
  set -- "$@" -H "X-Ttl: $TTL"
fi
if [ "$SPA" -eq 1 ]; then
  set -- "$@" -H "X-Spa: 1"
fi

echo "publishing $PUBLISH_PATH → $ENDPOINT" >&2

BODYFILE="$TMPDIR/deedpage-$STAMP-$i.body"
HTTP=$(curl -o "$BODYFILE" -w '%{http_code}' "$@" "$ENDPOINT" || printf '000')
RESP=$(cat "$BODYFILE" 2>/dev/null || true)
TRIM=$(printf '%s' "$RESP" | sed 's/^[[:space:]]*//')
case "$TRIM" in
  \{*|\[*) ;;
  *)
    if [ "$HTTP" = "413" ]; then
      use_large
    fi
    ;;
esac

# Echo the response without the token value.
printf '%s\n' "$RESP" | sed 's/"token":"[^"]*"/"token":"[saved]"/' >&2

TOKEN=$(printf '%s' "$RESP" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
if [ -n "$TOKEN" ]; then
  if [ -s "$TOKEN_FILE" ] && [ "$(tr -d ' \r\n' < "$TOKEN_FILE")" != "$TOKEN" ]; then
    SAVE_TO="$TOKEN_FILE.new"
  else
    SAVE_TO="$TOKEN_FILE"
  fi
  mkdir -p "$(dirname -- "$SAVE_TO")"
  (umask 077 && printf '%s\n' "$TOKEN" > "$SAVE_TO")
  chmod 600 "$SAVE_TO"
  if [ "$SAVE_TO" = "$TOKEN_FILE" ]; then
    echo "token minted and saved to $TOKEN_FILE (mode 600). Later publishes reuse it. It is not returned again." >&2
  else
    echo "token minted and saved to $SAVE_TO; $TOKEN_FILE already holds a different token and was left as is." >&2
  fi
fi

# First "url" is the live site. Later objects (analytics, visits) also have one,
# and a greedy match would print those instead.
LIVE=$(
  case $RESP in
    *'"url":"'*)
      _rest=${RESP#*'"url":"'}
      printf '%s\n' "${_rest%%\"*}"
      ;;
  esac
)
if [ -z "$LIVE" ]; then
  # Plan-limit errors carry one sentence for the user and a checkout link a human opens.
  MSG=$(printf '%s' "$RESP" | sed -n 's/.*"user_message":"\([^"]*\)".*/\1/p')
  if [ -n "$MSG" ]; then
    echo "$MSG" >&2
  fi
  echo "publish failed" >&2
  exit 1
fi

printf '%s\n' "$LIVE"
