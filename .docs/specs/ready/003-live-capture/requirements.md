# Spec 003: Live Capture Session — Requirements

## Context

- **Feature**: FEAT-001 — Voice to Markdown
- **Story IDs**: STORY-001, STORY-002
- **Complexity**: M
- **Status**: Draft
- **Depends on**: 001-foundation, 002-transcription-core

## Background

This is the primary user-facing mode. The writer launches the tool, presses a hotkey to begin speaking, and presses the same hotkey to stop. Audio is captured from the microphone continuously, VAD detects sentence boundaries, and each transcribed segment is appended to the output Markdown file in real time. The session ends cleanly, with frontmatter finalized and empty sessions discarded.

## STORY-001: Live Capture Session

*As a writer, I want to start a voice capture session with a hotkey, speak freely, and stop with the same hotkey, so that my words land in a new Markdown file without interrupting my flow.*

### Acceptance Criteria

1. WHEN the user presses the configured hotkey while no session is active, the system shall begin recording audio from the default microphone and print a message confirming the session has started.
2. WHEN the user presses the configured hotkey while a session is active, the system shall stop recording, finalize the output file, and print the path of the written file.
3. WHEN a new session begins, the system shall create a Markdown file named `YYYYMMDD-HHMM-{first 15 characters of first transcribed speech}.md` in the configured output directory. If no speech is transcribed during the session the filename shall use the suffix `untitled` in place of the speech excerpt.
4. WHEN a session ends with no transcribed content, the system shall delete the output file and print a message informing the user that no content was captured.
5. The system shall not require more than one hotkey press to start a session and one hotkey press to stop a session.
6. WHEN the system cannot access the microphone, the system shall print a clear error message and exit with a non-zero status code without creating an output file.

## STORY-002: Streaming Transcription (session integration)

*As a writer, I want to see transcribed text appear in the file sentence-by-sentence as I speak, so that I can glance at the screen and know the capture is working.*

### Acceptance Criteria

7. WHILE a session is active, the system shall continuously capture audio from the microphone and pass it through the transcription pipeline.
8. WHILE a session is active, the system shall print each transcribed segment to the terminal as it is appended to the output file.
9. The system shall not wait until the session ends to write transcribed segments — each segment shall be written to the file as soon as it is transcribed.
