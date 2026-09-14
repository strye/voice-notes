# VoiceNotes — Developer Guide

A local-first voice-to-markdown tool built in Python. Two modes: live capture (hotkey-triggered streaming transcription) and file transcription (`.wav`/`.mp3` batch processing). Output is structured Markdown with YAML frontmatter.

## Tech stack

- **faster-whisper** — CTranslate2-based Whisper with built-in silero-VAD (`vad_filter=True`, `device="cpu"`, `compute_type="int8"`)
- **sounddevice** — microphone capture at 16 kHz mono float32
- **pynput** — global hotkey listener
- **ffmpeg** (subprocess) — audio file decoding for file transcription mode
- **tomllib** (3.11+) / **tomli** (backport) — config parsing
- **pytest** — 117 tests across 6 test files

## Source layout

```
src/
  config.py       — load_config(), Config dataclass, ConfigError
  transcribe.py   — Transcriber.stream() → Generator[TranscriptSegment]
  output.py       — OutputWriter: open/write_segment/finalize, sentinel-based frontmatter
  hotkey.py       — HotkeyListener, _to_pynput() conversion
  capture.py      — AudioCapture: 16kHz mono, thread-safe buffer, CaptureError
  session.py      — LiveSession: hotkey toggle, 5s polling loop, file naming
  file_input.py   — validate_audio_file(), decode_audio_file(), FileSession
  main.py         — CLI entrypoint: --file dispatches FileSession, else LiveSession; --output overrides the output path
```

## Key design decisions

**Lazy imports** — `pynput` and `sounddevice` are imported inside functions, not at module level. This keeps the CLI fast and lets tests patch `sys.modules` rather than patching installed packages.

**Sentinel-based frontmatter** — `OutputWriter` writes `# __DURATION__` and `# __WORD_COUNT__` as YAML value placeholders, replaced in-place at `finalize()`. Avoids YAML re-parsing.

**Streaming as polling** — `LiveSession._stream_loop()` polls `AudioCapture.snapshot()` every 5 seconds, slicing `new_samples = snapshot[last_processed:]` to avoid reprocessing. Minimum 8,000 samples (0.5s) before transcribing.

**Test injection** — `LiveSession` and `FileSession` accept injectable `_capture` and `_poll_secs` so tests run at 0.05s polling with mock audio, no hardware required.

**sys.modules patching** — Hardware libraries not available in the system Python path are patched via `patch.dict("sys.modules", {...})` in tests. See `tests/test_hotkey_capture.py` for the pattern.

## Development setup

The project is installed editable into a local virtualenv, and the `voicenotes` command on PATH (`~/.local/bin/voicenotes`) is a symlink to `.venv/bin/voicenotes`. Code changes in `src/` take effect without reinstalling.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

`ffmpeg` must be on PATH for file transcription mode (`brew install ffmpeg`).

## Running tests

```bash
.venv/bin/python -m pytest
```

All 117 tests should pass. Tests do not require a microphone, ffmpeg, or internet access.

## Config file

`~/.config/voicenotes/config.toml` — all fields optional:

```toml
model = "base"          # tiny | base | small | medium
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"
```

## Model cache

Models download to `~/.cache/huggingface/hub/` on first use, managed automatically by `faster-whisper`.

## Claude Code skill

`skills/voice-notes/SKILL.md` is a portable skill that teaches Claude how to drive the CLI from other projects. It is symlinked into `~/.claude/skills/voice-notes` so it is available machine-wide. Deployment options are in `skills/voice-notes/README.md`. Update the skill when CLI flags, output format, or error messages change.

## Planning Workflows

Use `/indez [mode]` for all planning and implementation phases:

- `/indez plan --type feature` — create or refine a feature document
- `/indez design --name FEAT-NNN` — generate design and tasks from requirements
- `/indez implement --spec NNN-spec-name` — execute a spec's tasks
- `/indez sync` — report project status

Specs follow the three-file pattern (`requirements.md`, `design.md`, `tasks.md`) in `.docs/specs/`. See the `spec-best-practices` skill for conventions.
