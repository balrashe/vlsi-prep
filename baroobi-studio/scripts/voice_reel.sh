#!/usr/bin/env bash
# Cloned-voice reel: [sample -> profile] -> voice the beats -> Whisper + Rhubarb -> render renders/<slug>-v<N>.mp4
# Usage: voice_reel.sh <slug> [sample.(wav|m4a|mp3)] [version]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; slug="$1"; sample="${2:-}"; v="${3:-1}"
curl -sf http://127.0.0.1:3900/health | grep -q '"ok"' || {
  (cd "$root/tools/VoiceStudio" && OMNIVOICE_ANALYTICS_DISABLED=1 nohup bun scripts/dev-backend.mjs > "$root/tools/voicestudio.log" 2>&1 &)
  until curl -sf http://127.0.0.1:3900/health | grep -q '"ok"'; do sleep 3; done; }
curl -sf -X POST http://127.0.0.1:3900/engines/select -H 'Content-Type: application/json' -d '{"family":"tts","backend_id":"voxcpm2"}' >/dev/null
[[ -n "$sample" ]] && "$root/.venv/bin/python" -I "$root/scripts/clone_voice.py" profile "$sample"
"$root/.venv/bin/python" -I "$root/scripts/clone_voice.py" speak "$slug"
rm -rf "$root/projects/$slug/work"          # fresh Whisper + Rhubarb for the new voice
"$root/scripts/make_reel.sh" "$slug" "$v"
