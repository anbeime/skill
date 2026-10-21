#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SKILLS_DIR="$HOME/.qoder/skills"
TARGET_DIR="$SKILLS_DIR/email-concierge"
MARKER="$TARGET_DIR/state/.setup_completed.json"

FIRST_INSTALL=false
NO_SETUP=false
for arg in "$@"; do
  case "$arg" in
    --first-install) FIRST_INSTALL=true ;;
    --no-setup) NO_SETUP=true ;;
  esac
done

if [[ "$FIRST_INSTALL" == "false" && ! -f "$MARKER" ]]; then
  FIRST_INSTALL=true
fi

SETUP_FLAG="--setup"
if [[ "$NO_SETUP" == "true" ]]; then
  SETUP_FLAG="--no-setup"
fi

INSTALL_ARGS=(--target qoder --destination "$SKILLS_DIR" "$SETUP_FLAG" --json)
if [[ "$FIRST_INSTALL" == "true" ]]; then
  INSTALL_ARGS+=(--first-install)
fi

exec python3 "$SCRIPT_DIR/install_skill.py" "${INSTALL_ARGS[@]}"
