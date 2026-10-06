---
name: install-video-plugins
description: Install or repair the HyperFrames (heygen-com/hyperframes) and ChatCut (ChatCut-Inc/agent-plugin) Claude Code plugins. Use when the user says "/install-video-plugins", asks to install/reinstall HyperFrames or ChatCut, or when a video-editing task needs those plugins and they are missing from `claude plugin list`.
---

# Install video plugins

These plugins are also installed automatically by the SessionStart hook in
`.claude/settings.json`. Use this skill to install them on demand or repair a
broken install.

1. Run the installer (idempotent, skips plugins already installed):
   ```bash
   "$CLAUDE_PROJECT_DIR"/.claude/hooks/install-video-plugins.sh
   ```
   If the script is not available (another repo), run the raw commands:
   ```bash
   claude plugin marketplace add heygen-com/hyperframes || true
   claude plugin install hyperframes@hyperframes || true
   claude plugin marketplace add https://github.com/ChatCut-Inc/agent-plugin.git || true
   claude plugin install chatcut@chatcut-inc || true
   ```
2. Verify: `claude plugin list` must show `hyperframes@hyperframes` and
   `chatcut@chatcut-inc` as enabled.
3. Tell the user that plugins installed mid-session load on the next session
   (or after `/reload-plugins` in an interactive CLI).

Known quirk: the hyperframes marketplace clone contains Git LFS pointer files.
If a HyperFrames asset is missing, run
`git -C ~/.claude/plugins/marketplaces/hyperframes lfs pull`.
