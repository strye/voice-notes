# Spec 001: Foundation — Design

## Overview

Two modules: `config.py` loads and validates a TOML config file into a typed `Config` dataclass with safe defaults; `model.py` checks the local cache and downloads the model if absent, reporting progress and verifying the result. Both modules are pure functions / classes with no global state — callers construct them explicitly.

## Components

### Config *(Type: Util)*

**Purpose**: Parse `~/.config/voicenotes/config.toml`, apply defaults for missing keys, and validate field values. Returns an immutable `Config` dataclass or raises a descriptive `ConfigError`.

**Interface**:
```python
@dataclass(frozen=True)
class Config:
    model: Literal["tiny", "base", "small", "medium"]
    hotkey: str
    output_dir: Path
    language: str

class ConfigError(Exception): ...

def load_config() -> Config:
    """Load from ~/.config/voicenotes/config.toml. Returns defaults if file absent."""
```

**Behavior**:
- Uses `tomllib` (Python 3.11+) with a `tomli` fallback for 3.10.
- Unknown keys raise `ConfigError` naming the unexpected field.
- Invalid `model` value raises `ConfigError` listing valid options.
- `output_dir` is expanded with `Path.expanduser()` but not created here.
- `language` is accepted as any non-empty string; English ("en") is the default.

---

### ModelManager *(Type: Util)*

**Purpose**: Ensure the correct `faster-whisper` model is present in `~/.cache/voicenotes/`. Downloads with a progress callback if absent. Raises `ModelError` on failure.

**Interface**:
```python
class ModelError(Exception): ...

class ModelManager:
    def __init__(self, model_size: str, cache_dir: Path | None = None): ...

    def ensure_available(
        self,
        on_progress: Callable[[int, int], None] | None = None
    ) -> Path:
        """
        Returns the local model path, downloading if necessary.
        on_progress(downloaded_bytes, total_bytes) called during download.
        Raises ModelError on download failure or size mismatch.
        """
```

**Behavior**:
- Cache dir defaults to `~/.cache/voicenotes/`.
- Uses `faster-whisper`'s built-in `download_model()` when available; falls back to direct HTTP if needed.
- Progress callback fires on each received chunk.
- On completion, verifies file exists and `stat().st_size > 0`.
- On failure: removes incomplete file, raises `ModelError` with the cause.

---

## Data Models

```python
VALID_MODELS = ("tiny", "base", "small", "medium")

DEFAULTS = {
    "model": "base",
    "hotkey": "ctrl+space",
    "output_dir": "~/VoiceNotes",
    "language": "en",
}
```

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `src/config.py` | Create | `Config` dataclass, `load_config()`, `ConfigError` |
| `src/model.py` | Create | `ModelManager`, `ModelError` |
| `src/__init__.py` | Create | Empty package marker |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Config file absent | Return defaults — not an error |
| Unknown config key `foo` | `ConfigError("Unexpected config key: 'foo'")` |
| Invalid model value `"huge"` | `ConfigError("Invalid model 'huge'. Valid values: tiny, base, small, medium")` |
| Download network failure | `ModelError("Download failed: <reason>")`, incomplete file removed |
| Size mismatch after download | `ModelError("Downloaded file size mismatch — expected X bytes, got Y")`, file removed |

All errors propagate to `main.py` which prints the message and exits with code 1.

## Testing Strategy

- **Unit — config**: defaults applied when file absent; each invalid field raises correct `ConfigError`; valid file loads correctly; `output_dir` is expanded.
- **Unit — model**: cache hit skips download; download calls progress callback; size mismatch triggers cleanup and `ModelError`; network error triggers cleanup.
- Use `tmp_path` fixtures (pytest) for all filesystem operations.
