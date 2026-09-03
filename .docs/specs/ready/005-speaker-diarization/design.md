# Spec 005: Speaker Diarization — Design

## Overview

One new module, `diarize.py`, owns model download, the `sherpa-onnx` diarization pass, and word-to-speaker alignment. `TranscriptSegment` gains optional `speaker` and `words` fields so the rest of the pipeline can carry attribution without changing its shape. `FileSession` runs diarization over the decoded samples first, then streams Whisper with word timestamps and attributes each segment as it arrives, so progress reporting stays incremental and the speaker count is known before the output file is opened. `OutputWriter` writes a bold label only when the speaker changes. `LiveSession` is untouched.

Model choice was settled by benchmark on three two-speaker English clips (two from the sherpa-onnx release, one synthesized with two macOS voices). The pyannote segmentation-3.0 fp32 model paired with NVIDIA TitaNet-small was the fastest combination at roughly 0.15x realtime on Apple Silicon, reproduced the synthesized clip's turn boundaries exactly, and got the speaker count right on all clips with a clustering threshold of 0.8. WeSpeaker CAM++ over-clustered and collapsed to one speaker when hinted. 3D-Speaker ERes2Net was three times slower. The int8 segmentation variant was noisier for no meaningful speed gain.

## Components

### Model registry and downloader *(Type: Util, in `src/diarize.py`)*

**Purpose**: Fetch and verify the two ONNX models on first use, store them in the VoiceNotes cache, and return their paths.

**Interface**:
```python
DIARIZATION_CACHE_DIR = Path.home() / ".cache" / "voicenotes" / "diarization"

class DiarizationError(Exception): ...

@dataclass(frozen=True)
class ModelSpec:
    filename: str           # name on disk inside the cache dir
    url: str
    sha256: str             # of the final file on disk
    size_bytes: int         # of the download
    archive_member: str | None = None  # path inside a .tar.bz2, if the download is an archive
    archive_sha256: str | None = None  # of the archive itself, when archive_member is set

SEGMENTATION_MODEL = ModelSpec(
    filename="pyannote-segmentation-3.0.onnx",
    url="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2",
    sha256="220ad67ca923bef2fa91f2390c786097bf305bceb5e261d4af67b38e938e1079",
    size_bytes=6_958_444,
    archive_member="sherpa-onnx-pyannote-segmentation-3-0/model.onnx",
    archive_sha256="24615ee884c897d9d2ba09bb4d30da6bb1b15e685065962db5b02e76e4996488",
)
EMBEDDING_MODEL = ModelSpec(
    filename="nemo_en_titanet_small.onnx",
    url="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/nemo_en_titanet_small.onnx",
    sha256="ad4a1802485d8b34c722d2a9d04249662f2ece5d28a7a039063ca22f515a789e",
    size_bytes=40_257_283,
)

@dataclass(frozen=True)
class DiarizationModels:
    segmentation: Path
    embedding: Path

def ensure_models(cache_dir: Path = DIARIZATION_CACHE_DIR) -> DiarizationModels:
    """Download any missing model, verify it, and return paths. Raises DiarizationError."""
```

**Behavior**:
- If `cache_dir / spec.filename` exists, it is reused without any network access.
- Otherwise download with `urllib.request.urlopen` to `<filename>.part`, streaming in 1 MB chunks. Print `\r  Downloading {filename}: {pct}% of {size_mb:.1f} MB` after each chunk, and a newline when complete. Expected size comes from `spec.size_bytes`, so progress works even if the server omits `Content-Length`.
- After download, verify byte length equals `size_bytes` and, for direct files, SHA-256 equals `sha256`. For archives, verify SHA-256 equals `archive_sha256`, extract only `archive_member` with `tarfile` into the final filename, verify the extracted file's SHA-256 equals `sha256`, then delete the archive.
- Any `URLError`, `OSError`, `tarfile.TarError`, size mismatch, or checksum mismatch removes the `.part` file and any partially extracted output and raises `DiarizationError` with a message naming the model and the cause.
- Note: the release tag `speaker-recongition-models` is misspelled upstream. The URL must keep the misspelling.

---

### Diarizer *(Type: Service, in `src/diarize.py`)*

**Purpose**: Run `sherpa-onnx` offline speaker diarization over 16 kHz mono float32 samples and return speaker turns relabelled by order of first appearance.

**Interface**:
```python
@dataclass(frozen=True)
class SpeakerTurn:
    start_sec: float
    end_sec: float
    speaker: int   # 1-based, ordered by first appearance

class Diarizer:
    def __init__(
        self,
        models: DiarizationModels,
        *,
        num_speakers: int | None = None,
        threshold: float = 0.8,
        num_threads: int = 2,
    ) -> None: ...

    def run(self, samples: np.ndarray, progress: Callable[[int], None] | None = None) -> list[SpeakerTurn]:
        """Returns turns sorted by start time. Calls progress(pct) as chunks complete. Raises DiarizationError."""
```

**Behavior**:
- `import sherpa_onnx` happens inside `__init__` (lazy import, matching the `pynput` and `sounddevice` pattern). An `ImportError` is re-raised as `DiarizationError("sherpa-onnx is not installed — reinstall VoiceNotes: pip install -e .")`.
- Builds `OfflineSpeakerDiarizationConfig` with `OfflineSpeakerSegmentationPyannoteModelConfig(model=segmentation)`, `SpeakerEmbeddingExtractorConfig(model=embedding, num_threads=num_threads)`, and `FastClusteringConfig(num_clusters=num_speakers or -1, threshold=threshold)`. `min_duration_on=0.3`, `min_duration_off=0.5` (library defaults).
- Calls `OfflineSpeakerDiarization.process(samples, callback)`. The callback receives `(processed_chunks, total_chunks)`, forwards `int(processed * 100 / total)` to `progress`, and returns 0.
- Result segments are read with `sort_by_start_time()`. sherpa-onnx speaker ids are arbitrary integers, so the method walks segments in time order and maps each new id to the next label starting at 1.
- Any exception from `sherpa_onnx` during `process` is wrapped in `DiarizationError`.
- Empty input (no samples) returns an empty list without calling the library.

---

### Speaker alignment *(Type: Util, in `src/diarize.py`)*

**Purpose**: Attribute a Whisper segment to one or more speakers and split it where the speaker changes.

**Interface**:
```python
def assign_speakers(segment: TranscriptSegment, turns: list[SpeakerTurn]) -> list[TranscriptSegment]:
    """Return one or more segments, each with speaker set. Never returns an empty list for non-empty text."""
```

**Behavior**:
- If `segment.words` is non-empty: each word is assigned the speaker of the turn with the greatest time overlap with `[word.start_sec, word.end_sec]`. A word overlapping no turn takes the speaker of the turn whose boundary is nearest to the word's midpoint. Consecutive words with the same speaker are joined with single spaces into one `TranscriptSegment` whose `start_sec` and `end_sec` are the first and last word times and whose `words` list holds those words.
- If `segment.words` is empty (word timestamps unavailable): the whole segment takes the speaker with the greatest overlap against `[start_sec, end_sec]`, with the same nearest-boundary fallback.
- If `turns` is empty: the segment is returned unchanged with `speaker=None`.
- Word text from `faster-whisper` carries a leading space; it is stripped before joining.

---

### TranscriptSegment and Transcriber changes *(Type: Data model, in `src/transcribe.py`)*

**Interface**:
```python
@dataclass
class Word:
    text: str
    start_sec: float
    end_sec: float

@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float
    speaker: int | None = None
    words: list[Word] = field(default_factory=list)

class Transcriber:
    def stream(self, audio, sample_rate=16_000, *, word_timestamps: bool = False) -> Generator[TranscriptSegment, None, None]: ...
```

**Behavior**:
- `stream` passes `word_timestamps=word_timestamps` to `WhisperModel.transcribe`. When true, each yielded segment's `words` is populated from `seg.words` (attributes `word`, `start`, `end`). When false, `words` stays empty. Existing callers are unaffected because both new fields default.
- `TranscriptSegment` equality in existing tests is unaffected because the new fields have defaults.

---

### OutputWriter changes *(Type: Service, in `src/output.py`)*

**Interface**:
```python
@dataclass
class SessionMeta:
    date: datetime
    model: str
    duration: timedelta = field(default_factory=timedelta)
    word_count: int = 0
    speakers: int | None = None   # written to frontmatter only when not None
```

**Behavior**:
- `open()` writes `speakers: {n}` on its own line after `word_count` only when `meta.speakers is not None`. When `None`, the frontmatter is byte-identical to today's output.
- `write_segment()` tracks `self._last_speaker`. When `segment.speaker is not None` and differs from `_last_speaker`, the paragraph is written as `**Speaker {n}:** {text}`. Otherwise the paragraph is written as `text`. `_last_speaker` is updated after every segment with a non-`None` speaker.
- `first_words`, `_title`, and `_word_count` are computed from `segment.text` before the prefix is added, so labels never leak into the filename, title, or word count.

---

### FileSession changes *(Type: Service, in `src/file_input.py`)*

**Interface**:
```python
class FileSession:
    def __init__(self, config, transcriber, output_dir, *, output_path=None, diarizer: Diarizer | None = None) -> None: ...
    def run(self, audio_path: Path) -> bool:
        """Returns True on full success, False if the transcript was written but diarization failed."""
```

**Behavior** when `diarizer` is not `None`:
1. Validate and decode as today.
2. Print `  Identifying speakers…` and call `diarizer.run(decoded.samples, progress)` where `progress` prints `\r  Identifying speakers… {pct}%`. Print a newline when finished.
3. On `DiarizationError`: print `Warning: speaker identification failed: {exc}` to stderr, set `turns = []`, and remember `diarization_failed = True`.
4. `speaker_count = len({t.speaker for t in turns})`. If `speaker_count <= 1`, set `turns = []` so no labels are written, and set `meta.speakers = speaker_count` (which will be 1 when speech was found, 0 when diarization found nothing). If diarization failed, `meta.speakers` stays `None` so the frontmatter is not misleading.
5. Open the writer with `SessionMeta(date=..., model=..., speakers=meta_speakers)`.
6. Stream with `self._transcriber.stream(decoded.samples, word_timestamps=bool(turns))`. For each segment, `for part in assign_speakers(seg, turns): writer.write_segment(part)`. Transcription progress printing is unchanged and is driven by the original segment's `end_sec`.
7. Finalize and rename exactly as today.
8. Return `not diarization_failed`.

When `diarizer` is `None`, behaviour and output are exactly as today, and `run` returns `True`. The `src.diarize` import in `file_input.py` is a module-level import of only the pure-Python pieces (`Diarizer` type, `assign_speakers`, `DiarizationError`); `sherpa_onnx` itself is only imported inside `Diarizer.__init__`, so a non-diarized run never touches it.

---

### Config changes *(Type: Util, in `src/config.py`)*

**Interface**:
```python
DEFAULTS = {..., "diarize": False, "num_speakers": None}

@dataclass(frozen=True)
class Config:
    ...
    diarize: bool = False
    num_speakers: int | None = None
```

**Behavior**:
- `diarize` must be a `bool`. Otherwise `ConfigError("Invalid diarize: must be true or false")`.
- `num_speakers` must be absent, or an `int` (not `bool`) greater than or equal to 1. Otherwise `ConfigError("Invalid num_speakers: must be a positive integer")`.
- Both keys are added to `VALID_KEYS` via `DEFAULTS`.

---

### CLI changes *(Type: Entrypoint, in `src/main.py`)*

**Interface**:
```python
parser.add_argument("--diarize", action="store_true", help="Label speakers in the transcript (requires --file).")
parser.add_argument("--num-speakers", type=_positive_int, metavar="N", help="Expected number of speakers; implies --diarize.")

def _resolve_diarization(args, config) -> tuple[bool, int | None]:
    """Returns (enabled, num_speakers). CLI values override config values."""
```

**Behavior**:
- `_positive_int` raises `argparse.ArgumentTypeError("must be a positive integer")` for values below 1 or non-integers, so argparse exits 2 with a message naming `--num-speakers`.
- `cli_requested = args.diarize or args.num_speakers is not None`.
- If `cli_requested and not args.file`: print `Error: speaker diarization is only available with --file.` to stderr and exit 1 before loading any model.
- `enabled = cli_requested or (config.diarize and args.file is not None)`. Config-only `diarize = true` is ignored for live sessions.
- `num_speakers = args.num_speakers if args.num_speakers is not None else config.num_speakers`.
- When enabled: call `ensure_models()` inside a `try`, on `DiarizationError` print `Error: {exc}` and exit 1. Then construct `Diarizer(models, num_speakers=num_speakers)` and pass it to `FileSession`.
- After `session.run(args.file)`, if it returns `False`, exit 1.
- Model loading for the `Transcriber` stays where it is. `ensure_models()` runs before the `Transcriber` is constructed so a download failure exits before Whisper spends time loading.

## Data Models

```python
Word(text: str, start_sec: float, end_sec: float)
TranscriptSegment(text, start_sec, end_sec, speaker: int | None = None, words: list[Word] = [])
SpeakerTurn(start_sec: float, end_sec: float, speaker: int)     # 1-based
DiarizationModels(segmentation: Path, embedding: Path)
ModelSpec(filename, url, sha256, size_bytes, archive_member=None, archive_sha256=None)
SessionMeta(date, model, duration, word_count, speakers: int | None = None)
```

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `src/diarize.py` | Create | `ModelSpec`, `SEGMENTATION_MODEL`, `EMBEDDING_MODEL`, `ensure_models()`, `DiarizationError`, `SpeakerTurn`, `Diarizer`, `assign_speakers()` |
| `src/transcribe.py` | Modify | Add `Word`; add `speaker` and `words` to `TranscriptSegment`; add `word_timestamps` keyword to `stream()` |
| `src/output.py` | Modify | Add `speakers` to `SessionMeta`; write `speakers` frontmatter line when set; label paragraphs on speaker change |
| `src/file_input.py` | Modify | Accept optional `diarizer`; diarize-then-transcribe flow; return `bool` from `run()` |
| `src/config.py` | Modify | Add `diarize` and `num_speakers` with validation |
| `src/main.py` | Modify | Add `--diarize`, `--num-speakers`; `_resolve_diarization()`; live-mode guard; model setup; non-zero exit on partial success |
| `pyproject.toml` | Modify | Add `sherpa-onnx>=1.12` dependency |
| `config.toml.example` | Modify | Document `diarize` and `num_speakers` |
| `README.md` | Modify | Usage, configuration, and model table entries for diarization |
| `CLAUDE.md` | Modify | Add `diarize.py` to source layout; note diarize-first pipeline; update test count |
| `tests/test_diarize.py` | Create | Downloader, `Diarizer`, `assign_speakers` tests |
| `tests/test_transcribe.py` | Modify | Word timestamp plumbing tests |
| `tests/test_output.py` | Modify | Label and `speakers` frontmatter tests |
| `tests/test_file_input.py` | Modify | Diarized `FileSession` tests |
| `tests/test_config.py` | Modify | `diarize` and `num_speakers` validation tests |
| `tests/test_main.py` | Create | `_resolve_diarization()` and `_positive_int` tests |
| `.docs/planning/features/FEAT-002-speaker-diarization.md` | Modify | Link stories to this spec, mark status Ready, resolve open questions |

## Error Handling

| Scenario | Behavior | Exit |
|----------|----------|------|
| `--diarize` or `--num-speakers` without `--file` | `Error: speaker diarization is only available with --file.` on stderr, nothing loaded | 1 |
| `--num-speakers 0` or `--num-speakers abc` | argparse usage error naming the option | 2 |
| Config `num_speakers` invalid | `Configuration error: Invalid num_speakers: must be a positive integer` | 1 |
| Config `diarize` not boolean | `Configuration error: Invalid diarize: must be true or false` | 1 |
| Model download network failure | `Error: failed to download {filename}: {reason}`; `.part` removed; no output file | 1 |
| Model size or checksum mismatch | `Error: {filename} failed verification (expected …, got …)`; file removed; no output file | 1 |
| `sherpa_onnx` import fails | `Error: sherpa-onnx is not installed — reinstall VoiceNotes: pip install -e .` | 1 |
| Diarization `process()` raises | `Warning: speaker identification failed: …` on stderr; unlabelled transcript written; `speakers` omitted from frontmatter | 1 |
| Diarization finds one speaker | Unlabelled transcript, `speakers: 1` | 0 |
| Diarization finds no speech | Unlabelled transcript, `speakers: 0` | 0 |
| Config `diarize = true` with live session | Live session runs normally without diarization | 0 |

## Testing Strategy

- **Unit — downloader**: patch `urllib.request.urlopen` with an in-memory response. Verify: existing file skips network; progress lines printed with percentage and MB; size mismatch removes `.part` and raises; checksum mismatch removes file and raises; archive member extracted and archive deleted; `URLError` wrapped in `DiarizationError`. Build a tiny real `.tar.bz2` in `tmp_path` for the archive path and compute its real hashes in the test.
- **Unit — Diarizer**: patch `sys.modules["sherpa_onnx"]` with a `MagicMock` module (see `tests/test_hotkey_capture.py` for the pattern). Verify: `FastClusteringConfig` receives `num_clusters=-1` by default and `N` when hinted, `threshold=0.8`; arbitrary speaker ids are relabelled 1, 2, 3 by first appearance; progress callback converts chunk counts to percentages; library exceptions become `DiarizationError`; empty input returns `[]` without calling the library.
- **Unit — assign_speakers**: segment fully inside one turn; segment spanning two turns split at the correct word; word with no overlap uses nearest turn; no words falls back to whole-segment overlap; empty turns returns unchanged segment; leading spaces on word text stripped.
- **Unit — Transcriber**: `word_timestamps` forwarded in `transcribe` kwargs; `words` populated when the fake segment has `.words`; empty when not requested.
- **Unit — OutputWriter**: label written on first labelled segment and on change; omitted when speaker repeats; `speakers:` line present only when `meta.speakers` set; title, filename slug, and word count exclude labels; output byte-identical to a pre-change fixture when no speaker data is present.
- **Unit — Config**: defaults `diarize=False`, `num_speakers=None`; valid values accepted; `num_speakers=0`, `"2"`, `true` rejected; `diarize="yes"` rejected.
- **Unit — FileSession**: mock diarizer returning two speakers, verify labels and `speakers: 2`; mock returning one speaker, verify no labels and `speakers: 1`; mock raising `DiarizationError`, verify transcript still written, warning on stderr, `run()` returns `False`, no `speakers` line; `word_timestamps=True` passed to `stream` only when turns exist; no diarizer means `stream` called without `word_timestamps=True` and output identical to existing tests.
- **Unit — main**: `_resolve_diarization` precedence table; `--num-speakers` implies enabled; `_positive_int` rejects 0 and non-integers.
- **Integration (manual, not in CI)**: run `voicenotes --file /tmp/diar-eval/synth-two.wav --diarize` and confirm five labelled paragraphs alternating Speaker 1 and Speaker 2, `speakers: 2` in frontmatter, and total wall time under 3x the non-diarized run.
