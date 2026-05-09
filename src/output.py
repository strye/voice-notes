from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.transcribe import TranscriptSegment

_SENTINEL_DURATION = "# __DURATION__"
_SENTINEL_WORD_COUNT = "# __WORD_COUNT__"
_SENTINEL_TITLE = "# __TITLE__"


def _fmt_duration(td: timedelta) -> str:
    total = int(td.total_seconds())
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class SessionMeta:
    date: datetime
    model: str
    duration: timedelta = field(default_factory=timedelta)
    word_count: int = 0


class OutputWriter:
    def __init__(self, path: Path, meta: SessionMeta) -> None:
        self._path = path
        self._meta = meta
        self._opened = False
        self._word_count = 0
        self._first_words: str | None = None
        self._title: str | None = None

    @property
    def first_words(self) -> str | None:
        return self._first_words

    def open(self) -> None:
        """Write the frontmatter stub. Creates parent directories if needed."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        stub = (
            "---\n"
            f"aliases:\n  - {_SENTINEL_TITLE}\n"
            f"title: {_SENTINEL_TITLE}\n"
            f"date: {self._meta.date.isoformat()}\n"
            f"model: {self._meta.model}\n"
            f"duration: \"00:00:00\" {_SENTINEL_DURATION}\n"
            f"word_count: 0 {_SENTINEL_WORD_COUNT}\n"
            "---\n"
            "\n"
        )
        self._path.write_text(stub, encoding="utf-8")
        self._opened = True

    def write_segment(self, segment: TranscriptSegment) -> None:
        """Append segment as a paragraph. Updates word count and first_words."""
        if not self._opened:
            raise RuntimeError("OutputWriter.open() must be called first")

        text = segment.text.strip()
        if not text:
            return

        if self._first_words is None:
            words = text.split()[:4]
            self._title = " ".join(w.capitalize() for w in words)
            self._first_words = "".join(w.capitalize() for w in words)

        self._word_count += len(text.split())

        with open(self._path, "a", encoding="utf-8") as f:
            f.write(text + "\n\n")

    def finalize(self, duration: timedelta) -> None:
        """Rewrite frontmatter with final duration, word_count, and title."""
        if not self._opened:
            raise RuntimeError("OutputWriter.open() must be called first")

        content = self._path.read_text(encoding="utf-8")

        content = content.replace(_SENTINEL_TITLE, self._title or "Untitled")
        duration_str = _fmt_duration(duration)
        content = content.replace(
            f'"00:00:00" {_SENTINEL_DURATION}',
            f'"{duration_str}"',
        )
        content = content.replace(
            f"0 {_SENTINEL_WORD_COUNT}",
            str(self._word_count),
        )

        self._path.write_text(content, encoding="utf-8")
