from __future__ import annotations

import threading
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from src.capture import AudioCapture, CaptureError
from src.hotkey import HotkeyListener, _to_pynput


# ---------------------------------------------------------------------------
# _to_pynput conversion
# ---------------------------------------------------------------------------


def test_single_modifier_and_char() -> None:
    assert _to_pynput("ctrl+a") == "<ctrl>+a"


def test_multi_modifier() -> None:
    assert _to_pynput("ctrl+shift+space") == "<ctrl>+<shift>+<space>"


def test_space_wrapped() -> None:
    assert _to_pynput("ctrl+space") == "<ctrl>+<space>"


def test_cmd_converted() -> None:
    assert _to_pynput("cmd+shift+space") == "<cmd>+<shift>+<space>"


def test_uppercase_normalised() -> None:
    assert _to_pynput("CTRL+SPACE") == "<ctrl>+<space>"


def test_single_char_not_wrapped() -> None:
    result = _to_pynput("ctrl+a")
    assert result.endswith("+a")
    assert "<a>" not in result


def test_spaces_in_string_stripped() -> None:
    assert _to_pynput("ctrl + space") == "<ctrl>+<space>"


# ---------------------------------------------------------------------------
# HotkeyListener
# ---------------------------------------------------------------------------


def test_hotkey_listener_stores_converted_hotkey() -> None:
    cb = MagicMock()
    listener = HotkeyListener("ctrl+space", cb)
    assert listener._pynput_hotkey == "<ctrl>+<space>"


def _pynput_modules(ghk_instance: MagicMock) -> dict:
    """Build sys.modules stubs for pynput so lazy imports inside hotkey.py work."""
    mock_keyboard = MagicMock()
    mock_keyboard.GlobalHotKeys.return_value = ghk_instance
    mock_pynput = MagicMock()
    mock_pynput.keyboard = mock_keyboard
    return {
        "pynput": mock_pynput,
        "pynput.keyboard": mock_keyboard,
    }


def test_hotkey_listener_start_creates_global_hot_keys() -> None:
    cb = MagicMock()
    listener = HotkeyListener("ctrl+space", cb)
    mock_ghk = MagicMock()

    with patch.dict("sys.modules", _pynput_modules(mock_ghk)):
        import pynput.keyboard as _kb  # noqa: F401 – force cache update
        listener.start()

    import sys as _sys
    mock_keyboard = _sys.modules.get("pynput.keyboard") or MagicMock()
    # Verify the listener was wired up
    assert listener._listener is not None


def test_hotkey_listener_stop_calls_stop_and_join() -> None:
    cb = MagicMock()
    listener = HotkeyListener("ctrl+space", cb)
    mock_ghk = MagicMock()

    with patch.dict("sys.modules", _pynput_modules(mock_ghk)):
        listener.start()
        listener.stop()

    mock_ghk.stop.assert_called_once()
    mock_ghk.join.assert_called_once()


def test_hotkey_listener_stop_is_idempotent() -> None:
    cb = MagicMock()
    listener = HotkeyListener("ctrl+space", cb)
    # stop() before start() should not raise
    listener.stop()


# ---------------------------------------------------------------------------
# AudioCapture — buffer accumulation
# ---------------------------------------------------------------------------


def make_mock_stream() -> MagicMock:
    stream = MagicMock()
    stream.__enter__ = lambda s: s
    stream.__exit__ = MagicMock(return_value=False)
    return stream


def test_audio_capture_snapshot_empty_before_start() -> None:
    cap = AudioCapture()
    result = cap.snapshot()
    assert result.dtype == np.float32
    assert len(result) == 0


def test_audio_capture_callback_accumulates_samples() -> None:
    cap = AudioCapture()
    cap._chunks = []

    chunk = np.ones((100, 1), dtype=np.float32)
    cap._callback(chunk, 100, None, None)
    cap._callback(chunk, 100, None, None)

    result = cap.snapshot()
    assert len(result) == 200
    assert result.dtype == np.float32


def test_audio_capture_callback_takes_first_channel() -> None:
    cap = AudioCapture()
    cap._chunks = []

    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    cap._callback(data, 2, None, None)

    result = cap.snapshot()
    np.testing.assert_array_equal(result, [1.0, 3.0])


def test_audio_capture_snapshot_thread_safe() -> None:
    cap = AudioCapture()
    cap._chunks = []

    errors: list[Exception] = []

    def writer() -> None:
        for _ in range(50):
            chunk = np.ones((10, 1), dtype=np.float32)
            cap._callback(chunk, 10, None, None)

    def reader() -> None:
        for _ in range(50):
            try:
                cap.snapshot()
            except Exception as exc:
                errors.append(exc)

    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert not errors


def test_audio_capture_stop_returns_all_samples() -> None:
    cap = AudioCapture()
    chunk = np.ones((100, 1), dtype=np.float32)
    cap._chunks = [chunk[:, 0]]

    mock_stream = make_mock_stream()
    cap._stream = mock_stream

    result = cap.stop()
    assert len(result) == 100
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()


def test_audio_capture_stop_clears_stream_reference() -> None:
    cap = AudioCapture()
    cap._stream = make_mock_stream()
    cap.stop()
    assert cap._stream is None


def _sounddevice_modules(stream_instance: MagicMock | None = None, raises: Exception | None = None) -> dict:
    """Build sys.modules stub for sounddevice."""
    mock_sd = MagicMock()
    if raises is not None:
        mock_sd.InputStream.side_effect = raises
    elif stream_instance is not None:
        mock_sd.InputStream.return_value = stream_instance
    return {"sounddevice": mock_sd}


def test_audio_capture_start_raises_capture_error_on_port_audio_error() -> None:
    cap = AudioCapture()
    with patch.dict("sys.modules", _sounddevice_modules(raises=Exception("PortAudio error"))):
        with pytest.raises(CaptureError, match="Cannot access microphone"):
            cap.start()


def test_audio_capture_start_resets_buffer() -> None:
    cap = AudioCapture()
    cap._chunks = [np.ones(10, dtype=np.float32)]  # stale data

    mock_stream = make_mock_stream()
    with patch.dict("sys.modules", _sounddevice_modules(stream_instance=mock_stream)):
        cap.start()

    assert cap._chunks == []
