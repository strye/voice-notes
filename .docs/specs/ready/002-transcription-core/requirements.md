# Spec 002: Transcription Core — Requirements

## Context

- **Feature**: FEAT-001 — Voice to Markdown
- **Story IDs**: STORY-002, STORY-004
- **Complexity**: M
- **Status**: Draft
- **Depends on**: 001-foundation

## Background

The transcription engine and Markdown output formatter are shared by both live capture and file transcription modes. This spec builds the central pipeline: a `Transcriber` that streams VAD-detected speech segments through `faster-whisper`, and an `OutputWriter` that formats those segments into structured Markdown with YAML frontmatter. Both live capture (Spec 003) and file transcription (Spec 004) depend on this module.

## STORY-002: Streaming Transcription

*As a writer, I want to see transcribed text appear in the file sentence-by-sentence as I speak, so that I can glance at the screen and know the capture is working.*

### Acceptance Criteria

1. WHILE audio samples are being provided, the system shall use voice activity detection to identify speech segment boundaries without requiring user input.
2. WHILE audio samples are being provided, the system shall transcribe each detected speech segment and yield the result as soon as the segment is complete.
3. The system shall not buffer all audio before beginning transcription — each segment shall be transcribed and yielded independently.
4. WHEN a speech segment produces an empty or whitespace-only transcription, the system shall discard it and not yield it to the caller.

## STORY-004: Structured Output

*As a writer, I want each transcript file to have YAML frontmatter containing date, duration, model, and word count above the transcript body, so that my notes app or static site generator can index and sort my captures.*

### Acceptance Criteria

5. The system shall create each output file beginning with a YAML frontmatter block containing the fields: `date` (ISO 8601 datetime), `duration` (HH:MM:SS), `model` (model size string), and `word_count` (integer, updated on finalization).
6. WHEN a session ends, the system shall update `duration` and `word_count` in the frontmatter with final values computed from the session.
7. WHEN an audio file is transcribed, the system shall set `duration` to the audio file's playback length in HH:MM:SS format.
8. The system shall separate the YAML frontmatter block from the transcript body with a blank line after the closing `---`.
9. The system shall write each transcribed speech segment as a separate paragraph in the transcript body, with a blank line between consecutive segments.
