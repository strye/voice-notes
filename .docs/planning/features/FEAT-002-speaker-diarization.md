# FEAT-002: Speaker Diarization for File Transcription

**Feature ID**: FEAT-002
**Created**: 2026-09-02
**Last Updated**: 2026-09-02
**Status**: Ready

## Overview

Add opt-in speaker separation to `--file` transcription. When enabled, VoiceNotes identifies who is speaking in a pre-recorded interview, meeting, or conversation and labels each paragraph of the Markdown transcript with an anonymous speaker label (`Speaker 1`, `Speaker 2`, ...). Diarization runs fully on-device using `sherpa-onnx`, which reuses the `onnxruntime` dependency already present via `faster-whisper` and requires no PyTorch and no gated model downloads.

## Problem Statement

Whisper transcribes words but has no concept of who said them. A transcript of a two-person interview reads as a single unbroken monologue, and the writer has to replay the recording to reconstruct who said what before the transcript is usable as source material.

## Value Proposition

A writer can drop a recorded interview or meeting into VoiceNotes and get a transcript where speaker changes are already marked, so quoting, attributing, and summarizing can start immediately. The privacy guarantee is unchanged: no audio leaves the machine, and no account is needed to fetch the additional models.

## User Stories

| Story | Status | Spec |
|-------|--------|------|
| STORY-007: Diarized file transcription | Ready | [005-speaker-diarization](../../specs/ready/005-speaker-diarization/) |
| STORY-008: Speaker-labelled Markdown output | Ready | [005-speaker-diarization](../../specs/ready/005-speaker-diarization/) |
| STORY-009: Diarization model setup | Ready | [005-speaker-diarization](../../specs/ready/005-speaker-diarization/) |
| STORY-010: Diarization configuration | Ready | [005-speaker-diarization](../../specs/ready/005-speaker-diarization/) |

## Functional Requirements

### STORY-007: Diarized File Transcription

*As a writer transcribing an interview, I want to turn on speaker separation for a `--file` run, so that the transcript shows where one speaker stops and another starts.*

FR-31. WHERE diarization is enabled, WHEN the user transcribes an audio file, the system shall identify speaker turns across the full recording and attribute every transcribed speech segment to exactly one speaker.

FR-32. WHERE diarization is enabled, WHEN a transcribed speech segment overlaps more than one speaker turn, the system shall split the segment text at the speaker-change boundary so that each resulting paragraph is attributed to a single speaker.

FR-33. The system shall assign speaker labels in order of first appearance in the recording, starting at `Speaker 1`.

FR-34. WHEN the user enables diarization without providing `--file`, the system shall display an error message stating that diarization is only available for file transcription and exit without starting a live session.

FR-35. WHILE diarizing an audio file, the system shall display a progress message distinct from the transcription progress so the user can tell which stage is running.

FR-36. WHEN diarization fails after transcription has succeeded, the system shall write the unlabelled transcript, display a warning describing the diarization failure, and exit with a non-zero status.

FR-37. WHERE diarization is not enabled, the system shall produce output byte-for-byte identical to the current file transcription output and shall not load any diarization model.

---

### STORY-008: Speaker-Labelled Markdown Output

*As a writer, I want speaker labels in the transcript to be unobtrusive and consistent, so that the file is readable as-is and easy to edit into named quotes later.*

FR-38. WHERE diarization is enabled, WHEN the speaker of a paragraph differs from the speaker of the preceding paragraph, the system shall prefix that paragraph with the speaker label in bold followed by a colon and a space (for example `**Speaker 2:** `).

FR-39. WHERE diarization is enabled, WHEN a paragraph has the same speaker as the preceding paragraph, the system shall write it without a label prefix.

FR-40. WHERE diarization is enabled, the system shall add a `speakers` field to the YAML frontmatter containing the integer count of distinct speakers detected.

FR-41. WHERE diarization is enabled, WHEN only one speaker is detected, the system shall write the transcript without any speaker label prefixes and set `speakers: 1`.

FR-42. WHERE diarization is enabled, the system shall derive the output filename slug and the `title` frontmatter field from the transcribed words only, excluding speaker labels.

FR-43. WHERE diarization is enabled, the system shall exclude speaker labels from the `word_count` frontmatter field.

---

### STORY-009: Diarization Model Setup

*As a user enabling diarization for the first time, I want the required models to download automatically without creating an account, so that setup matches the rest of the tool.*

FR-44. WHEN diarization is enabled and the required diarization models are not present in the model cache, the system shall download them before processing the audio file.

FR-45. WHILE a diarization model is downloading, the system shall display progress as a percentage and the total expected file size.

FR-46. WHEN a diarization model download fails or the downloaded file fails integrity verification, the system shall display a clear error message, remove the incomplete file, and exit without writing an output file.

FR-47. The system shall cache diarization models alongside the existing model cache and reuse them on subsequent runs without re-downloading.

FR-48. The system shall not require an account, access token, or license acceptance step to obtain diarization models.

---

### STORY-010: Diarization Configuration

*As a writer who mostly transcribes interviews, I want to turn diarization on by default and hint at the number of speakers, so that I get accurate labels without extra flags every time.*

FR-49. The system shall accept a `--diarize` command-line flag that enables diarization for the current run.

FR-50. The system shall accept a `--num-speakers N` command-line option that supplies the expected number of speakers as a hint, and WHEN this option is provided without `--diarize`, the system shall treat diarization as enabled.

FR-51. The system shall support a `diarize` boolean field and a `num_speakers` positive integer field in the configuration file, defaulting to `false` and unset respectively.

FR-52. WHEN both a configuration value and a command-line option are present for the same setting, the system shall use the command-line value.

FR-53. WHEN `num_speakers` is provided with a value less than 1 or a non-integer value, the system shall display an error message identifying the field and exit without processing.

FR-54. WHERE `num_speakers` is not provided, the system shall determine the number of speakers automatically.

---

## Non-Functional Requirements

NFR-5. The system shall perform all diarization on-device with no network requests after the one-time model download.

NFR-6. The system shall not introduce PyTorch or any GPU-only dependency; diarization shall run on CPU using `onnxruntime`.

NFR-7. WHERE diarization is enabled, total processing time for a file shall not exceed 3x the processing time of the same file with diarization disabled, measured on the `base` Whisper model on Apple Silicon.

NFR-8. The combined download size of the diarization models shall not exceed 100 MB.

NFR-9. WHERE diarization is not enabled, the system shall have no measurable change in startup time or memory footprint compared to the current release.

## Technical Considerations

- **Library**: `sherpa-onnx` (PyPI package `sherpa-onnx`), using its `OfflineSpeakerDiarization` API. Ships macOS arm64 and x86_64 wheels. CPU-only, depends on `onnxruntime`, which `faster-whisper` already installs.
- **Models**: a pyannote `segmentation-3.0` model exported to ONNX (~6 MB) plus a speaker-embedding model (~25 to 40 MB, exact choice to be settled in design; candidates are 3D-Speaker ERes2Net, WeSpeaker ResNet34, or NeMo TitaNet-small). Both are published as plain downloads in the `k2-fsa/sherpa-onnx` GitHub releases with no gating.
- **Input**: `sherpa-onnx` diarization consumes 16 kHz mono float32 samples, which is exactly what `decode_audio_file()` already produces. No second decode pass is needed.
- **Alignment**: enable `word_timestamps=True` in `faster-whisper` for diarized runs so segments can be split at word boundaries where a speaker change falls mid-segment. Each word is attributed to the speaker turn with the greatest overlap.
- **Data model**: `TranscriptSegment` gains an optional `speaker: int | None` field, defaulting to `None`, so live capture and non-diarized file runs are unaffected.
- **Output**: `OutputWriter` tracks the previous speaker and writes the label prefix only on change. Labels are excluded from `first_words`, `title`, and `word_count`.
- **Clustering**: when `num_speakers` is provided, pass it as the cluster count; otherwise use the library's threshold-based clustering.
- **Lazy import**: import `sherpa_onnx` inside the diarization module, consistent with the existing pattern for `pynput` and `sounddevice`, so tests can patch `sys.modules`.
- **Live mode exclusion**: the 5-second polling loop in `LiveSession` transcribes chunks independently. Speaker clustering needs the whole recording to keep labels stable, so live mode is deliberately out of scope for this feature.

## Resolved Questions

- **Embedding model**: NVIDIA TitaNet-small (38 MB) paired with the fp32 pyannote segmentation-3.0 model (6 MB). Chosen by benchmark on three two-speaker English clips: fastest of the three English candidates at roughly 0.15x realtime on Apple Silicon, exact turn boundaries on the synthesized clip, and correct speaker count on all clips with clustering threshold 0.8. See spec 005 design.md for the comparison.
- **Live mode and `--diarize`**: an explicit `--diarize` or `--num-speakers` flag without `--file` is a hard error. A `diarize = true` value in the config file is ignored for live sessions so that setting it does not break live capture.

## Dependencies

- FEAT-001: Voice to Markdown, specifically spec `004-file-transcription` (file validation, decoding, and `FileSession`) and spec `002-transcription-core` (`TranscriptSegment`, `OutputWriter`).
- External: `sherpa-onnx` Python package and its published ONNX models.

## Out of Scope

- Speaker diarization during live capture (`LiveSession`). Labels cannot be kept stable across independently transcribed 5-second chunks.
- Speaker identification or naming (mapping `Speaker 1` to a real person, or recognising the same voice across files). Labels are anonymous and per-file.
- Handling of overlapping speech. Each word is attributed to one speaker.
- Diarization of languages other than English (the feature inherits FEAT-001's English-only validation).
- GPU acceleration.
- Any change to the default, non-diarized output format.
