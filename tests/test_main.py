from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from src.config import Config
from src.main import _positive_int, _resolve_diarization, build_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(diarize: bool = False, num_speakers: int | None = None) -> Config:
    return Config(
        model="base",
        hotkey="ctrl+space",
        output_dir=Path("/tmp/vn"),
        language="en",
        diarize=diarize,
        num_speakers=num_speakers,
    )


def parse(*argv: str) -> argparse.Namespace:
    return build_parser().parse_args(list(argv))


# ---------------------------------------------------------------------------
# _positive_int (Spec 005 AC-25)
# ---------------------------------------------------------------------------


def test_positive_int_accepts_one_and_above() -> None:
    assert _positive_int("1") == 1
    assert _positive_int("4") == 4


@pytest.mark.parametrize("value", ["0", "-1", "abc", "2.5", ""])
def test_positive_int_rejects_invalid(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="positive integer"):
        _positive_int(value)


def test_parser_rejects_zero_num_speakers() -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse("--file", "a.wav", "--num-speakers", "0")
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# _resolve_diarization (Spec 005 AC-4, AC-5, AC-21, AC-22, AC-24)
# ---------------------------------------------------------------------------


def test_disabled_by_default() -> None:
    enabled, n = _resolve_diarization(parse("--file", "a.wav"), make_config())
    assert enabled is False
    assert n is None


def test_diarize_flag_enables() -> None:
    enabled, n = _resolve_diarization(parse("--file", "a.wav", "--diarize"), make_config())
    assert enabled is True
    assert n is None


def test_num_speakers_flag_implies_diarize() -> None:
    enabled, n = _resolve_diarization(
        parse("--file", "a.wav", "--num-speakers", "3"), make_config()
    )
    assert enabled is True
    assert n == 3


def test_config_diarize_applies_to_file_mode() -> None:
    enabled, n = _resolve_diarization(parse("--file", "a.wav"), make_config(diarize=True))
    assert enabled is True
    assert n is None


def test_config_diarize_ignored_for_live_mode() -> None:
    enabled, _ = _resolve_diarization(parse(), make_config(diarize=True, num_speakers=2))
    assert enabled is False


def test_config_num_speakers_used_when_flag_absent() -> None:
    enabled, n = _resolve_diarization(
        parse("--file", "a.wav", "--diarize"), make_config(num_speakers=2)
    )
    assert enabled is True
    assert n == 2


def test_cli_num_speakers_overrides_config() -> None:
    _, n = _resolve_diarization(
        parse("--file", "a.wav", "--num-speakers", "4"), make_config(diarize=True, num_speakers=2)
    )
    assert n == 4


def test_cli_diarize_without_file_still_reports_enabled() -> None:
    # main() guards this case before calling _resolve_diarization; the resolver itself
    # reports the explicit request so the guard logic stays simple.
    enabled, _ = _resolve_diarization(parse("--diarize"), make_config())
    assert enabled is True
