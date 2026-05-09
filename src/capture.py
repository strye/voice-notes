from __future__ import annotations

import threading

import numpy as np


class CaptureError(Exception):
    pass


class AudioCapture:
    _SAMPLE_RATE = 16_000

    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream = None

    def start(self) -> None:
        import sounddevice as sd

        self._chunks = []
        try:
            self._stream = sd.InputStream(
                samplerate=self._SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:
            raise CaptureError(f"Cannot access microphone: {exc}") from exc

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: object,
        status: object,
    ) -> None:
        with self._lock:
            self._chunks.append(indata[:, 0].copy())

    def snapshot(self) -> np.ndarray:
        """Return a copy of all accumulated samples without stopping capture."""
        with self._lock:
            if not self._chunks:
                return np.array([], dtype=np.float32)
            return np.concatenate(self._chunks)

    def stop(self) -> np.ndarray:
        """Stop capture and return all accumulated samples as float32 16 kHz mono."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        return self.snapshot()
