# VoiceNotes

A local-first, privacy-preserving voice-to-markdown tool for writers. Capture long-form ideas — articles, white papers, fiction — with a hotkey or from a pre-recorded audio file. Nothing leaves your machine.

Built in Python using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for on-device transcription with built-in voice activity detection.

> **Inspired by [SecureVoice](https://github.com/chradavi/SecureVoice)** by David Christian — a Rust macOS menu bar app for private speech-to-text. VoiceNotes takes the same privacy-first philosophy and extends it for long-form writing workflows with streaming transcription and structured Markdown output.

---

## What it does

VoiceNotes writes your spoken words directly to a Markdown file as you speak — sentence by sentence — or transcribes a pre-recorded `.wav` or `.mp3` file in one pass. Each session produces a structured file with YAML frontmatter (date, model, duration, word count) ready for editing and publishing.

**Two modes:**

| Mode | How to use |
|------|------------|
| Live capture | Press the hotkey to start recording, speak, press again to stop |
| File transcription | Pass an audio file with `--file recording.mp3` |

**Output format:**

```
20260508-1030-Ideasflowthroughm.md
```

```markdown
---
date: 2026-05-08T10:30:00
model: base
duration: 00:04:12
word_count: 623
---

Ideas flow through my mind like water...
```

## Install

**Requirements:** Python 3.9+, ffmpeg (for MP3 support)

```bash
# Install ffmpeg (macOS)
brew install ffmpeg

# Install VoiceNotes
git clone <repo>
cd VoiceNotes
pip install -e .
```

On first run, VoiceNotes downloads the Whisper `base` model (~148 MB) to `~/.cache/voicenotes/`.

## Usage

**Live capture** (hotkey defaults to `ctrl+space`):

```bash
voicenotes
```

Press the hotkey to start recording. Press it again to stop — the transcript is saved to `~/VoiceNotes/`.

**File transcription:**

```bash
voicenotes --file recording.wav
voicenotes --file interview.mp3
```

## Configuration

VoiceNotes looks for `~/.config/voicenotes/config.toml`. All fields are optional — defaults are shown.

```toml
model = "base"          # tiny | base | small | medium
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"
```

## Models

| Model | Size | Notes |
|-------|------|-------|
| tiny | 75 MB | Fastest, lower accuracy |
| **base** *(default)* | 148 MB | Fast, solid accuracy |
| small | 466 MB | More accurate |
| medium | 1.5 GB | High accuracy, slower |

Models are downloaded once from [huggingface.co/ggerganov/whisper.cpp](https://huggingface.co/ggerganov/whisper.cpp) and cached locally.

## Project layout

```
src/
  main.py         — CLI entrypoint (argparse, dependency wiring)
  config.py       — TOML config loading
  model.py        — model download and cache management
  transcribe.py   — faster-whisper wrapper
  output.py       — Markdown writer with YAML frontmatter
  hotkey.py       — global hotkey listener (pynput)
  capture.py      — microphone capture (sounddevice)
  session.py      — live capture session
  file_input.py   — audio file validation, decoding, and file session
tests/            — pytest suite (122 tests)
.docs/            — specs and planning docs
```

## Privacy

- Audio is processed entirely on-device
- No network requests after the one-time model download
- No telemetry, no accounts, no cloud

## License

MIT
