# Spec 002: Transcription Core — Tasks

## Summary

- **Total**: 7 tasks
- **Completed**: 7
- **Remaining**: 0

## Tasks

- [x] 1. Create `src/transcribe.py` with `TranscriptSegment` dataclass and `Transcriber.__init__()` *(~2h)*
  - Define `TranscriptSegment(text, start_sec, end_sec)`
  - Construct `faster_whisper.WhisperModel` with `device="cpu"`, `compute_type="int8"`
  - Fulfills: AC-1

- [x] 2. Implement `Transcriber.stream()` with VAD-enabled segment generator *(~2h)*
  - Call `model.transcribe(audio, vad_filter=True, language=language)`
  - Iterate segments; yield `TranscriptSegment` for each non-empty segment
  - Discard segments where `text.strip()` is empty
  - Fulfills: AC-1, AC-2, AC-3, AC-4

- [x] 3. Write unit tests for `Transcriber` *(~2h)*
  - Mock `WhisperModel.transcribe()`; verify empty segments discarded; verify generator yields correctly; verify `stream()` is reusable
  - Fulfills: AC-2, AC-3, AC-4

- [x] 4. Create `src/output.py` with `SessionMeta` dataclass and `OutputWriter.open()` *(~2h)*
  - Write YAML frontmatter stub with sentinel placeholders for duration and word_count
  - Ensure blank line after closing `---`
  - Create parent directories if they don't exist
  - Fulfills: AC-5, AC-8

- [x] 5. Implement `OutputWriter.write_segment()` and `first_words` property *(~1h)*
  - Append `segment.text.strip() + "\n\n"` to file
  - Increment internal word count; set `first_words` on first call
  - Fulfills: AC-9

- [x] 6. Implement `OutputWriter.finalize()` *(~2h)*
  - Read file, replace sentinel placeholders with final `duration` (HH:MM:SS) and `word_count`
  - Rewrite file in-place; handle `open()` not called guard
  - Fulfills: AC-6, AC-7

- [x] 7. Write unit tests for `OutputWriter` *(~2h)*
  - Test: frontmatter structure after `open()`; segment appended as paragraph; `finalize()` rewrites values correctly; `first_words` returns first 15 chars; `finalize()` before `open()` raises `RuntimeError`
  - Fulfills: AC-5, AC-6, AC-8, AC-9
