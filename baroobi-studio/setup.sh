#!/usr/bin/env bash
# Rebuild the toolchain in a fresh container. Idempotent.
set -euo pipefail
cd "$(dirname "$0")"
command -v yt-dlp >/dev/null || pip3 install --break-system-packages -q yt-dlp
[[ -x tools/rhubarb/rhubarb ]] || { mkdir -p tools && cd tools \
  && curl -sSL -o r.zip https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.9.1/Rhubarb-Lip-Sync-1.9.1-Linux.zip \
  && unzip -q r.zip && mv rhubarb-lip-sync-1.9.1-linux rhubarb && rm r.zip && cd ..; }
[[ -d .venv ]] || python3 -m venv .venv
.venv/bin/pip install -q faster-whisper "av<16"
(cd remotion && npm i -s)
[[ -e ~/.claude/skills/hypit ]] || npx -y skills add hypit-ai/hypit -g -y
# HyperFrames: claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes
tools/rhubarb/rhubarb --version && npx -y hyperframes@0.8.172 --version
# VoiceStudio backend (voice clone). Engine: VoxCPM2 (Apache-2.0). Never OmniVoice (CC-BY-NC).
if [[ ! -d tools/VoiceStudio ]]; then
  git clone -q --depth 1 https://github.com/debpalash/VoiceStudio.git tools/VoiceStudio
  (cd tools/VoiceStudio && OMNIVOICE_ANALYTICS_DISABLED=1 node scripts/setup-api.mjs)
fi
# then start it, POST /models/install {"repo_id":"openbmb/VoxCPM2"} and POST /engines/sidecar/voxcpm2/install
