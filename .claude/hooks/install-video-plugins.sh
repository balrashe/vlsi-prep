#!/bin/bash
# Installs the HyperFrames and ChatCut Claude Code plugins.
# Idempotent and never fails the session: every step is `|| true`.
set -uo pipefail

command -v claude >/dev/null 2>&1 || { echo "claude CLI not found; skipping plugin install" >&2; exit 0; }

installed="$(claude plugin list 2>/dev/null || true)"

if ! grep -q 'hyperframes@hyperframes' <<<"$installed"; then
  claude plugin marketplace add heygen-com/hyperframes || true
  claude plugin install hyperframes@hyperframes || true
fi

if ! grep -q 'chatcut@chatcut-inc' <<<"$installed"; then
  claude plugin marketplace add https://github.com/ChatCut-Inc/agent-plugin.git || true
  claude plugin install chatcut@chatcut-inc || true
fi

exit 0
