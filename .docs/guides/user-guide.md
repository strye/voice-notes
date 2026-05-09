# User Guide

VoiceNotes captures spoken ideas and writes them to structured Markdown files — locally, privately, with no cloud dependency. This guide covers both usage modes with a walkthrough of each.

---

## Modes at a glance

| Mode | Use case | How to invoke |
|------|----------|---------------|
| **Live capture** | Capture ideas as you speak, sentence by sentence | `voicenotes` |
| **File transcription** | Transcribe a pre-recorded `.wav` or `.mp3` | `voicenotes --file recording.mp3` |

Both modes accept `--output` to override the output path.

---

## Output format

Every session produces a single Markdown file in `~/VoiceNotes/` (or your configured `output_dir`).

**File name:**

```
YYYYMMDD-HHMM-{first15chars}.md
```

For example, a session started at 10:30 on May 8 2026 where you said "Ideas are the currency of creativity" produces:

```
20260508-1030-Ideasarethecurre.md
```

To use a specific path and name instead, pass `--output`:

```bash
voicenotes --output ~/Documents/meeting-notes.md
voicenotes --file interview.mp3 --output ~/Documents/interview-transcript.md
```

The parent directory is created automatically if it does not exist.

**File contents:**

```markdown
---
date: 2026-05-08T10:30:00
model: base
duration: 00:04:12
word_count: 623
---

Ideas are the currency of creativity. The best ones come unexpectedly,
while you're walking or just before sleep.

Every writer needs a fast way to capture them before they dissolve.
```

---

## Walkthrough — Live capture

### 1. Start VoiceNotes

```bash
voicenotes
```

VoiceNotes loads the model (instant after first run) and waits silently. Nothing is recording yet.

### 2. Start recording

Press the hotkey (default: `ctrl+space`).

```
Recording… (press hotkey to stop)
```

VoiceNotes is now capturing audio from your microphone. Speak naturally. Every ~5 seconds, the transcription catches up and prints each sentence to the terminal as it is recognized:

```
Recording… (press hotkey to stop)
Ideas are the currency of creativity.
The best ones come unexpectedly, while you're walking or just before sleep.
```

### 3. Stop recording

Press the hotkey again (`ctrl+space`).

VoiceNotes finishes transcribing the remaining audio, finalizes the file, and prints the output path:

```
Saved: /Users/you/VoiceNotes/20260508-1030-Ideasarethecurre.md
```

### 4. Open the file

The Markdown file is ready to edit in any editor. The YAML frontmatter records the session metadata; the body is your transcription, ready to refine.

**Empty session:** If you stop before any speech is recognized, no file is created:

```
No content captured.
```

---

## Walkthrough — File transcription

### 1. Run with `--file`

```bash
voicenotes --file ~/Recordings/interview.mp3
```

Supported formats: `.wav`, `.mp3`

### 2. Watch progress

VoiceNotes decodes the audio and transcribes it in one pass, printing progress as it goes:

```
Transcribing interview.mp3… 24%
Transcribing interview.mp3… 51%
Transcribing interview.mp3… 78%
Transcribing interview.mp3… 100%
Saved: /Users/you/VoiceNotes/20260508-1045-Todaywerelooking.md
```

The output file uses the audio file's creation date (not today's date) in the frontmatter.

**No speech detected:** If the file contains no recognizable speech, the file is still saved with frontmatter only (word count: 0) and a notice is printed.

---

## Configuration

Create `~/.config/voicenotes/config.toml` to override defaults. All fields are optional.

```toml
model = "base"
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"
```

### `model`

The Whisper model to use for transcription.

| Value | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 75 MB | Fastest | Lower |
| `base` | 148 MB | Fast | Good |
| `small` | 466 MB | Moderate | Better |
| `medium` | 1.5 GB | Slow | Best |

`base` is the default and works well for most content. Use `small` or `medium` for technical vocabulary, accents, or noisy recordings.

Changing the model triggers a one-time download of the new model file.

### `hotkey`

Any modifier + key combination recognized by your OS. Examples:

```toml
hotkey = "ctrl+space"      # default
hotkey = "cmd+shift+space"
hotkey = "ctrl+alt+r"
```

### `output_dir`

Where transcription files are saved. Supports `~` for your home directory.

```toml
output_dir = "~/Documents/Notes"
output_dir = "/Volumes/External/VoiceNotes"
```

The directory is created automatically if it does not exist.

### `language`

The spoken language of your recordings. Use a BCP-47 language code.

```toml
language = "en"    # English (default)
language = "fr"    # French
language = "es"    # Spanish
language = "de"    # German
```

---

## CLI reference

| Flag | Argument | Description |
|------|----------|-------------|
| _(none)_ | | Start live capture mode |
| `--file` | `AUDIO_FILE` | Transcribe a `.wav` or `.mp3` file |
| `--output` | `OUTPUT_PATH` | Save to this exact path instead of the auto-generated name |

`--output` works with both modes and overrides both the folder and the filename.

---

## Tips

**Keep sentences natural.** Whisper transcribes sentence by sentence based on voice activity pauses. Speak in complete thoughts rather than stopping mid-sentence.

**Reduce background noise.** VAD (voice activity detection) filters silence, but loud background noise can produce spurious segments.

**Review immediately.** The first few seconds after stopping while the transcription is fresh is the best time to scan for misrecognized words.

**Use `tiny` for quick notes.** If you are capturing short bursts of ideas and speed matters more than perfect accuracy, `tiny` is significantly faster.

**Transcribe recordings in batch.** Use `--file` to process existing recordings — interviews, voice memos, meeting notes — into editable Markdown.
