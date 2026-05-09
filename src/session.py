from __future__ import annotations

import threading
from datetime import datetime, timedelta
from pathlib import Path

from src.capture import AudioCapture, CaptureError
from src.config import Config
from src.hotkey import HotkeyListener
from src.output import OutputWriter, SessionMeta
from src.transcribe import Transcriber

_SAMPLE_RATE = 16_000
_MIN_SAMPLES = _SAMPLE_RATE // 2  # 0.5 s minimum before attempting transcription


class LiveSession:
    def __init__(
        self,
        config: Config,
        transcriber: Transcriber,
        output_dir: Path,
        *,
        output_path: Path | None = None,
        _capture: AudioCapture | None = None,
        _poll_secs: float = 5.0,
    ) -> None:
        self._config = config
        self._transcriber = transcriber
        self._output_dir = output_dir
        self._output_path = output_path
        self._capture = _capture or AudioCapture()
        self._poll_secs = _poll_secs

        self._recording = False
        self._done = threading.Event()
        self._stop_streaming = threading.Event()
        self._writer: OutputWriter | None = None
        self._tmp_path: Path | None = None
        self._start_time: datetime | None = None
        self._stream_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Hotkey toggle
    # ------------------------------------------------------------------

    def _on_hotkey(self) -> None:
        if not self._recording:
            self._start()
        else:
            self._stop()

    # ------------------------------------------------------------------
    # Session start
    # ------------------------------------------------------------------

    def _start(self) -> None:
        self._recording = True
        self._start_time = datetime.now()

        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_path = (
            self._output_dir
            / f".tmp-{self._start_time.strftime('%Y%m%d%H%M%S%f')}.md"
        )

        meta = SessionMeta(date=self._start_time, model=self._config.model)
        self._writer = OutputWriter(self._tmp_path, meta)
        self._writer.open()

        self._capture.start()

        self._stop_streaming.clear()
        self._stream_thread = threading.Thread(
            target=self._stream_loop, daemon=True, name="voicenotes-stream"
        )
        self._stream_thread.start()

        print("Recording… (press hotkey to stop)")

    # ------------------------------------------------------------------
    # Session stop
    # ------------------------------------------------------------------

    def _stop(self) -> None:
        self._recording = False

        # Signal stream thread; it does one final drain then exits
        self._stop_streaming.set()
        if self._stream_thread is not None:
            self._stream_thread.join()

        self._capture.stop()

        elapsed = datetime.now() - self._start_time  # type: ignore[operator]
        self._writer.finalize(elapsed)  # type: ignore[union-attr]

        if self._writer.first_words is None:  # type: ignore[union-attr]
            self._tmp_path.unlink(missing_ok=True)  # type: ignore[union-attr]
            print("No content captured.")
        else:
            if self._output_path is not None:
                final_path = self._output_path
            else:
                slug = self._writer.first_words  # type: ignore[union-attr]
                dt = self._start_time  # type: ignore[assignment]
                final_name = f"{dt.strftime('%Y%m%d-%H%M')}-{slug}.md"
                final_path = self._output_dir / final_name
            final_path.parent.mkdir(parents=True, exist_ok=True)
            self._tmp_path.rename(final_path)  # type: ignore[union-attr]
            print(f"Saved: {final_path}")

        self._done.set()

    # ------------------------------------------------------------------
    # Streaming loop (background thread)
    # ------------------------------------------------------------------

    def _stream_loop(self) -> None:
        last_processed = 0

        while True:
            stopping = self._stop_streaming.wait(timeout=self._poll_secs)

            snapshot = self._capture.snapshot()
            new_samples = snapshot[last_processed:]

            if len(new_samples) >= _MIN_SAMPLES:
                try:
                    for seg in self._transcriber.stream(new_samples):
                        self._writer.write_segment(seg)  # type: ignore[union-attr]
                        print(seg.text)
                except Exception as exc:
                    print(f"[transcription error: {exc}]")
                last_processed = len(snapshot)

            if stopping:
                break

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Block until start+stop hotkey cycle completes and file is written."""
        listener = HotkeyListener(self._config.hotkey, self._on_hotkey)
        try:
            listener.start()
        except Exception as exc:
            raise CaptureError(
                f"Hotkey unavailable — try a different combination ({exc})"
            ) from exc

        try:
            self._done.wait()
        finally:
            listener.stop()
