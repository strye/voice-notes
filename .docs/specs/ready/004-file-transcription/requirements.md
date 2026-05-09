# Spec 004: File Transcription — Requirements

## Context

- **Feature**: FEAT-001 — Voice to Markdown
- **Story IDs**: STORY-003
- **Complexity**: S
- **Status**: Draft
- **Depends on**: 001-foundation, 002-transcription-core

## Background

Writers often record ideas on a phone or dedicated recorder and want to transcribe those recordings without a live session. This spec adds a batch mode that accepts a `.wav` or `.mp3` file, decodes it to the format Whisper expects, transcribes it with progress reporting, and writes the same structured Markdown output as the live capture mode. It integrates into the same `main.py` entrypoint via a `--file` flag.

## STORY-003: Audio File Transcription

*As a writer, I want to point the tool at a `.wav` or `.mp3` audio file and receive a structured Markdown transcript, so that I can transcribe recordings I made elsewhere.*

### Acceptance Criteria

1. WHEN the user invokes the tool with a valid `.wav` or `.mp3` file path, the system shall transcribe the file and write a structured Markdown output file to the configured output directory.
2. WHEN transcribing an audio file, the system shall name the output file using the pattern `YYYYMMDD-HHMM-{first 15 characters of first transcribed speech}.md`, where the date and time are taken from the audio file's filesystem creation timestamp. If no speech is transcribed the suffix shall be `untitled`.
3. WHEN the user provides a file path that does not exist, the system shall display an error message identifying the missing path and exit with a non-zero status code without creating an output file.
4. WHEN the user provides a file with an extension other than `.wav` or `.mp3`, the system shall display an error message listing the supported formats and exit with a non-zero status code without creating an output file.
5. WHILE transcribing an audio file, the system shall display progress as a percentage of audio duration processed, updated after each transcribed segment.
6. WHEN transcription of the audio file is complete, the system shall print the path of the written output file.
7. WHEN the audio file contains no detectable speech, the system shall write a Markdown file with frontmatter only (word_count: 0) and notify the user that no speech was detected.
