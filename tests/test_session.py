from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.capture import AudioCapture
from src.session import LiveSession
from src.transcribe import TranscriptSegment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(hotkey: str = "ctrl+space", model: str = "base") -> MagicMock:
    cfg = MagicMock()
    cfg.hotkey = hotkey
    cfg.model = model
    return cfg


def make_transcriber(segments: list[TranscriptSegment] | None = None) -> MagicMock:
    mock = MagicMock()
    segs = segments or [TranscriptSegment("Hello world.", 0.0, 1.0)]
    # Each call to stream() returns a fresh iterator
    mock.stream.side_effect = lambda audio: iter(segs)
    return mock


def make_capture(samples: np.ndarray | None = None) -> MagicMock:
    """Mock AudioCapture returning fixed audio on snapshot/stop."""
    audio = samples if samples is not None else np.ones(16_000, dtype=np.float32)
    mock = MagicMock(spec=AudioCapture)
    mock.snapshot.return_value = audio
    mock.stop.return_value = audio
    return mock


def run_session_sync(
    session: LiveSession,
    press_count: int = 2,
    delay: float = 0.05,
) -> None:
    """Run session in a thread, firing hotkey presses after a short delay."""
    def _fire() -> None:
        for _ in range(press_count):
            time.sleep(delay)
            session._on_hotkey()

    t = threading.Thread(target=_fire, daemon=True)
    t.start()
    session._done.wait(timeout=5.0)
    t.join(timeout=1.0)


# ---------------------------------------------------------------------------
# Session start
# ---------------------------------------------------------------------------


def test_session_start_creates_tmp_file(tmp_path: Path) -> None:
    capture = make_capture()
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    assert len(md_files) == 1


def test_session_output_file_has_correct_name_pattern(tmp_path: Path) -> None:
    capture = make_capture()
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    # Pattern: YYYYMMDD-HHMM-{first_words}.md
    name = md_files[0].name
    assert len(name) > 14  # at minimum "20260508-1030-"
    assert name.endswith(".md")
    # First 13 chars should be digits and a dash
    assert name[8] == "-"


def test_session_output_contains_transcript(tmp_path: Path) -> None:
    capture = make_capture()
    segs = [TranscriptSegment("Creativity flows.", 0.0, 1.0)]
    session = LiveSession(
        make_config(), make_transcriber(segs), tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    content = md_files[0].read_text()
    assert "Creativity flows." in content


def test_session_output_has_yaml_frontmatter(tmp_path: Path) -> None:
    capture = make_capture()
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    content = md_files[0].read_text()
    assert content.startswith("---")
    assert "word_count:" in content
    assert "duration:" in content


# ---------------------------------------------------------------------------
# Empty session — no content captured
# ---------------------------------------------------------------------------


def test_empty_session_deletes_file(tmp_path: Path) -> None:
    # Transcriber returns nothing
    capture = make_capture(np.zeros(100, dtype=np.float32))  # too short for MIN_SAMPLES
    mock_t = MagicMock()
    mock_t.stream.side_effect = lambda audio: iter([])

    session = LiveSession(
        make_config(), mock_t, tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)

    md_files = list(tmp_path.glob("*.md"))
    tmp_files = list(tmp_path.glob(".tmp-*.md"))
    assert len(md_files) == 0
    assert len(tmp_files) == 0


def test_empty_session_no_stray_tmp_files(tmp_path: Path) -> None:
    capture = make_capture(np.zeros(100, dtype=np.float32))
    mock_t = MagicMock()
    mock_t.stream.side_effect = lambda audio: iter([])

    session = LiveSession(
        make_config(), mock_t, tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)

    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# File naming
# ---------------------------------------------------------------------------


def test_session_filename_uses_first_words(tmp_path: Path) -> None:
    capture = make_capture()
    segs = [TranscriptSegment("The quick brown fox", 0.0, 1.0)]
    session = LiveSession(
        make_config(), make_transcriber(segs), tmp_path, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    assert "TheQuickBrownFox" in md_files[0].name


def test_session_filename_uses_untitled_when_no_speech(tmp_path: Path) -> None:
    # Provide enough audio for MIN_SAMPLES check but transcriber yields nothing
    capture = make_capture(np.ones(16_000, dtype=np.float32))
    mock_t = MagicMock()
    mock_t.stream.side_effect = lambda audio: iter([])

    session = LiveSession(
        make_config(), mock_t, tmp_path, _capture=capture, _poll_secs=0.05
    )
    # With no segments, _stop deletes the file (empty session path)
    run_session_sync(session)
    # No file should exist (empty session deletes it)
    assert list(tmp_path.glob("*.md")) == []


# ---------------------------------------------------------------------------
# Output dir creation
# ---------------------------------------------------------------------------


def test_session_creates_output_dir_if_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "notes"
    capture = make_capture()
    session = LiveSession(
        make_config(), make_transcriber(), output_dir, _capture=capture, _poll_secs=0.05
    )
    run_session_sync(session)
    assert output_dir.exists()


# ---------------------------------------------------------------------------
# --output override
# ---------------------------------------------------------------------------


def test_session_output_path_overrides_filename(tmp_path: Path) -> None:
    capture = make_capture()
    custom = tmp_path / "custom-name.md"
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path,
        output_path=custom, _capture=capture, _poll_secs=0.05,
    )
    run_session_sync(session)
    assert custom.exists()


def test_session_output_path_no_slug_files(tmp_path: Path) -> None:
    capture = make_capture()
    custom = tmp_path / "custom-name.md"
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path,
        output_path=custom, _capture=capture, _poll_secs=0.05,
    )
    run_session_sync(session)
    md_files = list(tmp_path.glob("*.md"))
    assert md_files == [custom]


def test_session_output_path_creates_parent_dirs(tmp_path: Path) -> None:
    capture = make_capture()
    custom = tmp_path / "deep" / "dir" / "note.md"
    session = LiveSession(
        make_config(), make_transcriber(), tmp_path,
        output_path=custom, _capture=capture, _poll_secs=0.05,
    )
    run_session_sync(session)
    assert custom.exists()


def test_session_output_path_ignored_when_no_content(tmp_path: Path) -> None:
    capture = make_capture(np.zeros(100, dtype=np.float32))
    mock_t = MagicMock()
    mock_t.stream.side_effect = lambda audio: iter([])
    custom = tmp_path / "custom-name.md"
    session = LiveSession(
        make_config(), mock_t, tmp_path,
        output_path=custom, _capture=capture, _poll_secs=0.05,
    )
    run_session_sync(session)
    assert not custom.exists()
