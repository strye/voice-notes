# Spec 002: Transcription Core — Design

## Overview

Two modules: `transcribe.py` wraps `faster-whisper` with VAD-enabled segment streaming, yielding one `TranscriptSegment` at a time; `output.py` owns the output file lifecycle — it writes the initial frontmatter stub, appends segments as they arrive, and rewrites the frontmatter with final values on close. Callers (Spec 003 and 004) drive the pipeline by feeding audio and calling `finalize()`.

## Components

### Transcriber *(Type: Service)*

**Purpose**: Load a `faster-whisper` model and expose a generator that streams `TranscriptSegment` objects from a block of audio samples. VAD is handled internally by `faster-whisper`'s built-in silero-VAD integration.

**Interface**:
```python
@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float

class Transcriber:
    def __init__(self, model_path: str, language: str = "en"): ...

    def stream(
        self,
        audio: np.ndarray,          # float32, 16 kHz mono
        sample_rate: int = 16_000,
    ) -> Generator[TranscriptSegment, None, None]:
        """Yield one segment per detected speech region. Skips empty segments."""
```

**Behavior**:
- `faster_whisper.WhisperModel` is constructed once in `__init__` with `device="cpu"` and `compute_type="int8"` for portable performance on Apple Silicon.
- `model.transcribe()` is called with `vad_filter=True` and `language=language`.
- The method iterates `segments` from the `transcribe()` return value and yields one `TranscriptSegment` per segment.
- Segments whose `text.strip()` is empty are discarded (AC-4).
- `stream()` can be called multiple times on the same `Transcriber` instance.

---

### OutputWriter *(Type: Service)*

**Purpose**: Manage one output Markdown file for the duration of a session. Writes the frontmatter stub on open, appends segments on each `write_segment()` call, and rewrites frontmatter with final `duration` and `word_count` on `finalize()`.

**Interface**:
```python
@dataclass
class SessionMeta:
    date: datetime
    model: str
    duration: timedelta = field(default_factory=timedelta)
    word_count: int = 0

class OutputWriter:
    def __init__(self, path: Path, meta: SessionMeta): ...

    def open(self) -> None:
        """Write frontmatter stub to path. Creates parent dirs if needed."""

    def write_segment(self, segment: TranscriptSegment) -> None:
        """Append segment text as a paragraph followed by a blank line."""

    def finalize(self, duration: timedelta) -> None:
        """Rewrite frontmatter with final duration and word_count, then close."""

    @property
    def first_words(self) -> str | None:
        """Return first 15 non-whitespace characters of transcript, or None."""
```

**Behavior**:
- `open()` writes a YAML block with `duration: "00:00:00"` and `word_count: 0` as placeholders, followed by `---\n\n`.
- `write_segment()` appends `segment.text.strip() + "\n\n"` and increments an internal word count.
- `finalize()` seeks to byte 0, reads the file, replaces the placeholder frontmatter values, and rewrites. Uses a sentinel comment `# __DURATION__` and `# __WORD_COUNT__` in the initial write so replacement is unambiguous.
- `first_words` is populated after the first `write_segment()` call.

---

## Data Models

```python
@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float

@dataclass
class SessionMeta:
    date: datetime
    model: str
    duration: timedelta = field(default_factory=timedelta)
    word_count: int = 0
```

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `src/transcribe.py` | Create | `Transcriber`, `TranscriptSegment` |
| `src/output.py` | Create | `OutputWriter`, `SessionMeta` |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Model file missing at construction | `FileNotFoundError` propagates — caller (main.py) catches and exits |
| `transcribe()` raises on malformed audio | Exception propagates to caller; file left as-is |
| Empty segment text | Silently discarded, not yielded (AC-4) |
| Disk full on `write_segment` | `OSError` propagates to caller |
| `finalize()` called before `open()` | `RuntimeError("OutputWriter.open() must be called first")` |

## Testing Strategy

- **Unit — Transcriber**: mock `faster_whisper.WhisperModel`; verify empty segments discarded; verify `stream()` yields one item per non-empty model segment.
- **Unit — OutputWriter**: verify frontmatter structure after `open()`; verify segment appended correctly; verify `finalize()` rewrites duration and word_count accurately; verify `first_words` returns first 15 chars.
- Use `tmp_path` for all file operations.
