from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

VALID_MODELS = ("tiny", "base", "small", "medium")

DEFAULTS: dict[str, object] = {
    "model": "base",
    "hotkey": "ctrl+space",
    "output_dir": "~/VoiceNotes",
    "language": "en",
    "diarize": False,
    "num_speakers": None,
}

VALID_KEYS = frozenset(DEFAULTS)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    model: Literal["tiny", "base", "small", "medium"]
    hotkey: str
    output_dir: Path
    language: str
    diarize: bool = False
    num_speakers: int | None = None


def load_config(path: Path | None = None) -> Config:
    """Load from ~/.config/voicenotes/config.toml. Returns defaults if file absent."""
    if path is None:
        path = Path.home() / ".config" / "voicenotes" / "config.toml"

    raw: dict[str, object] = {}

    if path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
            with open(path, "rb") as f:
                raw = tomllib.load(f)
        else:
            try:
                import tomli
                with open(path, "rb") as f:
                    raw = tomli.load(f)
            except ImportError as exc:
                raise ConfigError(
                    "Python < 3.11 requires the 'tomli' package: pip install tomli"
                ) from exc

    unknown = set(raw) - VALID_KEYS
    if unknown:
        names = ", ".join(f"'{k}'" for k in sorted(unknown))
        raise ConfigError(f"Unexpected config key(s): {names}")

    model = raw.get("model", DEFAULTS["model"])
    if model not in VALID_MODELS:
        raise ConfigError(
            f"Invalid model '{model}'. Valid values: {', '.join(VALID_MODELS)}"
        )

    hotkey = raw.get("hotkey", DEFAULTS["hotkey"])
    if not isinstance(hotkey, str) or not hotkey.strip():
        raise ConfigError("Invalid hotkey: must be a non-empty string")

    output_dir = Path(str(raw.get("output_dir", DEFAULTS["output_dir"]))).expanduser()

    language = raw.get("language", DEFAULTS["language"])
    if not isinstance(language, str) or not language.strip():
        raise ConfigError("Invalid language: must be a non-empty string")

    diarize = raw.get("diarize", DEFAULTS["diarize"])
    if type(diarize) is not bool:
        raise ConfigError("Invalid diarize: must be true or false")

    num_speakers = raw.get("num_speakers", DEFAULTS["num_speakers"])
    if num_speakers is not None:
        if type(num_speakers) is bool or not isinstance(num_speakers, int) or num_speakers < 1:
            raise ConfigError("Invalid num_speakers: must be a positive integer")

    return Config(
        model=model,  # type: ignore[arg-type]
        hotkey=hotkey,
        output_dir=output_dir,
        language=language,
        diarize=diarize,
        num_speakers=num_speakers,
    )
