from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.output import OutputWriter, SessionMeta, _fmt_duration
from src.transcribe import TranscriptSegment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_meta(model: str = "base") -> SessionMeta:
    return SessionMeta(date=datetime(2026, 5, 8, 14, 30, 0), model=model)


def make_seg(text: str, start: float = 0.0, end: float = 1.0) -> TranscriptSegment:
    return TranscriptSegment(text=text, start_sec=start, end_sec=end)


def make_writer(tmp_path: Path, name: str = "out.md", model: str = "base") -> OutputWriter:
    return OutputWriter(path=tmp_path / name, meta=make_meta(model))


# ---------------------------------------------------------------------------
# _fmt_duration helper
# ---------------------------------------------------------------------------


def test_fmt_duration_zero() -> None:
    assert _fmt_duration(timedelta(0)) == "00:00:00"


def test_fmt_duration_minutes_and_seconds() -> None:
    assert _fmt_duration(timedelta(seconds=90)) == "00:01:30"


def test_fmt_duration_hours() -> None:
    assert _fmt_duration(timedelta(hours=1, minutes=2, seconds=3)) == "01:02:03"


# ---------------------------------------------------------------------------
# open() — frontmatter structure (AC-5, AC-8)
# ---------------------------------------------------------------------------


def test_open_creates_file(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    assert w._path.exists()


def test_open_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "out.md"
    w = OutputWriter(path=path, meta=make_meta())
    w.open()
    assert path.exists()


def test_open_writes_yaml_frontmatter(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    content = w._path.read_text()
    assert content.startswith("---\n")
    assert "aliases:" in content
    assert "title:" in content
    assert "date:" in content
    assert "model:" in content
    assert "duration:" in content
    assert "word_count:" in content
    assert "---\n" in content


def test_open_frontmatter_contains_date_and_model(tmp_path: Path) -> None:
    w = make_writer(tmp_path, model="small")
    w.open()
    content = w._path.read_text()
    assert "2026-05-08" in content
    assert "small" in content


def test_open_has_blank_line_after_closing_dashes(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    content = w._path.read_text()
    assert "---\n\n" in content


def test_open_placeholder_duration_is_zeros(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    content = w._path.read_text()
    assert '"00:00:00"' in content


def test_open_placeholder_word_count_is_zero(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    content = w._path.read_text()
    assert "word_count: 0" in content


# ---------------------------------------------------------------------------
# write_segment() — paragraph append (AC-9)
# ---------------------------------------------------------------------------


def test_write_segment_appends_text(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("Hello world."))
    content = w._path.read_text()
    assert "Hello world." in content


def test_write_segment_adds_blank_line_after_paragraph(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("First sentence."))
    content = w._path.read_text()
    assert "First sentence.\n\n" in content


def test_write_segment_strips_whitespace(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("  padded  "))
    content = w._path.read_text()
    assert "  padded  " not in content
    assert "padded" in content


def test_write_segment_multiple_segments_separated(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("First."))
    w.write_segment(make_seg("Second."))
    content = w._path.read_text()
    assert "First.\n\nSecond.\n\n" in content


def test_write_segment_before_open_raises(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    with pytest.raises(RuntimeError, match="open\\(\\)"):
        w.write_segment(make_seg("text"))


def test_write_segment_empty_text_is_ignored(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    before = w._path.read_text()
    w.write_segment(make_seg(""))
    after = w._path.read_text()
    assert before == after


# ---------------------------------------------------------------------------
# first_words property
# ---------------------------------------------------------------------------


def test_first_words_is_none_before_any_segment(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    assert w.first_words is None


def test_first_words_set_after_first_segment(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("Hello beautiful world today."))
    assert w.first_words is not None


def test_first_words_is_title_case_hyphenated(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("hello beautiful world today extra words"))
    assert w.first_words == "HelloBeautifulWorldToday"


def test_first_words_not_updated_by_second_segment(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("First segment text."))
    first = w.first_words
    w.write_segment(make_seg("Second segment text."))
    assert w.first_words == first


def test_first_words_short_text(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("Hi"))
    assert w.first_words == "Hi"


# ---------------------------------------------------------------------------
# finalize() — rewrites frontmatter (AC-6, AC-7)
# ---------------------------------------------------------------------------


def test_finalize_updates_duration(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("Some words here."))
    w.finalize(timedelta(minutes=2, seconds=30))
    content = w._path.read_text()
    assert '"02:30"' not in content  # wrong format
    assert '"00:02:30"' in content


def test_finalize_updates_word_count(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("one two three"))
    w.write_segment(make_seg("four five"))
    w.finalize(timedelta(seconds=10))
    content = w._path.read_text()
    assert "word_count: 5" in content


def test_finalize_removes_sentinels(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.finalize(timedelta(seconds=5))
    content = w._path.read_text()
    assert "__DURATION__" not in content
    assert "__WORD_COUNT__" not in content
    assert "__TITLE__" not in content


def test_finalize_sets_title_from_first_segment(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("the quick brown fox jumped"))
    w.finalize(timedelta(seconds=5))
    content = w._path.read_text()
    assert "title: The Quick Brown Fox" in content


def test_finalize_sets_aliases_from_first_segment(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("the quick brown fox jumped"))
    w.finalize(timedelta(seconds=5))
    content = w._path.read_text()
    assert "  - The Quick Brown Fox" in content


def test_finalize_title_defaults_to_untitled_when_no_segments(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.finalize(timedelta(seconds=0))
    content = w._path.read_text()
    assert "title: Untitled" in content
    assert "  - Untitled" in content


def test_finalize_zero_word_count_when_no_segments(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.finalize(timedelta(seconds=0))
    content = w._path.read_text()
    assert "word_count: 0" in content


def test_finalize_before_open_raises(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    with pytest.raises(RuntimeError, match="open\\(\\)"):
        w.finalize(timedelta(seconds=5))


def test_finalize_preserves_transcript_body(tmp_path: Path) -> None:
    w = make_writer(tmp_path)
    w.open()
    w.write_segment(make_seg("This is the transcript."))
    w.finalize(timedelta(seconds=10))
    content = w._path.read_text()
    assert "This is the transcript." in content
