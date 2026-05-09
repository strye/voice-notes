# FEAT-001: Voice to Markdown

**Feature ID**: FEAT-001
**Created**: 2026-05-08
**Last Updated**: 2026-05-08
**Status**: Ready

## Overview

A local-first, privacy-preserving CLI tool that captures spoken ideas and writes them to structured Markdown files. Supports two modes: live capture (streaming transcription while speaking) and batch (transcribe a pre-recorded audio file). All processing runs offline using `faster-whisper` with built-in voice activity detection.

## Problem Statement

Writers lose ideas because the friction of typing interrupts the creative flow. Existing dictation tools either require a cloud connection, paste to a clipboard (limiting for long-form content), or produce unstructured output that needs significant cleanup before it can be used.

## Value Proposition

A writer can speak freely, stop when done, and immediately have a structured Markdown file ready for refinement — no cloud, no subscriptions, no manual formatting. The same tool handles recordings made on a phone or recorder, closing the loop between capture and draft.

## User Stories

| Story | Status | Spec |
|-------|--------|------|
| STORY-001: Live capture session | Ready | [003-live-capture](../../specs/ready/003-live-capture/) |
| STORY-002: Streaming transcription | Ready | [002-transcription-core](../../specs/ready/002-transcription-core/), [003-live-capture](../../specs/ready/003-live-capture/) |
| STORY-003: Audio file transcription | Ready | [004-file-transcription](../../specs/ready/004-file-transcription/) |
| STORY-004: Structured output | Ready | [002-transcription-core](../../specs/ready/002-transcription-core/) |
| STORY-005: First-run model setup | Ready | [001-foundation](../../specs/ready/001-foundation/) |
| STORY-006: Configuration | Ready | [001-foundation](../../specs/ready/001-foundation/) |

## Functional Requirements

### STORY-001: Live Capture Session

*As a writer, I want to start a voice capture session with a hotkey, speak freely, and stop with the same hotkey, so that my words land in a new Markdown file without interrupting my flow.*

FR-1. WHEN the user presses the configured hotkey while no session is active, the system shall begin recording audio from the default microphone.

FR-2. WHEN the user presses the configured hotkey while a session is active, the system shall stop recording and finalize the output file.

FR-3. WHEN a new session begins, the system shall create a new Markdown file in the configured output directory, named using the pattern `YYYYMMDD-HHMM-{first 15 characters of the first transcribed speech segment}.md`.

FR-4. WHEN a session ends with no transcribed content, the system shall delete the empty file and print a message informing the user that no content was captured.

FR-5. The system shall not require more than one hotkey press to start or stop a session.

---

### STORY-002: Streaming Transcription

*As a writer, I want to see transcribed text appear in the file sentence-by-sentence as I speak, so that I can glance at the screen and know the capture is working.*

FR-6. WHILE a session is active, the system shall use voice activity detection to identify speech segment boundaries without requiring user input.

FR-7. WHILE a session is active, the system shall transcribe each detected speech segment and append the result to the output file within 3 seconds of the segment ending.

FR-8. WHILE a session is active, the system shall print each transcribed segment to the terminal as it is written to the file.

FR-9. The system shall not buffer all audio until session end before writing transcribed text to the file.

---

### STORY-003: Audio File Transcription

*As a writer, I want to point the tool at a `.wav` or `.mp3` audio file and receive a structured Markdown transcript, so that I can transcribe recordings I made elsewhere.*

FR-10. WHEN the user provides a valid `.wav` or `.mp3` file path, the system shall transcribe the file and write a structured Markdown output file to the configured output directory.

FR-11. WHEN transcribing an audio file, the system shall name the output file using the pattern `YYYYMMDD-HHMM-{first 15 characters of the first transcribed speech segment}.md`, using the audio file's filesystem creation date for the timestamp.

FR-12. WHEN the user provides a file path that does not exist, the system shall display an error message identifying the missing path and exit without creating an output file.

FR-13. WHEN the user provides a file with an unsupported extension, the system shall display an error message listing the supported formats (`.wav`, `.mp3`) and exit without creating an output file.

FR-14. WHILE transcribing an audio file, the system shall display progress as a percentage of audio duration processed.

---

### STORY-004: Structured Output

*As a writer, I want each transcript file to have YAML frontmatter containing date, duration, model, and word count above the transcript body, so that my notes app or static site generator can index and sort my captures.*

FR-15. The system shall begin every output file with YAML frontmatter containing the fields: `date` (ISO 8601), `duration` (HH:MM:SS), `model` (model size identifier), and `word_count` (integer).

FR-16. WHEN a live session ends, the system shall calculate the final `duration` from session start to stop, and `word_count` from the total transcribed text, and write both to the frontmatter.

FR-17. WHEN an audio file is transcribed, the system shall set `duration` to the audio file's playback length.

FR-18. The system shall separate the YAML frontmatter block from the transcript body with a blank line after the closing `---`.

FR-19. The system shall write each transcribed speech segment as a separate paragraph in the transcript body, separated by a blank line.

---

### STORY-005: First-Run Model Setup

*As a new user, I want the tool to download the Whisper model automatically on first run with a clear progress indicator, so that I don't need to configure anything manually.*

FR-20. WHEN the configured Whisper model file is not present in the cache directory, the system shall download it before proceeding with any recording or transcription.

FR-21. WHILE a model is downloading, the system shall display progress as a percentage and the total expected file size.

FR-22. WHEN a model download completes, the system shall verify the downloaded file size matches the expected size before proceeding.

FR-23. WHEN a model download fails or the verified size does not match, the system shall display a clear error message, remove the incomplete file, and exit cleanly.

FR-24. The system shall cache downloaded models at `~/.cache/voicenotes/` and reuse them on subsequent runs without re-downloading.

---

### STORY-006: Configuration

*As a writer, I want to configure the hotkey, model size, and output directory via a config file, so that the tool fits my workflow without code changes.*

FR-25. The system shall read configuration from `~/.config/voicenotes/config.toml` on startup.

FR-26. WHEN no configuration file exists, the system shall apply defaults: `model = "base"`, `hotkey = "ctrl+space"`, `output_dir = "~/VoiceNotes"`.

FR-27. WHEN the configuration file contains an unrecognised key or invalid value, the system shall display an error message identifying the specific field and exit without starting.

FR-28. The system shall support configuration of the following fields: `hotkey`, `model` (tiny | base | small | medium), `output_dir`, and `language`.

FR-29. WHERE `language` is set in the configuration, the system shall pass that value to the Whisper model; otherwise the system shall default to English.

FR-30. The system shall not require the configuration file to exist in order to run.

---

## Non-Functional Requirements

NFR-1. The system shall perform all audio capture, transcription, and file writing on-device with no network requests after the initial model download.

NFR-2. WHILE a live session is active, the system shall append each transcribed segment to the output file within 3 seconds of the speech segment ending.

NFR-3. The system shall support macOS as the primary target platform.

NFR-4. The system shall not transmit audio data, transcripts, or configuration to any remote service.

## Technical Considerations

- **Transcription**: `faster-whisper` (CTranslate2 backend) with `silero-vad` for voice activity detection
- **Audio capture**: `sounddevice` (PortAudio bindings)
- **Hotkey**: `pynput` global listener
- **Audio file decoding**: `ffmpeg` (via `pydub` or `subprocess`) for format normalization to 16 kHz mono PCM before Whisper ingestion
- **Model cache**: `~/.cache/voicenotes/` using `faster-whisper`'s built-in download mechanism
- **Config format**: TOML via `tomllib` (stdlib in Python 3.11+) or `tomli` backport

## Dependencies

None — standalone tool.

## Out of Scope

- GUI or menu bar interface
- Speaker diarization (multiple speaker identification)
- Post-processing or LLM-based cleanup of transcripts
- Cloud transcription fallback
- Languages other than English (configuration hook exists but only English is validated in v1)
- `.aup3` Audacity project file support (export to `.wav` or `.mp3` first)
