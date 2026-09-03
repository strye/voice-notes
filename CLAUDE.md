# VoiceNotes — Developer Guide

A local-first voice-to-markdown tool built in Python. Two modes: live capture (hotkey-triggered streaming transcription) and file transcription (`.wav`/`.mp3`/`.m4a` batch processing). Output is structured Markdown with YAML frontmatter.

## Tech stack

- **faster-whisper** — CTranslate2-based Whisper with built-in silero-VAD (`vad_filter=True`, `device="cpu"`, `compute_type="int8"`)
- **sherpa-onnx** — CPU speaker diarization (pyannote segmentation-3.0 + TitaNet-small ONNX models), file mode only
- **sounddevice** — microphone capture at 16 kHz mono float32
- **pynput** — global hotkey listener
- **ffmpeg** (subprocess) — audio file decoding for file transcription mode
- **tomllib** (3.11+) / **tomli** (backport) — config parsing
- **pytest** — 185 tests across 8 test files

## Source layout

```
src/
  config.py       — load_config(), Config dataclass, ConfigError
  transcribe.py   — Transcriber.stream() → Generator[TranscriptSegment]
  output.py       — OutputWriter: open/write_segment/finalize, sentinel-based frontmatter
  hotkey.py       — HotkeyListener, _to_pynput() conversion
  capture.py      — AudioCapture: 16kHz mono, thread-safe buffer, CaptureError
  session.py      — LiveSession: hotkey toggle, 5s polling loop, file naming
  file_input.py   — validate_audio_file(), decode_audio_file(), FileSession (optional Diarizer)
  diarize.py      — ensure_models() downloader, Diarizer.run() → SpeakerTurn list, assign_speakers()
  main.py         — CLI entrypoint: --file dispatches FileSession, else LiveSession
```

## Key design decisions

**Lazy imports** — `pynput` and `sounddevice` are imported inside functions, not at module level. This keeps the CLI fast and lets tests patch `sys.modules` rather than patching installed packages.

**Sentinel-based frontmatter** — `OutputWriter` writes `# __DURATION__` and `# __WORD_COUNT__` as YAML value placeholders, replaced in-place at `finalize()`. Avoids YAML re-parsing.

**Streaming as polling** — `LiveSession._stream_loop()` polls `AudioCapture.snapshot()` every 5 seconds, slicing `new_samples = snapshot[last_processed:]` to avoid reprocessing. Minimum 8,000 samples (0.5s) before transcribing.

**Diarize first, then transcribe** — `FileSession` runs the diarizer over the whole decoded file before streaming Whisper (with `word_timestamps=True`), so the speaker count is known when the frontmatter is written and each segment is split at speaker changes via `assign_speakers()`. Live mode never diarizes: labels cannot be kept stable across independently transcribed chunks.

**Test injection** — `LiveSession` and `FileSession` accept injectable `_capture` and `_poll_secs` so tests run at 0.05s polling with mock audio, no hardware required.

**sys.modules patching** — Hardware libraries not available in the system Python path are patched via `patch.dict("sys.modules", {...})` in tests. See `tests/test_hotkey_capture.py` for the pattern.

## Running tests

```bash
python3 -m pytest
```

All 185 tests should pass. Tests do not require a microphone, ffmpeg, or internet access. One diarization smoke test exercises the real `sherpa-onnx` API and is skipped unless the models are already cached in `~/.cache/voicenotes/diarization/`.

## Config file

`~/.config/voicenotes/config.toml` — all fields optional:

```toml
model = "base"          # tiny | base | small | medium
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"
diarize = false         # file mode only
# num_speakers = 2
```

## Model cache

Whisper models download to `~/.cache/huggingface/hub/` on first use, managed automatically by `faster-whisper`. Diarization models download to `~/.cache/voicenotes/diarization/` on first `--diarize` run, verified by pinned SHA-256 in `src/diarize.py`.

## Planning Workflows

Use `/indez [mode]` for all planning and implementation phases:

- `/indez plan --type feature` — create or refine a feature document
- `/indez design --name FEAT-NNN` — generate design and tasks from requirements
- `/indez implement --spec NNN-spec-name` — execute a spec's tasks
- `/indez sync` — report project status

Specs follow the three-file pattern (`requirements.md`, `design.md`, `tasks.md`) in `.docs/specs/`. See the `spec-best-practices` skill for conventions.
