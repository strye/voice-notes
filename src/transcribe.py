from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator

import numpy as np

if TYPE_CHECKING:
    from faster_whisper import WhisperModel as _WhisperModel


@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float


class Transcriber:
    def __init__(self, model_path: str, language: str = "en") -> None:
        from faster_whisper import WhisperModel

        self._model: _WhisperModel = WhisperModel(
            model_path,
            device="cpu",
            compute_type="int8",
        )
        self._language = language

    def stream(
        self,
        audio: np.ndarray,
        sample_rate: int = 16_000,
    ) -> Generator[TranscriptSegment, None, None]:
        """Yield one TranscriptSegment per VAD-detected speech region. Skips empty segments."""
        segments, _info = self._model.transcribe(
            audio,
            language=self._language,
            vad_filter=True,
        )
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            yield TranscriptSegment(
                text=text,
                start_sec=seg.start,
                end_sec=seg.end,
            )
