# voice-notes skill

A Claude Code skill that teaches Claude how to drive the `voicenotes` CLI correctly from any
project: preflight checks, file transcription, format conversion, live capture, and output
handling.

The canonical copy lives here in the voice-notes repo. Deploy it in one of two ways.

## Machine-wide (recommended)

Available in every project on this machine. Stays current with the repo.

```bash
ln -s /Users/strye/Documents/source/strye/voice-notes/skills/voice-notes ~/.claude/skills/voice-notes
```

## Per project

For a project that should carry the skill with it (for example, one shared with others who
also have `voicenotes` installed):

```bash
mkdir -p <project>/.claude/skills
cp -r /Users/strye/Documents/source/strye/voice-notes/skills/voice-notes <project>/.claude/skills/
```

A copy will not pick up later edits. Re-copy after changing `SKILL.md`.

## Requirements on the target machine

- `voicenotes` on PATH (see the repo README for install)
- `ffmpeg` on PATH for file mode
