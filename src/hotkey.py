from __future__ import annotations

from typing import Callable


def _to_pynput(hotkey: str) -> str:
    """Convert 'ctrl+space' → '<ctrl>+<space>' for pynput.GlobalHotKeys."""
    parts = hotkey.lower().replace(" ", "").split("+")
    return "+".join(f"<{p}>" if len(p) > 1 else p for p in parts)


class HotkeyListener:
    def __init__(self, hotkey: str, on_press: Callable[[], None]) -> None:
        self._pynput_hotkey = _to_pynput(hotkey)
        self._on_press = on_press
        self._listener = None

    def start(self) -> None:
        from pynput.keyboard import GlobalHotKeys

        self._listener = GlobalHotKeys({self._pynput_hotkey: self._on_press})
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join()
            self._listener = None
