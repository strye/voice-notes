from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from src.config import Config
from src.transcribe import Transcriber

SUPPORTED_EXTENSIONS = {".wav", ".mp3"}


class FileInputError(Exception):
    pass


def validate_audio_file(path: Path) -> Path:
    """Return resolved path if valid. Raise FileInputError otherwise."""
    if not path.exists():
        raise FileInputError(f"File not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise FileInputError(
            f"Unsupported format '{path.suffix}'. Supported: .wav, .mp3"
        )
    return path.resolve()


@dataclass
class DecodedAudio:
    samples: np.ndarray  # float32, 16 kHz mono
    duration_sec: float
    created_at: datetime


def decode_audio_file(path: Path) -> DecodedAudio:
    """Decode audio to 16 kHz mono float32 via ffmpeg."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-i", str(path),
                "-ar", "16000",
                "-ac", "1",
                "-f", "s16le",
                "-",
            ],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise FileInputError(
            "ffmpeg not found — install via: brew install ffmpeg"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise FileInputError(f"Failed to decode {path.name}: ffmpeg returned an error") from exc

    raw = np.frombuffer(result.stdout, dtype=np.int16)
    samples = raw.astype(np.float32) / 32768.0
    duration_sec = len(raw) / 16_000

    stat = path.stat()
    ts = getattr(stat, "st_birthtime", None) or stat.st_ctime
    created_at = datetime.fromtimestamp(ts)

    return DecodedAudio(samples=samples, duration_sec=duration_sec, created_at=created_at)


class FileSession:
    def __init__(
        self,
        config: Config,
        transcriber: Transcriber,
        output_dir: Path,
        *,
        output_path: Path | None = None,
    ) -> None:
        self._config = config
        self._transcriber = transcriber
        self._output_dir = output_dir
        self._output_path = output_path

    def run(self, audio_path: Path) -> None:
        from src.output import OutputWriter, SessionMeta

        path = validate_audio_file(audio_path)
        decoded = decode_audio_file(path)

        self._output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._output_dir / f".tmp-{datetime.now().strftime('%Y%m%d%H%M%S%f')}.md"

        meta = SessionMeta(date=decoded.created_at, model=self._config.model)
        writer = OutputWriter(tmp_path, meta)
        writer.open()

        for seg in self._transcriber.stream(decoded.samples):
            writer.write_segment(seg)
            if decoded.duration_sec > 0:
                pct = int((seg.end_sec / decoded.duration_sec) * 100)
                print(f"\r  {pct}% transcribed…", end="", flush=True)

        print()  # newline after progress line

        writer.finalize(timedelta(seconds=decoded.duration_sec))

        if self._output_path is not None:
            final_path = self._output_path
            final_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            slug = writer.first_words or "untitled"
            final_name = f"{decoded.created_at.strftime('%Y%m%d-%H%M')}-{slug}.md"
            final_path = self._output_dir / final_name
        tmp_path.rename(final_path)

        if writer.first_words is None:
            print(f"No speech detected in {audio_path.name}.")

        print(f"Saved: {final_path}")
