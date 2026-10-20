#!/usr/bin/env bash
# Installs the editing skills and the shared reel-kit into ~/.claude/skills (re-run after pulling changes).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; dst="$HOME/.claude/skills"; mkdir -p "$dst"
for d in "$here"/*/; do n="$(basename "$d")"; mkdir -p "$dst/$n"; cp "$d/SKILL.md" "$dst/$n/SKILL.md"; done
mkdir -p "$dst/reel-kit"; (cd "$here/../reel-kit" && tar cf - --exclude=.venv .) | (cd "$dst/reel-kit" && tar xf -)
[ -e "$dst/reel-kit/.venv" ] || { [ -x "$here/../.venv/bin/python" ] && ln -s "$here/../.venv" "$dst/reel-kit/.venv"; } || true
echo "installed $(ls -d "$here"/*/ | wc -l) skills + reel-kit -> $dst"
