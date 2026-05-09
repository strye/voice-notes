# Spec 003: Live Capture Session — Design

## Overview

Three focused modules: `hotkey.py` registers and listens for the global hotkey using `pynput`; `capture.py` manages the `sounddevice` microphone stream and accumulates audio into a rolling buffer; `session.py` orchestrates the session lifecycle — wiring hotkey events to capture start/stop and driving the transcription + output pipeline. `main.py` is the CLI entrypoint that wires config, model, and session together.

## Components

### HotkeyListener *(Type: Util)*

**Purpose**: Register a global hotkey combination and invoke a callback on each press. Toggle behavior (start/stop on same key) is the caller's responsibility.

**Interface**:
```python
class HotkeyListener:
    def __init__(self, hotkey: str, on_press: Callable[[], None]): ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

**Behavior**:
- Uses `pynput.keyboard.GlobalHotKeys` with the configured key string (e.g. `"<ctrl>+space"`).
- `on_press` is called on each key event in the listener thread — callbacks must be thread-safe.
- `stop()` releases the listener and blocks until the thread exits.

---

### AudioCapture *(Type: Service)*

**Purpose**: Open a `sounddevice` input stream and accumulate float32 samples into a thread-safe buffer at 16 kHz mono.

**Interface**:
```python
class AudioCapture:
    def start(self) -> None: ...
    def stop(self) -> np.ndarray:
        """Stop capture and return all accumulated samples as float32 16kHz mono."""
```

**Behavior**:
- Opens a `sounddevice.InputStream` at 16 kHz, 1 channel, `dtype=float32`.
- Each callback appends samples to an internal `list[np.ndarray]`; `stop()` concatenates and returns the result.
- On `sounddevice.PortAudioError` (microphone unavailable), raises `CaptureError`.
- The buffer is cleared on each `start()` call so the object is reusable.

---

### LiveSession *(Type: Service)*

**Purpose**: Orchestrate the full session lifecycle: capture → transcribe → write → finalize. Handles the rolling-chunk strategy for near-real-time streaming.

**Interface**:
```python
class CaptureError(Exception): ...

class LiveSession:
    def __init__(
        self,
        config: Config,
        transcriber: Transcriber,
        output_dir: Path,
    ): ...

    def run(self) -> None:
        """Block until two hotkey presses (start + stop). Writes output file."""
```

**Behavior**:
- On first hotkey press: start `AudioCapture`, create a temporary `OutputWriter` at a temp path, print "Recording… (press hotkey to stop)".
- Streaming strategy: a background thread reads audio from the capture buffer in 5-second chunks, runs `Transcriber.stream()` on each chunk, calls `writer.write_segment()` and prints to terminal for each result.
- On second hotkey press: stop capture, drain the final chunk through the pipeline, call `writer.finalize(duration)`.
- Rename the temp file to the final name using `writer.first_words` (or `"untitled"` if None). Print the final path.
- If no segments were written: delete the temp file and print "No content captured."
- Chunks overlap by 0.5 seconds to avoid cutting words at boundaries.

---

### CLI Entrypoint *(Type: Util)*

**Purpose**: Parse arguments, load config, ensure model, construct dependencies, and dispatch to `LiveSession.run()`.

**Interface**:
```python
# src/main.py
def main() -> None: ...
```

**Behavior**:
- `argparse` with one positional-optional argument: `file` (path). If absent → live mode. If present → delegates to Spec 004's file transcription path.
- Calls `load_config()` → on `ConfigError`, prints message and exits 1.
- Calls `ModelManager.ensure_available(on_progress=print_progress)` → on `ModelError`, prints and exits 1.
- Constructs `Transcriber` and `LiveSession`, calls `run()`.

---

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `src/hotkey.py` | Create | `HotkeyListener` wrapping `pynput.GlobalHotKeys` |
| `src/capture.py` | Create | `AudioCapture`, `CaptureError` |
| `src/session.py` | Create | `LiveSession` orchestrating the full capture loop |
| `src/main.py` | Create | CLI entrypoint with argparse, config, model, dispatch |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Microphone unavailable | `CaptureError` → print message, exit 1, no file created |
| Hotkey already bound by OS | `pynput` raises; print "Hotkey unavailable — try a different combination", exit 1 |
| Empty session | Delete temp file, print "No content captured." |
| Disk full during write | `OSError` propagates to `run()`, prints message, temp file left for inspection |
| Transcriber raises mid-session | Log error, continue capture; if no segments written, treat as empty |

## Testing Strategy

- **Unit — HotkeyListener**: mock `pynput.GlobalHotKeys`; verify callback invoked on simulated key event.
- **Unit — AudioCapture**: mock `sounddevice.InputStream`; verify buffer accumulates correctly; verify `CaptureError` on `PortAudioError`.
- **Integration — LiveSession**: simulate two hotkey presses with injected audio; verify output file created with correct name and content; verify empty session deletes file.
