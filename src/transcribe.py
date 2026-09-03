from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generator

import numpy as np

if TYPE_CHECKING:
    from faster_whisper import WhisperModel as _WhisperModel


@dataclass
class Word:
    text: str
    start_sec: float
    end_sec: float


@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float
    speaker: int | None = None  # 1-based label, set only when diarization ran
    words: list[Word] = field(default_factory=list)  # populated only with word_timestamps=True


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
        *,
        word_timestamps: bool = False,
    ) -> Generator[TranscriptSegment, None, None]:
        """Yield one TranscriptSegment per VAD-detected speech region. Skips empty segments.

        With word_timestamps=True each segment also carries per-word timing in `words`.
        """
        segments, _info = self._model.transcribe(
            audio,
            language=self._language,
            vad_filter=True,
            word_timestamps=word_timestamps,
        )
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            words: list[Word] = []
            if word_timestamps:
                for w in getattr(seg, "words", None) or []:
                    wtext = w.word.strip()
                    if wtext:
                        words.append(Word(text=wtext, start_sec=w.start, end_sec=w.end))
            yield TranscriptSegment(
                text=text,
                start_sec=seg.start,
                end_sec=seg.end,
                words=words,
            )
