---
name: voice-notes
description: Transcribe audio to Markdown with the local `voicenotes` CLI (faster-whisper, fully on-device). Use when the user asks to transcribe a recording, convert a .wav/.mp3/.m4a/voice memo to text, capture a voice note, dictate into a file, or "run voicenotes". Handles preflight checks, file mode, live hotkey mode, format conversion, and reading the resulting Markdown back.
argument-hint: "[audio file] [--output path]"
allowed-tools: [Bash, Read, Glob]
---

# voice-notes

`voicenotes` turns speech into a Markdown file with YAML frontmatter. Everything runs on the
user's machine. Nothing is uploaded. Two modes:

| Mode | Command | When |
|------|---------|------|
| File | `voicenotes --file recording.mp3` | User has an audio file. Preferred from Claude Code. |
| Live | `voicenotes` | User wants to dictate now. Requires the user at the keyboard. |

## Preflight (run once per session)

```bash
command -v voicenotes && voicenotes --help >/dev/null && echo OK
command -v ffmpeg >/dev/null && echo "ffmpeg OK" || echo "ffmpeg MISSING"
```

- **`voicenotes` missing**: it is not installed on this machine. Point the user at the
  voice-notes repo and its install steps (`python3 -m venv .venv && .venv/bin/pip install -e .`,
  then symlink `.venv/bin/voicenotes` into `~/.local/bin`). Do not pip-install it into the
  current project's environment.
- **`ffmpeg` missing**: file mode will fail. Tell the user to run `brew install ffmpeg`.
- **First run** downloads the Whisper model (about 150 MB for `base`) into
  `~/.cache/huggingface/hub/`. Warn the user it may take a minute and needs network once.

## File mode

1. **Check the format.** Only `.wav` and `.mp3` are accepted. Anything else (`.m4a`, `.ogg`,
   `.flac`, `.mp4`, `.webm`, iPhone voice memos) must be converted first:

   ```bash
   ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav
   ```

   Write the converted file next to the original or in a temp dir. Say that you converted it.

2. **Run it.** Use `--output` when the user names a destination or when the transcript should
   land inside the current project. Otherwise let it use the default output directory.

   ```bash
   voicenotes --file /path/to/recording.wav --output ./notes/recording.md
   ```

   The command prints a progress percentage and finishes with `Saved: <path>`. Parse that line
   to find the file. Speed depends on the configured model: `base` runs several times faster
   than real time on CPU, `medium` is close to real time. Use a generous Bash timeout.

   A stderr line beginning `Warning: You are sending unauthenticated requests to the HF Hub`
   is harmless noise from faster-whisper's cache check. Ignore it. It is not a failure.

3. **Read the result back** with Read and act on whatever the user actually asked for
   (summarize, extract tasks, clean up, file it). The transcript is plain paragraphs, one
   Whisper segment per paragraph, no speaker labels, no timestamps.

### Exit behaviour

| Output | Meaning | What to do |
|--------|---------|------------|
| `Saved: <path>` exit 0 | Success | Read the file |
| `No speech detected in X.` then `Saved: ...-untitled.md` | Silence or music only | Tell the user; the file has empty body |
| `Error: File not found: ...` exit 1 | Bad path | Fix the path |
| `Error: Unsupported format '.m4a'...` exit 1 | Needs conversion | Run the ffmpeg step |
| `Error: ffmpeg not found` exit 1 | Missing dependency | `brew install ffmpeg` |
| `Error: Failed to decode ...` exit 1 | Corrupt or not really audio | Try `ffmpeg -i file` to inspect |
| `Configuration error: ...` exit 1 | Bad `~/.config/voicenotes/config.toml` | Show the user the offending line |

## Live mode

Live mode blocks until the user presses the hotkey once to start and once to stop, then writes
one file and exits. It needs a microphone, macOS Accessibility permission for the global hotkey,
and a human at the keyboard. Claude cannot press the hotkey.

- Never run it in a sandboxed or non-interactive shell. Tell the user to run it themselves in a
  terminal, or run it in the background with `run_in_background` and tell them the hotkey
  (default `ctrl+space`, overridable in config).
- If they want the note in the project, pass `--output ./path/note.md`.
- When the process exits, look for `Saved: <path>` in its output and read the file.
- `Error: Hotkey unavailable` means another app owns the combination or Accessibility
  permission is missing. Suggest a different `hotkey` in config or granting permission in
  System Settings → Privacy & Security → Accessibility.

## Output format

Default location is `~/VoiceNotes/`. Default filename is `YYYYMMDD-HHMM-FirstFourWords.md`,
where the timestamp is the recording start time (live) or the audio file's creation time (file).

```markdown
---
aliases:
  - First Four Words Here
title: First Four Words Here
date: 2026-05-08T10:30:00
model: base
duration: "00:04:12"
word_count: 623
---

First paragraph of transcript...

Second paragraph...
```

The frontmatter is Obsidian-friendly. Keep it intact if you edit the body.

## Configuration

`~/.config/voicenotes/config.toml`, all keys optional:

```toml
model = "base"          # tiny | base | small | medium
hotkey = "ctrl+space"
output_dir = "~/VoiceNotes"
language = "en"         # BCP-47 code
```

- Suggest `small` or `medium` when the user complains about accuracy, and warn about the
  larger download and slower speed. Suggest `tiny` only for quick drafts.
- Set `language` when the recording is not English. Whisper does much better with it set.
- Do not edit this file without telling the user. It affects every project on the machine.

## Do not

- Do not send audio to any cloud transcription API. The whole point of this tool is local.
- Do not reimplement transcription with a Python snippet when the CLI is available.
- Do not run live mode expecting it to return on its own.
- Do not pass `--file` a directory, a video, or an unsupported extension without converting.
