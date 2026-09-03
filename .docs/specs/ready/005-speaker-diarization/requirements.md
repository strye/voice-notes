# Spec 005: Speaker Diarization — Requirements

## Context

- **Feature**: FEAT-002 — Speaker Diarization for File Transcription
- **Story IDs**: STORY-007, STORY-008, STORY-009, STORY-010
- **Complexity**: M
- **Status**: Ready
- **Depends on**: 002-transcription-core, 004-file-transcription

## Background

Whisper transcribes words but does not know who said them, so a recorded interview comes out as one unbroken monologue. This spec adds opt-in speaker diarization to `--file` transcription. It identifies speaker turns across the whole recording, attributes each transcribed word to a speaker, and labels paragraphs in the Markdown output with anonymous `Speaker N` labels. Diarization runs on-device with `sherpa-onnx`, which reuses the `onnxruntime` runtime already installed by `faster-whisper`, and fetches its models without any account or license gate. Live capture is deliberately excluded because speaker labels cannot be kept stable across independently transcribed 5-second chunks.

## STORY-007: Diarized File Transcription

*As a writer transcribing an interview, I want to turn on speaker separation for a `--file` run, so that the transcript shows where one speaker stops and another starts.*

### Acceptance Criteria

1. WHERE diarization is enabled, WHEN the user transcribes an audio file, the system shall identify speaker turns across the full recording and attribute every transcribed speech segment to exactly one speaker.
2. WHERE diarization is enabled, WHEN a transcribed speech segment overlaps more than one speaker turn, the system shall split the segment text at the speaker-change boundary so that each resulting paragraph is attributed to a single speaker.
3. The system shall assign speaker labels in order of first appearance in the recording, starting at `Speaker 1`.
4. WHEN the user passes a diarization command-line option without also passing `--file`, the system shall display an error message stating that diarization is only available for file transcription and exit with a non-zero status without starting a live session.
5. WHERE diarization is enabled only through the configuration file and the user starts a live session, the system shall run the live session without diarization and without error.
6. WHILE identifying speakers in an audio file, the system shall display a progress message that is distinct from the transcription progress message.
7. WHEN speaker identification fails after the diarization models have loaded, the system shall still write the unlabelled transcript, display a warning describing the failure, and exit with a non-zero status.
8. WHERE diarization is not enabled, the system shall produce output identical to the current file transcription output and shall not import or load any diarization library or model.

## STORY-008: Speaker-Labelled Markdown Output

*As a writer, I want speaker labels in the transcript to be unobtrusive and consistent, so that the file is readable as-is and easy to edit into named quotes later.*

### Acceptance Criteria

9. WHERE diarization is enabled, WHEN the speaker of a paragraph differs from the speaker of the preceding paragraph, the system shall prefix that paragraph with the speaker label in bold followed by a colon and a space, for example `**Speaker 2:** `.
10. WHERE diarization is enabled, WHEN a paragraph has the same speaker as the preceding paragraph, the system shall write it without a label prefix.
11. WHERE diarization is enabled, the system shall add a `speakers` field to the YAML frontmatter containing the integer count of distinct speakers detected.
12. WHERE diarization is enabled, WHEN only one speaker is detected, the system shall write the transcript without any speaker label prefixes and set `speakers: 1`.
13. WHERE diarization is enabled, the system shall derive the output filename slug and the `title` frontmatter field from the transcribed words only, excluding speaker labels.
14. WHERE diarization is enabled, the system shall exclude speaker labels from the `word_count` frontmatter field.

## STORY-009: Diarization Model Setup

*As a user enabling diarization for the first time, I want the required models to download automatically without creating an account, so that setup matches the rest of the tool.*

### Acceptance Criteria

15. WHEN diarization is enabled and a required diarization model is not present in the model cache, the system shall download it before processing the audio file.
16. WHILE a diarization model is downloading, the system shall display progress as a percentage and the total expected file size.
17. WHEN a diarization model download fails, or the downloaded file's size or checksum does not match the expected value, the system shall display a clear error message, remove the incomplete file, and exit with a non-zero status without writing an output file.
18. The system shall store diarization models under the VoiceNotes model cache directory and reuse them on subsequent runs without re-downloading.
19. The system shall not require an account, access token, or license acceptance step to obtain diarization models.
20. The combined download size of the diarization models shall not exceed 100 MB.

## STORY-010: Diarization Configuration

*As a writer who mostly transcribes interviews, I want to turn diarization on by default and hint at the number of speakers, so that I get accurate labels without extra flags every time.*

### Acceptance Criteria

21. The system shall accept a `--diarize` command-line flag that enables diarization for the current run.
22. The system shall accept a `--num-speakers N` command-line option that supplies the expected number of speakers, and WHEN this option is provided without `--diarize`, the system shall treat diarization as enabled.
23. The system shall support a `diarize` boolean field and a `num_speakers` positive integer field in the configuration file, defaulting to `false` and unset respectively.
24. WHEN both a configuration value and a command-line option are present for the same setting, the system shall use the command-line value.
25. WHEN `num_speakers` is provided with a value less than 1 or a non-integer value, whether on the command line or in the configuration file, the system shall display an error message identifying the field and exit with a non-zero status without processing.
26. WHERE `num_speakers` is not provided, the system shall determine the number of speakers automatically.
27. WHEN the configuration file sets `diarize` to a non-boolean value, the system shall display an error message identifying the field and exit with a non-zero status.

## Non-Functional Criteria

28. The system shall perform all diarization on-device with no network requests after the one-time model download.
29. The system shall not introduce PyTorch or any GPU-only dependency. Diarization shall run on CPU.
30. WHERE diarization is enabled, total processing time for a file shall not exceed 3x the processing time of the same file with diarization disabled, measured with the `base` Whisper model on Apple Silicon.
31. WHERE diarization is not enabled, the system shall have no measurable change in startup time or memory footprint compared to the previous release.
