# baroobi-studio status

## Setup (done 2026-10-18)
- node 22.22, python 3.13, ffmpeg 6.1.1, git 2.43 preinstalled. Installed: yt-dlp 2026.08.19.
- HyperFrames plugin 0.8.172 (was already installed). Smoke test: renders/smoke-test.mp4, 1080x1920, 30fps, 3.000s.
- Hypit skill (global, ~/.claude/skills/hypit). Free/local paths only.
- Rhubarb Lip Sync 1.9.1 (tools/rhubarb). Remotion 4.0.536 (remotion/). faster-whisper 1.2.1 (.venv, av<16 pin).
- Container is ephemeral: run ./setup.sh in a new session.

## ai-job-search  (blocked)
- [ ] photos -> assets/character/photos/
- [ ] KREA/OpenArt cartoon output -> assets/character/
- [ ] reference reel URL
- [ ] beat breakdown + Hypit template
- [ ] script locked (draft: scripts/ai-job-search/script-v0.txt)
- [ ] voiceover -> assets/voice/ai-job-search.wav
- [ ] Rhubarb cues, Whisper captions, HyperFrames build, render renders/ai-job-search-v1.mp4
