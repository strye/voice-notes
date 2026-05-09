# Installation Guide

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.9+ | 3.11+ recommended |
| ffmpeg | Required for `.mp3` decoding. Not needed for `.wav`-only use. |
| Microphone | Required for live capture mode only. |
| Internet | Required once for the initial model download. |

---

## Step 1 — Install Homebrew, Python, and ffmpeg

If you don't have Homebrew installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/homebrew/install/HEAD/install.sh)"
```

After installing, add Homebrew to your shell (add this to `~/.zshrc` and restart your terminal):

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Then install Python, ffmpeg, and pipx:

```bash
brew install python ffmpeg pipx
pipx ensurepath
```

Restart your terminal after running `pipx ensurepath`.

---

## Step 2 — Install VoiceNotes

```bash
pipx install git+<repo-url>
```

pipx installs VoiceNotes into an isolated environment and puts the `voicenotes` command on your PATH automatically. No virtual environment management required.

---

## Step 3 — macOS permissions

macOS requires explicit permission for microphone access and global hotkeys. These are requested on first use.

**Microphone** — prompted automatically when you first start a live capture session.

**Accessibility** — required for the global hotkey to work system-wide. You will likely need to add your terminal manually:

> 1. Open System Settings → Privacy & Security → Accessibility
> 2. Click the **+** button at the bottom of the app list
> 3. Navigate to Applications → Utilities → Terminal (or whichever terminal you use)
> 4. Click Open, then make sure the toggle next to it is on

**Input Monitoring** — also required on some macOS versions:

> System Settings → Privacy & Security → Input Monitoring → enable Terminal (or your Python runner)

If the hotkey does not respond, check both Accessibility and Input Monitoring.

---

## Step 4 — First run

```bash
voicenotes
```

On first launch, the Whisper `base` model (~150 MB) is downloaded automatically to `~/.cache/huggingface/hub/`. The download happens once; subsequent runs load the cached model instantly.

---

## Optional — Configuration file

VoiceNotes works without any configuration. To customize defaults, copy the included example file to the right location:

```bash
mkdir -p ~/.config/voicenotes
cp config.toml.example ~/.config/voicenotes/config.toml
```

Then open it and uncomment the lines you want to change. All fields are optional — the example file documents every option with its default value. See [User Guide](user-guide.md) for more detail.

---

## Troubleshooting

**`voicenotes: command not found`**
Run `pipx ensurepath`, restart your terminal, then retry.

**`ffmpeg not found` when transcribing an MP3**
Install ffmpeg with `brew install ffmpeg` and verify it is on your PATH with `ffmpeg -version`.

**Hotkey does not respond / "This process is not trusted"**
Check both Accessibility and Input Monitoring in System Settings → Privacy & Security. The terminal or process running `voicenotes` must be listed and enabled under both. After granting access, restart the terminal and try again.

**`Configuration error: Unexpected config key(s): ...`**
Your `config.toml` contains an unrecognized field. Valid keys are: `model`, `hotkey`, `output_dir`, `language`.

---

## Developer installation

For working on VoiceNotes itself, clone the repo and install in editable mode inside a virtual environment:

```bash
git clone <repo-url>
cd voice-notes
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

To make `voicenotes` available in every new terminal without manually activating the venv, add this to your `~/.zshrc`:

```bash
source /path/to/voice-notes/.venv/bin/activate
```

Run the test suite to verify everything is working (no microphone, ffmpeg, or internet required):

```bash
python3 -m pytest
```

All 114 tests should pass.
