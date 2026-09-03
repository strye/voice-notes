# Spec 005: Speaker Diarization — Tasks

## Summary

- **Total**: 9 tasks
- **Completed**: 9
- **Remaining**: 0

## Tasks

- [x] 1. Extend `TranscriptSegment` and `Transcriber` with word timestamps *(~1h)*
  - Add `Word` dataclass; add `speaker: int | None = None` and `words: list[Word]` to `TranscriptSegment`
  - Add `word_timestamps` keyword to `Transcriber.stream()`, forward to `transcribe()`, populate `words`
  - Tests in `tests/test_transcribe.py`: kwarg forwarded, words populated, defaults keep existing behaviour
  - Fulfills: AC-2, AC-8

- [x] 2. Extend `Config` with `diarize` and `num_speakers` *(~1h)*
  - Add both to `DEFAULTS` and the `Config` dataclass with defaults
  - Validate `diarize` is `bool`; `num_speakers` is absent or `int >= 1` and not `bool`
  - Tests in `tests/test_config.py` for defaults, valid values, and each rejection
  - Fulfills: AC-23, AC-25, AC-27

- [x] 3. Extend `OutputWriter` with speaker labels and `speakers` frontmatter *(~1.5h)*
  - Add `speakers: int | None` to `SessionMeta`; write `speakers:` line in `open()` only when set
  - Track last speaker in `write_segment()`; prefix `**Speaker N:** ` only on change
  - Keep `first_words`, title, and word count derived from unlabelled text
  - Tests in `tests/test_output.py` including a byte-identical check for the non-diarized path
  - Fulfills: AC-8, AC-9, AC-10, AC-11, AC-13, AC-14

- [ ] 4. Create `src/diarize.py` model registry and downloader *(~3h)*
  - `ModelSpec`, `SEGMENTATION_MODEL`, `EMBEDDING_MODEL` with pinned URLs, sizes, SHA-256
  - `ensure_models()` with streamed download, progress line, size and checksum verification, tar member extraction, cleanup on failure, `DiarizationError`
  - Tests in `tests/test_diarize.py` with patched `urlopen` and a real tiny `.tar.bz2` fixture
  - Fulfills: AC-15, AC-16, AC-17, AC-18, AC-19, AC-20

- [ ] 5. Implement `Diarizer` and `assign_speakers()` in `src/diarize.py` *(~3h)*
  - `SpeakerTurn`; `Diarizer` with lazy `sherpa_onnx` import, config construction, progress callback, first-appearance relabelling, error wrapping
  - `assign_speakers()` with word-level overlap attribution, nearest-boundary fallback, segment splitting, whole-segment fallback when no words
  - Tests in `tests/test_diarize.py` with `sys.modules` patching for `sherpa_onnx`
  - Fulfills: AC-1, AC-2, AC-3, AC-26, AC-28, AC-29

- [x] 6. Integrate diarization into `FileSession` *(~2h)*
  - Accept optional `diarizer`; diarize first with distinct progress line; handle `DiarizationError` as a warning
  - Collapse to unlabelled output when one or zero speakers; set `SessionMeta.speakers`
  - Stream with `word_timestamps` when turns exist; split segments via `assign_speakers()`
  - Return `bool` from `run()`
  - Tests in `tests/test_file_input.py` for two speakers, one speaker, failure, and unchanged non-diarized path
  - Fulfills: AC-1, AC-6, AC-7, AC-8, AC-12

- [x] 7. Wire CLI flags and dispatch in `src/main.py` *(~1.5h)*
  - Add `--diarize` and `--num-speakers` with `_positive_int`
  - `_resolve_diarization()` with CLI-over-config precedence and config-only live-mode pass-through
  - Live-mode guard for explicit CLI flags; `ensure_models()` before `Transcriber`; non-zero exit when `run()` returns `False`
  - Tests in new `tests/test_main.py`
  - Fulfills: AC-4, AC-5, AC-21, AC-22, AC-24, AC-25

- [x] 8. Add dependency and update documentation *(~1h)*
  - Add `sherpa-onnx>=1.12` to `pyproject.toml`
  - Document `diarize` and `num_speakers` in `config.toml.example`, README configuration section, README usage, and README models table
  - Update CLAUDE.md source layout, design decisions, and test count
  - Link STORY-007 to STORY-010 to this spec in FEAT-002, set status Ready, record resolved open questions
  - Fulfills: AC-19, AC-23

- [x] 9. End-to-end verification *(~1h)*
  - Fresh cache: run `voicenotes --file /tmp/diar-eval/synth-two.wav --diarize`; confirm model download progress, five alternating labelled paragraphs, `speakers: 2`
  - Run again with `--num-speakers 2` and confirm identical labels
  - Run without `--diarize` and confirm output matches pre-change format
  - Time both runs and confirm the diarized run is under 3x the plain run
  - Run `--diarize` without `--file` and confirm the error and exit 1
  - Fulfills: AC-30, AC-31
