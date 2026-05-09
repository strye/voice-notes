# Spec 004: File Transcription — Tasks

## Summary

- **Total**: 5 tasks
- **Completed**: 5
- **Remaining**: 0

## Tasks

- [x] 1. Create `src/file_input.py` with `FileValidator` and `validate_audio_file()` *(~1h)*
  - Check path exists; check extension in `{".wav", ".mp3"}`
  - Raise `FileInputError` with descriptive message for each failure case
  - Return `path.resolve()` on success
  - Fulfills: AC-3, AC-4

- [x] 2. Implement `AudioDecoder` and `decode_audio_file()` in `file_input.py` *(~3h)*
  - Use `pydub.AudioSegment.from_file()` → mono → 16 kHz → float32 `np.ndarray`
  - Extract `duration_sec` from segment length; extract `created_at` from `st_birthtime` / `st_ctime`
  - Wrap pydub/ffmpeg errors in `FileInputError`; detect missing ffmpeg and give install hint
  - Fulfills: AC-1, AC-2

- [x] 3. Implement `FileSession.run()` with transcription loop and progress display *(~2h)*
  - Call `validate_audio_file()` and `decode_audio_file()`
  - Stream segments via `Transcriber.stream()`; call `writer.write_segment()` per segment
  - Print progress as percentage after each segment
  - Finalize and rename output file; handle no-speech case
  - Print final output path
  - Fulfills: AC-1, AC-2, AC-5, AC-6, AC-7

- [x] 4. Extend `src/main.py` with `--file` argument and dispatch *(~1h)*
  - Add `parser.add_argument("--file", type=Path, metavar="AUDIO_FILE")`
  - When `--file` provided: construct `FileSession` and call `run(args.file)`
  - Fulfills: AC-1

- [x] 5. Write unit tests for `file_input.py` and `FileSession` *(~2h)*
  - Validator: missing file, unsupported extension, valid paths
  - Decoder: mock pydub; verify float32 output, duration, created_at; ffmpeg missing → `FileInputError`
  - Session: mock Transcriber; verify progress updates, file naming, no-speech output
  - Fulfills: AC-2, AC-3, AC-4, AC-5, AC-7
