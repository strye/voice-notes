from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.file_input import (
    SUPPORTED_EXTENSIONS,
    DecodedAudio,
    FileInputError,
    FileSession,
    decode_audio_file,
    validate_audio_file,
)


# ---------------------------------------------------------------------------
# validate_audio_file
# ---------------------------------------------------------------------------


def test_validate_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileInputError, match="File not found"):
        validate_audio_file(tmp_path / "missing.wav")


def test_validate_missing_file_includes_path(tmp_path: Path) -> None:
    missing = tmp_path / "audio.wav"
    with pytest.raises(FileInputError, match=str(missing)):
        validate_audio_file(missing)


def test_validate_unsupported_extension_raises(tmp_path: Path) -> None:
    bad = tmp_path / "audio.aup3"
    bad.touch()
    with pytest.raises(FileInputError, match="Unsupported format"):
        validate_audio_file(bad)


def test_validate_unsupported_extension_lists_formats(tmp_path: Path) -> None:
    bad = tmp_path / "audio.ogg"
    bad.touch()
    with pytest.raises(FileInputError) as exc_info:
        validate_audio_file(bad)
    msg = str(exc_info.value)
    assert ".wav" in msg and ".mp3" in msg


def test_validate_wav_returns_resolved_path(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.touch()
    result = validate_audio_file(f)
    assert result == f.resolve()


def test_validate_mp3_returns_resolved_path(tmp_path: Path) -> None:
    f = tmp_path / "audio.mp3"
    f.touch()
    result = validate_audio_file(f)
    assert result == f.resolve()


def test_validate_extension_case_insensitive(tmp_path: Path) -> None:
    f = tmp_path / "audio.WAV"
    f.touch()
    result = validate_audio_file(f)
    assert result.exists()


# ---------------------------------------------------------------------------
# decode_audio_file — happy path (mocked subprocess)
# ---------------------------------------------------------------------------


def make_ffmpeg_result(n_samples: int = 16_000, value: int = 0) -> MagicMock:
    """Return a mock subprocess.CompletedProcess with raw int16 PCM bytes."""
    raw = np.full(n_samples, value, dtype=np.int16).tobytes()
    result = MagicMock()
    result.stdout = raw
    return result


def test_decode_returns_decoded_audio(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result()):
        result = decode_audio_file(f)

    assert isinstance(result, DecodedAudio)


def test_decode_samples_are_float32(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result()):
        result = decode_audio_file(f)

    assert result.samples.dtype == np.float32


def test_decode_samples_normalized(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)
    raw = np.array([32767], dtype=np.int16).tobytes()
    mock_result = MagicMock()
    mock_result.stdout = raw

    with patch("subprocess.run", return_value=mock_result):
        result = decode_audio_file(f)

    assert result.samples[0] == pytest.approx(32767 / 32768.0)


def test_decode_duration_extracted(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result(n_samples=16_000)):
        result = decode_audio_file(f)

    assert result.duration_sec == pytest.approx(1.0)


def test_decode_created_at_is_datetime(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result()):
        result = decode_audio_file(f)

    assert isinstance(result.created_at, datetime)


def test_decode_calls_ffmpeg_with_mono(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result()) as mock_run:
        decode_audio_file(f)

    args = mock_run.call_args[0][0]
    assert "-ac" in args
    assert args[args.index("-ac") + 1] == "1"


def test_decode_calls_ffmpeg_with_16khz(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", return_value=make_ffmpeg_result()) as mock_run:
        decode_audio_file(f)

    args = mock_run.call_args[0][0]
    assert "-ar" in args
    assert args[args.index("-ar") + 1] == "16000"


# ---------------------------------------------------------------------------
# decode_audio_file — error handling
# ---------------------------------------------------------------------------


def test_decode_ffmpeg_missing_raises(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
        with pytest.raises(FileInputError, match="ffmpeg not found"):
            decode_audio_file(f)


def test_decode_ffmpeg_error_wrapped(tmp_path: Path) -> None:
    f = tmp_path / "audio.wav"
    f.write_bytes(b"\x00" * 100)

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
        with pytest.raises(FileInputError, match="Failed to decode"):
            decode_audio_file(f)


# ---------------------------------------------------------------------------
# FileSession.run — mocked dependencies
# ---------------------------------------------------------------------------


def make_transcriber_mock(segments=None):
    from src.transcribe import TranscriptSegment

    mock = MagicMock()
    segs = segments or [
        TranscriptSegment(text="Hello world.", start_sec=0.5, end_sec=2.0)
    ]
    mock.stream.return_value = iter(segs)
    return mock


def make_config_mock(model: str = "base", output_dir: str = "") -> MagicMock:
    cfg = MagicMock()
    cfg.model = model
    return cfg


def test_file_session_creates_output_file(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"

    cfg = make_config_mock()
    transcriber = make_transcriber_mock()

    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir).run(audio)

    md_files = list(output_dir.glob("*.md"))
    assert len(md_files) == 1


def test_file_session_output_named_with_first_words(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"

    from src.transcribe import TranscriptSegment
    cfg = make_config_mock()
    transcriber = make_transcriber_mock([
        TranscriptSegment(text="Hello beautiful world", start_sec=0.0, end_sec=1.0)
    ])

    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 30, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir).run(audio)

    md_files = list(output_dir.glob("*.md"))
    assert md_files[0].name.startswith("20260508-1030-")


def test_file_session_no_speech_keeps_file(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"

    cfg = make_config_mock()
    mock_t = MagicMock()
    mock_t.stream.return_value = iter([])  # no segments

    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 9, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, mock_t, output_dir).run(audio)

    # File must exist (frontmatter-only), named with "untitled"
    md_files = list(output_dir.glob("*.md"))
    assert len(md_files) == 1
    assert "untitled" in md_files[0].name


def test_file_session_no_speech_file_has_frontmatter(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"

    cfg = make_config_mock()
    mock_t = MagicMock()
    mock_t.stream.return_value = iter([])

    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=2.0,
        created_at=datetime(2026, 5, 8, 9, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, mock_t, output_dir).run(audio)

    md_files = list(output_dir.glob("*.md"))
    content = md_files[0].read_text()
    assert "---" in content
    assert "word_count: 0" in content


def test_file_session_output_contains_transcript(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"

    from src.transcribe import TranscriptSegment
    cfg = make_config_mock()
    transcriber = make_transcriber_mock([
        TranscriptSegment(text="Ideas flow freely.", start_sec=0.0, end_sec=1.5)
    ])

    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=2.0,
        created_at=datetime(2026, 5, 8, 8, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir).run(audio)

    md_files = list(output_dir.glob("*.md"))
    content = md_files[0].read_text()
    assert "Ideas flow freely." in content


# ---------------------------------------------------------------------------
# FileSession --output override
# ---------------------------------------------------------------------------


def test_file_session_output_path_overrides_filename(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"
    custom = tmp_path / "my-note.md"

    cfg = make_config_mock()
    transcriber = make_transcriber_mock()
    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir, output_path=custom).run(audio)

    assert custom.exists()


def test_file_session_output_path_no_slug_file(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"
    custom = tmp_path / "my-note.md"

    cfg = make_config_mock()
    transcriber = make_transcriber_mock()
    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir, output_path=custom).run(audio)

    assert list(output_dir.glob("*.md")) == []


def test_file_session_output_path_creates_parent_dirs(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"
    custom = tmp_path / "deep" / "dir" / "note.md"

    cfg = make_config_mock()
    transcriber = make_transcriber_mock()
    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, transcriber, output_dir, output_path=custom).run(audio)

    assert custom.exists()


def test_file_session_output_path_no_speech_uses_custom_path(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "out"
    custom = tmp_path / "my-note.md"

    cfg = make_config_mock()
    mock_t = MagicMock()
    mock_t.stream.return_value = iter([])
    decoded = DecodedAudio(
        samples=np.zeros(16_000, dtype=np.float32),
        duration_sec=1.0,
        created_at=datetime(2026, 5, 8, 10, 0, 0),
    )

    with patch("src.file_input.validate_audio_file", return_value=audio), \
         patch("src.file_input.decode_audio_file", return_value=decoded):
        FileSession(cfg, mock_t, output_dir, output_path=custom).run(audio)

    assert custom.exists()
