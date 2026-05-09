# Spec 003: Live Capture Session — Tasks

## Summary

- **Total**: 8 tasks
- **Completed**: 8
- **Remaining**: 0

## Tasks

- [x] 1. Create `src/hotkey.py` with `HotkeyListener` wrapping `pynput.GlobalHotKeys` *(~2h)*
  - Accept hotkey string (e.g. `"ctrl+space"`), convert to `pynput` format (e.g. `"<ctrl>+space"`)
  - `start()` and `stop()` manage listener thread lifecycle
  - Fulfills: AC-1, AC-2, AC-5

- [x] 2. Create `src/capture.py` with `AudioCapture` and `CaptureError` *(~2h)*
  - Open `sounddevice.InputStream` at 16 kHz mono float32
  - Accumulate samples in thread-safe list; `stop()` returns concatenated `np.ndarray`
  - Raise `CaptureError` on `PortAudioError`
  - Fulfills: AC-6, AC-7

- [x] 3. Create `src/session.py` with `LiveSession` skeleton and hotkey toggle logic *(~2h)*
  - Wire `HotkeyListener` to internal `_on_hotkey()` which toggles between start/stop
  - `run()` blocks on a `threading.Event` until session ends
  - Fulfills: AC-1, AC-2, AC-5

- [x] 4. Implement streaming transcription loop in `LiveSession` *(~3h)*
  - Background thread reads 5-second chunks (0.5s overlap) from `AudioCapture`
  - Each chunk passed to `Transcriber.stream()`; each segment written via `OutputWriter.write_segment()` and printed to terminal
  - Fulfills: AC-7, AC-8, AC-9

- [x] 5. Implement session finalization and file naming *(~2h)*
  - On stop: drain final chunk, call `writer.finalize(duration)`
  - Rename temp file to `YYYYMMDD-HHMM-{first_words or "untitled"}.md`
  - If no segments written: delete temp file, print "No content captured."
  - Print final file path on success
  - Fulfills: AC-2, AC-3, AC-4

- [x] 6. Create `src/main.py` with argparse entrypoint and dependency wiring *(~2h)*
  - Parse optional `file` positional argument
  - Call `load_config()`, handle `ConfigError` → exit 1
  - Call `ModelManager.ensure_available()` with progress display, handle `ModelError` → exit 1
  - Construct `Transcriber` and `LiveSession`; call `run()`
  - Fulfills: AC-1, AC-6

- [x] 7. Write unit tests for `HotkeyListener` and `AudioCapture` *(~2h)*
  - Mock `pynput.GlobalHotKeys`; verify callback fires; verify toggle behavior
  - Mock `sounddevice`; verify buffer accumulation; verify `CaptureError` on `PortAudioError`
  - Fulfills: AC-5, AC-6

- [x] 8. Write integration test for full session lifecycle *(~2h)*
  - Inject pre-recorded audio samples; simulate two hotkey presses
  - Verify output file created with correct name pattern, frontmatter, and segment content
  - Verify empty session (no audio) deletes temp file
  - Fulfills: AC-1, AC-2, AC-3, AC-4, AC-7, AC-8, AC-9
