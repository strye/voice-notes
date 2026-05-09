# Spec 001: Foundation — Requirements

## Context

- **Feature**: FEAT-001 — Voice to Markdown
- **Story IDs**: STORY-005, STORY-006
- **Complexity**: S
- **Status**: Draft
- **Depends on**: None

## Background

Before any recording or transcription can occur, the tool must read and validate user configuration and ensure the correct Whisper model is available locally. This spec establishes the foundation all other specs build on: a typed config layer and a model manager that handles first-run download, progress reporting, size verification, and caching.

## STORY-005: First-Run Model Setup

*As a new user, I want the tool to download the Whisper model automatically on first run with a clear progress indicator, so that I don't need to configure anything manually.*

### Acceptance Criteria

1. WHEN the configured Whisper model file is not present in `~/.cache/voicenotes/`, the system shall download it from the `faster-whisper` model hub before proceeding.
2. WHILE a model is downloading, the system shall display a progress indicator showing the percentage downloaded and the total expected file size in MB.
3. WHEN a model download completes, the system shall verify the downloaded file size matches the expected size and proceed only if they match.
4. WHEN a model download fails or the verified size does not match the expected size, the system shall display an error message naming the failure, remove any incomplete file, and exit with a non-zero status code.
5. The system shall cache downloaded models at `~/.cache/voicenotes/` and reuse them on subsequent runs without re-downloading.

## STORY-006: Configuration

*As a writer, I want to configure the hotkey, model size, and output directory via a config file, so that the tool fits my workflow without code changes.*

### Acceptance Criteria

6. The system shall read configuration from `~/.config/voicenotes/config.toml` on startup.
7. WHEN no configuration file exists at the expected path, the system shall apply the following defaults without error: `model = "base"`, `hotkey = "ctrl+space"`, `output_dir = "~/VoiceNotes"`, `language = "en"`.
8. WHEN the configuration file contains an unrecognised key, the system shall display an error message naming the unexpected key and exit with a non-zero status code.
9. WHEN the configuration file contains a recognised key with an invalid value, the system shall display an error message identifying the field and the set of valid values, then exit with a non-zero status code.
10. The system shall support the following configuration fields: `hotkey` (string), `model` (one of: tiny | base | small | medium), `output_dir` (string path), `language` (string, default "en").
11. The system shall not require the configuration file to exist in order to run.
