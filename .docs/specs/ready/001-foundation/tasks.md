# Spec 001: Foundation — Tasks

## Summary

- **Total**: 6 tasks
- **Completed**: 6
- **Remaining**: 0

## Tasks

- [x] 1. Create `src/__init__.py` and `src/config.py` with `Config` dataclass and `DEFAULTS` *(~1h)*
  - Define `Config` frozen dataclass with fields: `model`, `hotkey`, `output_dir`, `language`
  - Define `DEFAULTS` dict and `VALID_MODELS` tuple
  - Fulfills: AC-7, AC-10

- [x] 2. Implement `load_config()` with TOML parsing, unknown-key detection, and value validation *(~2h)*
  - Use `tomllib` (3.11+) with `tomli` fallback; handle `FileNotFoundError` by returning defaults
  - Reject unknown keys with `ConfigError`; validate `model` against `VALID_MODELS`
  - Expand `output_dir` with `Path.expanduser()`
  - Fulfills: AC-6, AC-7, AC-8, AC-9, AC-11

- [x] 3. Write unit tests for `config.py` *(~2h)*
  - Test: defaults when file absent; valid file loads; unknown key raises `ConfigError`; invalid model raises `ConfigError`; `output_dir` expanded
  - Use `tmp_path` and monkeypatching for config path
  - Fulfills: AC-6, AC-7, AC-8, AC-9

- [x] 4. Create `src/model.py` with `ModelManager` and cache-hit check *(~1h)*
  - Constructor accepts `model_size` and optional `cache_dir` (defaults to `~/.cache/voicenotes/`)
  - `ensure_available()` returns cached path immediately if model file exists and `st_size > 0`
  - Fulfills: AC-5

- [x] 5. Implement model download with progress callback, size verification, and failure cleanup *(~2h)*
  - Uses direct HTTP stream via `urllib.request` with 64 KB chunks
  - Call `on_progress(downloaded, total)` on each chunk
  - After download: verify size matches registry expected bytes; on mismatch or exception remove file and raise `ModelError`
  - Fulfills: AC-1, AC-2, AC-3, AC-4

- [x] 6. Write unit tests for `model.py` *(~2h)*
  - Test: cache hit skips download; progress callback invoked; size mismatch raises `ModelError` and removes file; network error raises `ModelError` and removes file
  - Use `tmp_path` and mock HTTP responses
  - Fulfills: AC-1, AC-2, AC-3, AC-4, AC-5
