from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.transcribe import TranscriptSegment, Transcriber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_seg(text: str, start: float = 0.0, end: float = 1.0) -> SimpleNamespace:
    """Build a fake faster-whisper segment."""
    return SimpleNamespace(text=text, start=start, end=end)


def make_transcriber(segments: list, language: str = "en") -> Transcriber:
    """Construct a Transcriber with a mocked WhisperModel."""
    with patch("faster_whisper.WhisperModel") as MockModel:
        instance = MockModel.return_value
        instance.transcribe.return_value = (iter(segments), SimpleNamespace())
        t = Transcriber.__new__(Transcriber)
        t._model = instance
        t._language = language
    return t


# ---------------------------------------------------------------------------
# TranscriptSegment dataclass
# ---------------------------------------------------------------------------


def test_segment_stores_fields() -> None:
    seg = TranscriptSegment(text="hello", start_sec=0.5, end_sec=2.0)
    assert seg.text == "hello"
    assert seg.start_sec == 0.5
    assert seg.end_sec == 2.0


# ---------------------------------------------------------------------------
# Transcriber construction
# ---------------------------------------------------------------------------


def test_transcriber_constructs_whisper_model() -> None:
    with patch("faster_whisper.WhisperModel") as MockModel:
        MockModel.return_value.transcribe.return_value = (iter([]), SimpleNamespace())
        t = Transcriber("fake/path")
        MockModel.assert_called_once_with("fake/path", device="cpu", compute_type="int8")


def test_transcriber_stores_language() -> None:
    with patch("faster_whisper.WhisperModel") as MockModel:
        MockModel.return_value.transcribe.return_value = (iter([]), SimpleNamespace())
        t = Transcriber("fake/path", language="fr")
        assert t._language == "fr"


# ---------------------------------------------------------------------------
# stream() — normal segments
# ---------------------------------------------------------------------------


def test_stream_yields_segment_for_each_nonempty_result() -> None:
    t = make_transcriber([
        make_seg("Hello world", 0.0, 1.5),
        make_seg("Second sentence.", 2.0, 3.5),
    ])
    audio = np.zeros(16_000, dtype=np.float32)
    results = list(t.stream(audio))
    assert len(results) == 2
    assert results[0].text == "Hello world"
    assert results[1].text == "Second sentence."


def test_stream_returns_correct_timestamps() -> None:
    t = make_transcriber([make_seg("Test", 1.0, 2.5)])
    audio = np.zeros(16_000, dtype=np.float32)
    results = list(t.stream(audio))
    assert results[0].start_sec == 1.0
    assert results[0].end_sec == 2.5


def test_stream_strips_leading_trailing_whitespace() -> None:
    t = make_transcriber([make_seg("  padded text  ")])
    audio = np.zeros(16_000, dtype=np.float32)
    results = list(t.stream(audio))
    assert results[0].text == "padded text"


# ---------------------------------------------------------------------------
# stream() — empty segment filtering (AC-4)
# ---------------------------------------------------------------------------


def test_stream_discards_empty_text_segments() -> None:
    t = make_transcriber([
        make_seg(""),
        make_seg("   "),
        make_seg("Real content."),
    ])
    audio = np.zeros(16_000, dtype=np.float32)
    results = list(t.stream(audio))
    assert len(results) == 1
    assert results[0].text == "Real content."


def test_stream_yields_nothing_for_all_empty_segments() -> None:
    t = make_transcriber([make_seg(""), make_seg("  \n  ")])
    audio = np.zeros(16_000, dtype=np.float32)
    assert list(t.stream(audio)) == []


def test_stream_yields_nothing_when_no_segments() -> None:
    t = make_transcriber([])
    audio = np.zeros(16_000, dtype=np.float32)
    assert list(t.stream(audio)) == []


# ---------------------------------------------------------------------------
# stream() — VAD and language passed through (AC-1)
# ---------------------------------------------------------------------------


def test_stream_calls_transcribe_with_vad_filter() -> None:
    t = make_transcriber([])
    t._model.transcribe.return_value = (iter([]), SimpleNamespace())
    audio = np.zeros(16_000, dtype=np.float32)
    list(t.stream(audio))
    _, kwargs = t._model.transcribe.call_args
    assert kwargs.get("vad_filter") is True


def test_stream_passes_language_to_transcribe() -> None:
    t = make_transcriber([], language="de")
    t._model.transcribe.return_value = (iter([]), SimpleNamespace())
    audio = np.zeros(16_000, dtype=np.float32)
    list(t.stream(audio))
    _, kwargs = t._model.transcribe.call_args
    assert kwargs.get("language") == "de"


# ---------------------------------------------------------------------------
# stream() — reusability (AC-3)
# ---------------------------------------------------------------------------


def test_stream_is_reusable_across_calls() -> None:
    t = make_transcriber([])
    audio = np.zeros(16_000, dtype=np.float32)

    t._model.transcribe.return_value = (iter([make_seg("First call.")]), SimpleNamespace())
    r1 = list(t.stream(audio))

    t._model.transcribe.return_value = (iter([make_seg("Second call.")]), SimpleNamespace())
    r2 = list(t.stream(audio))

    assert r1[0].text == "First call."
    assert r2[0].text == "Second call."


# ---------------------------------------------------------------------------
# stream() yields TranscriptSegment instances
# ---------------------------------------------------------------------------


def test_stream_yields_transcript_segment_instances() -> None:
    t = make_transcriber([make_seg("Hello.")])
    audio = np.zeros(16_000, dtype=np.float32)
    results = list(t.stream(audio))
    assert all(isinstance(r, TranscriptSegment) for r in results)
