# VoiceNotes

A local-first, privacy-preserving voice-to-markdown tool for writers. Capture long-form ideas — articles, white papers, fiction — with a hotkey or from a pre-recorded audio file. Nothing leaves your machine.

Built in Python using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for on-device transcription with built-in voice activity detection.

> **Inspired by [SecureVoice](https://github.com/chradavi/SecureVoice)** by David Christian — a Rust macOS menu bar app for private speech-to-text. VoiceNotes takes the same privacy-first philosophy and extends it for long-form writing workflows with streaming transcription and structured Markdown output.

---

## What it does

VoiceNotes writes your spoken words directly to a Markdown file as you speak — sentence by sentence — or transcribes a pre-recorded `.wav`, `.mp3`, or `.m4a` file in one pass. Each session produces a structured file with YAML frontmatter (date, model, duration, word count) ready for editing and publishing.

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

**Requirements:** Python 3.9+, ffmpeg (for MP3 and M4A support)

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
voicenotes --file memo.m4a
```

**Speaker labels** (file transcription only):

```bash
voicenotes --file interview.mp3 --diarize
voicenotes --file panel.m4a --num-speakers 3
```

With `--diarize`, each change of speaker starts a new paragraph prefixed with `**Speaker 1:**`, `**Speaker 2:**`, and so on, and the frontmatter gains a `speakers` count. Labels are anonymous and numbered by first appearance. `--num-speakers N` implies `--diarize` and improves accuracy when you know how many people were talking. Diarization is not available during live capture.

## Configuration

VoiceNotes looks for `~/.config/voicenotes/config.toml`. All fields are optional — defaults are shown.

```toml
model = "base"          # tiny | base | small | medium
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"
diarize = false         # label speakers in --file transcripts
# num_speakers = 2      # optional hint; auto-detected when unset
```

## Models

| Model | Size | Notes |
|-------|------|-------|
| tiny | 75 MB | Fastest, lower accuracy |
| **base** *(default)* | 148 MB | Fast, solid accuracy |
| small | 466 MB | More accurate |
| medium | 1.5 GB | High accuracy, slower |

Models are downloaded once from [huggingface.co/ggerganov/whisper.cpp](https://huggingface.co/ggerganov/whisper.cpp) and cached locally.

**Speaker diarization models** (downloaded on first `--diarize` run, no account required):

| Model | Size | Role |
|-------|------|------|
| pyannote segmentation-3.0 | 6 MB | Detects speech and speaker-change points |
| NVIDIA TitaNet-small | 38 MB | Speaker embeddings for clustering |

Both run on CPU via [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) and are cached in `~/.cache/voicenotes/diarization/`.

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
  diarize.py      — speaker diarization (sherpa-onnx) and word-to-speaker alignment
tests/            — pytest suite
.docs/            — specs and planning docs
```

## Privacy

- Audio is processed entirely on-device
- No network requests after the one-time model download
- No telemetry, no accounts, no cloud

## License

MIT
