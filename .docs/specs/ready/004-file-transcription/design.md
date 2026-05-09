# Spec 004: File Transcription — Design

## Overview

One new module — `file_input.py` — handles validation, decoding, and duration extraction for audio files. A thin `FileSession` class in the same module orchestrates the transcription loop with progress reporting, then delegates to `OutputWriter` for structured Markdown output. `main.py` gains a `--file` flag that routes to this path.

## Components

### FileValidator *(Type: Util)*

**Purpose**: Validate that the provided path exists and has a supported extension before any decoding begins.

**Interface**:
```python
SUPPORTED_EXTENSIONS = {".wav", ".mp3"}

class FileInputError(Exception): ...

def validate_audio_file(path: Path) -> Path:
    """
    Returns the resolved Path if valid.
    Raises FileInputError with a descriptive message otherwise.
    """
```

**Behavior**:
- Raises `FileInputError("File not found: {path}")` if `path` does not exist.
- Raises `FileInputError("Unsupported format '{suffix}'. Supported: .wav, .mp3")` if extension not in `SUPPORTED_EXTENSIONS`.
- Returns `path.resolve()` on success.

---

### AudioDecoder *(Type: Util)*

**Purpose**: Decode any supported audio file to a 16 kHz mono float32 `np.ndarray` that Whisper expects. Also returns the original file's duration in seconds.

**Interface**:
```python
@dataclass
class DecodedAudio:
    samples: np.ndarray   # float32, 16 kHz mono
    duration_sec: float
    created_at: datetime  # from file filesystem ctime

def decode_audio_file(path: Path) -> DecodedAudio:
    """Decode .wav or .mp3 to 16 kHz mono float32."""
```

**Behavior**:
- Uses `pydub.AudioSegment.from_file()` to load — handles both `.wav` and `.mp3` via ffmpeg.
- Converts to mono (`set_channels(1)`), resamples to 16 kHz (`set_frame_rate(16_000)`), exports to raw float32 PCM via `np.frombuffer`.
- `duration_sec` = `len(audio_segment) / 1000.0`.
- `created_at` from `path.stat().st_birthtime` (macOS) with `st_ctime` fallback.
- Raises `FileInputError("Failed to decode {path}: {reason}")` on `pydub` or ffmpeg errors.

---

### FileSession *(Type: Service)*

**Purpose**: Run the batch transcription pipeline — decode file, stream segments, report progress, write output.

**Interface**:
```python
class FileSession:
    def __init__(
        self,
        config: Config,
        transcriber: Transcriber,
        output_dir: Path,
    ): ...

    def run(self, audio_path: Path) -> None:
        """Validate, decode, transcribe, write. Prints progress and final path."""
```

**Behavior**:
- Calls `validate_audio_file()` → on `FileInputError`, prints and exits 1.
- Calls `decode_audio_file()` to get `DecodedAudio`.
- Constructs `OutputWriter` with `SessionMeta(date=decoded.created_at, model=config.model)`.
- Calls `transcriber.stream(decoded.samples)`. After each segment: `writer.write_segment(seg)` and updates progress display as `int((seg.end_sec / decoded.duration_sec) * 100)`.
- After all segments: calls `writer.finalize(timedelta(seconds=decoded.duration_sec))`.
- Renames output file to `YYYYMMDD-HHMM-{first_words or "untitled"}.md` using `decoded.created_at`.
- If no segments: writes frontmatter-only file, prints "No speech detected in {path}."
- Prints final output path.

---

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `src/file_input.py` | Create | `FileValidator`, `AudioDecoder`, `FileSession`, `FileInputError` |
| `src/main.py` | Modify | Add `--file` argument; dispatch to `FileSession.run()` when present |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| File not found | `FileInputError` → print message, exit 1 |
| Unsupported extension | `FileInputError` → print message listing `.wav`, `.mp3`, exit 1 |
| ffmpeg not installed | `FileInputError("ffmpeg not found — install via: brew install ffmpeg")`, exit 1 |
| Decode failure | `FileInputError("Failed to decode {path}: {reason}")`, exit 1 |
| No speech detected | Write frontmatter-only file, print notice, exit 0 |

## Testing Strategy

- **Unit — FileValidator**: missing file raises correct `FileInputError`; unsupported extension raises; valid `.wav` and `.mp3` return resolved path.
- **Unit — AudioDecoder**: mock `pydub`; verify output is float32, 16 kHz, mono; verify duration extracted; verify ffmpeg error wrapped in `FileInputError`.
- **Unit — FileSession**: mock `Transcriber` and `OutputWriter`; verify progress percentage updates; verify file renamed correctly; verify no-speech path writes frontmatter-only.
