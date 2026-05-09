# SecureVoice Repository Analysis

## What It Is

A **macOS-only, fully offline speech-to-text dictation tool** that runs as a menu bar app. Press a hotkey → speak → release → transcribed text lands on the clipboard. Zero cloud, zero API keys.

Two implementations exist:
- **`securevoice/`** — Rust production version with Metal GPU acceleration (the real one)
- **`python/`** — Python reference implementation (simpler, CPU-only, no audio conversion)

---

## Architecture Overview

```
Hotkey press
    → cpal captures audio (native sample rate, stereo)
    → to_whisper_format(): mono mix + resample to 16 kHz
    → whisper-rs inference (Whisper.cpp via Metal)
    → arboard writes text to clipboard
    → User pastes with ⌘V
```

Everything runs on-device. The only network call is a one-time model download from Hugging Face.

---

## File Map

| File | Lines | Role |
|------|-------|------|
| `securevoice/src/main.rs` | 333 | Event loop, state machine, thread coordination |
| `securevoice/src/audio.rs` | 95 | **Audio capture + format conversion** |
| `securevoice/src/transcribe.rs` | 43 | **Whisper model loading & inference** |
| `securevoice/src/downloader.rs` | 56 | Model download & cache management |
| `securevoice/src/settings.rs` | 191 | Config persistence (JSON) |
| `securevoice/src/tray.rs` | 112 | Menu bar UI (muda + tray-icon) |
| `securevoice/src/hotkey.rs` | 33 | Global hotkey registration |
| `securevoice/src/paste.rs` | 10 | Clipboard write |
| `securevoice/src/permissions.rs` | 53 | macOS microphone permission dialog |
| `securevoice/src/state.rs` | 34 | App state enum |
| `python/app.py` | 189 | Python reference implementation |

---

## Whisper Transcription — The Part We Care About

### Model

Downloaded from `huggingface.co/ggerganov/whisper.cpp` (GGML format, Whisper.cpp compatible).

Four sizes available:

| Size | File | Disk |
|------|------|------|
| Tiny | `ggml-tiny.bin` | 75 MB |
| Base | `ggml-base.bin` | 141 MB |
| Small | `ggml-small.bin` | 466 MB |
| Medium | `ggml-medium.bin` | 1.5 GB |

Cached at `~/Library/Caches/securevoice/`. Default: Base.

### Inference Code (`transcribe.rs`)

```rust
// Load model once, reuse context across recordings
let ctx = WhisperContext::new_with_params(
    model_path,
    WhisperContextParameters { use_gpu: true }  // Metal on macOS
)?;

// Per-transcription (cheap to create)
let mut state = ctx.create_state()?;
let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });
params.set_language(Some("en"));
params.set_print_progress(false);
params.set_print_realtime(false);

state.full(params, &samples)?;

// Collect segments
let text: String = (0..state.full_n_segments()?)
    .map(|i| state.full_get_segment_text(i).unwrap_or_default())
    .collect();
text.trim().to_string()
```

Key decisions:
- **Greedy sampling** (`best_of: 1`) — fastest, good enough for dictation
- **English-only** (`set_language("en")`) — hardcoded, not configurable
- **Metal GPU** — enabled via `whisper-rs` feature `["metal"]` in Cargo.toml
- **Minimum 8,000 samples** (0.5s) — shorter recordings silently discarded

### Audio Format Conversion (`audio.rs`)

Whisper requires **16 kHz mono float32**. The conversion happens after recording stops:

```rust
fn to_whisper_format(raw: &[f32], native_rate: u32, channels: usize) -> Vec<f32> {
    // Step 1: Mix stereo to mono
    let mono: Vec<f32> = raw.chunks(channels)
        .map(|frame| frame.iter().sum::<f32>() / channels as f32)
        .collect();

    // Step 2: Resample to 16 kHz via linear interpolation
    let out_len = (mono.len() as f64 * 16_000.0 / native_rate as f64) as usize;
    (0..out_len).map(|i| {
        let pos = i as f64 * native_rate as f64 / 16_000.0;
        let lo = pos as usize;
        let hi = (lo + 1).min(mono.len() - 1);
        let frac = pos - lo as f64;
        mono[lo] * (1.0 - frac) as f32 + mono[hi] * frac as f32
    }).collect()
}
```

### Threading Model

- **Main thread**: winit event loop — handles all UI, hotkey, state transitions
- **model-init thread**: Downloads + loads Whisper on startup (sends `ModelReady` event when done)
- **transcribe thread**: Spawned per-recording, sends `TranscribeResult(text)` event when done

Events cross thread boundaries via `winit::event_loop::EventLoopProxy<AppEvent>`.

---

## What's Reusable

For a new project needing Whisper transcription, the minimal extractable pieces are:

### 1. `transcribe.rs` — Drop-in Whisper wrapper
Self-contained. Takes a model path + `&[f32]` samples, returns `String`.
Dependency: `whisper-rs = { version = "0.16", features = ["metal"] }`

### 2. `audio.rs` — Audio capture + conversion
Captures from default mic, converts to Whisper-compatible format.
Dependency: `cpal = "0.17"`

### 3. `downloader.rs` — Model download & caching
Downloads GGML model files from Hugging Face with progress reporting.
Dependencies: `reqwest` (blocking), `dirs`

### 4. `settings.rs` — Model size metadata
Contains URLs, filenames, and expected byte sizes for all 4 model variants. Useful even if you don't reuse the settings system.

---

## Python Reference (`python/app.py`)

Much simpler but illustrates the same flow:

```python
import whisper
import sounddevice as sd
import numpy as np

model = whisper.load_model("base")  # downloads automatically

# Record
audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()

# Transcribe
result = model.transcribe(audio.flatten())
text = result["text"].strip()
```

No audio conversion needed here — sounddevice records directly at 16 kHz mono if you ask it to.

---

## Key Dependencies (Rust)

```toml
whisper-rs = { version = "0.16", features = ["metal"] }  # Whisper.cpp bindings
cpal = "0.17"          # Audio capture
arboard = "3"          # Clipboard
global-hotkey = "0.7"  # System-wide hotkey
tray-icon = "0.21"     # Menu bar icon
muda = "0.17"          # Menu bar menus
winit = "0.30"         # Event loop
reqwest = { version = "0.13", features = ["blocking"] }
dirs = "6"
serde_json = "1"
```

Build requirement: Xcode Command Line Tools + cmake (for whisper.cpp compilation).

---

## macOS Permissions Required

1. **Microphone** — audio capture
2. **Input Monitoring** — global hotkey
3. **Accessibility** — clipboard write (paste)

Permission request code is in `permissions.rs` using `objc2-av-foundation`.

---

## Configuration Storage

- **Settings**: `~/Library/Application Support/securevoice/settings.json`
- **Model cache**: `~/Library/Caches/securevoice/`

```json
{
  "model": "base",
  "hotkey": "cmd+shift+space",
  "hold_to_record": false
}
```
