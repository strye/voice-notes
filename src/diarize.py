from __future__ import annotations

import hashlib
import tarfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import numpy as np

from src.transcribe import TranscriptSegment, Word

if TYPE_CHECKING:
    import sherpa_onnx


DIARIZATION_CACHE_DIR = Path.home() / ".cache" / "voicenotes" / "diarization"


class DiarizationError(Exception):
    """Raised when diarization setup or processing fails."""


@dataclass(frozen=True)
class ModelSpec:
    filename: str
    url: str
    sha256: str
    size_bytes: int
    archive_member: str | None = None
    archive_sha256: str | None = None


SEGMENTATION_MODEL = ModelSpec(
    filename="pyannote-segmentation-3.0.onnx",
    url="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2",
    sha256="220ad67ca923bef2fa91f2390c786097bf305bceb5e261d4af67b38e938e1079",
    size_bytes=6_958_444,
    archive_member="sherpa-onnx-pyannote-segmentation-3-0/model.onnx",
    archive_sha256="24615ee884c897d9d2ba09bb4d30da6bb1b15e685065962db5b02e76e4996488",
)

EMBEDDING_MODEL = ModelSpec(
    filename="nemo_en_titanet_small.onnx",
    url="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/nemo_en_titanet_small.onnx",
    sha256="ad4a1802485d8b34c722d2a9d04249662f2ece5d28a7a039063ca22f515a789e",
    size_bytes=40_257_283,
)


@dataclass(frozen=True)
class DiarizationModels:
    segmentation: Path
    embedding: Path


@dataclass(frozen=True)
class SpeakerTurn:
    start_sec: float
    end_sec: float
    speaker: int  # 1-based, ordered by first appearance


def ensure_models(cache_dir: Path = DIARIZATION_CACHE_DIR) -> DiarizationModels:
    """Download any missing model, verify it, and return paths. Raises DiarizationError."""
    cache_dir.mkdir(parents=True, exist_ok=True)

    segmentation_path = _ensure_model(SEGMENTATION_MODEL, cache_dir)
    embedding_path = _ensure_model(EMBEDDING_MODEL, cache_dir)

    return DiarizationModels(segmentation=segmentation_path, embedding=embedding_path)


def _ensure_model(spec: ModelSpec, cache_dir: Path) -> Path:
    """Download and verify a single model if not already cached."""
    final_path = cache_dir / spec.filename

    # If already exists, reuse without network access
    if final_path.exists():
        return final_path

    part_path = cache_dir / f"{spec.filename}.part"

    try:
        # Download with progress
        with urllib.request.urlopen(spec.url) as response:
            downloaded = 0
            chunks: list[bytes] = []

            while True:
                chunk = response.read(1_048_576)  # 1 MB chunks
                if not chunk:
                    break
                chunks.append(chunk)
                downloaded += len(chunk)
                pct = int(downloaded * 100 / spec.size_bytes)
                size_mb = spec.size_bytes / 1_048_576
                print(f"\r  Downloading {spec.filename}: {pct}% of {size_mb:.1f} MB", end="", flush=True)

            print()  # newline after progress

            # Write to .part file
            part_path.write_bytes(b"".join(chunks))

        # Verify size
        actual_size = part_path.stat().st_size
        if actual_size != spec.size_bytes:
            part_path.unlink(missing_ok=True)
            raise DiarizationError(
                f"{spec.filename} failed verification (expected {spec.size_bytes} bytes, got {actual_size})"
            )

        # Handle archive extraction or direct file
        if spec.archive_member and spec.archive_sha256:
            # Verify archive checksum
            archive_hash = _sha256_file(part_path)
            if archive_hash != spec.archive_sha256:
                part_path.unlink(missing_ok=True)
                raise DiarizationError(
                    f"{spec.filename} failed verification (expected sha256 {spec.archive_sha256[:12]}…, got {archive_hash[:12]}…)"
                )

            # Extract member
            try:
                with tarfile.open(part_path, "r:bz2") as tar:
                    member_file = tar.extractfile(spec.archive_member)
                    if member_file is None:
                        raise DiarizationError(f"Archive member {spec.archive_member} not found")
                    final_path.write_bytes(member_file.read())
            except (tarfile.TarError, OSError) as exc:
                part_path.unlink(missing_ok=True)
                final_path.unlink(missing_ok=True)
                raise DiarizationError(f"failed to download {spec.filename}: {exc}")

            # Verify extracted file checksum
            extracted_hash = _sha256_file(final_path)
            if extracted_hash != spec.sha256:
                part_path.unlink(missing_ok=True)
                final_path.unlink(missing_ok=True)
                raise DiarizationError(
                    f"{spec.filename} failed verification (expected sha256 {spec.sha256[:12]}…, got {extracted_hash[:12]}…)"
                )

            # Delete archive
            part_path.unlink(missing_ok=True)
        else:
            # Direct file: verify checksum and rename
            file_hash = _sha256_file(part_path)
            if file_hash != spec.sha256:
                part_path.unlink(missing_ok=True)
                raise DiarizationError(
                    f"{spec.filename} failed verification (expected sha256 {spec.sha256[:12]}…, got {file_hash[:12]}…)"
                )
            part_path.rename(final_path)

        return final_path

    except urllib.error.URLError as exc:
        part_path.unlink(missing_ok=True)
        raise DiarizationError(f"failed to download {spec.filename}: {exc}")
    except OSError as exc:
        part_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise DiarizationError(f"failed to download {spec.filename}: {exc}")


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1_048_576)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


class Diarizer:
    """Run sherpa-onnx offline speaker diarization over 16 kHz mono float32 samples."""

    def __init__(
        self,
        models: DiarizationModels,
        *,
        num_speakers: int | None = None,
        threshold: float = 0.8,
        num_threads: int = 2,
    ) -> None:
        try:
            import sherpa_onnx
        except ImportError:
            raise DiarizationError(
                "sherpa-onnx is not installed — reinstall VoiceNotes: pip install -e ."
            )

        # Build configuration
        seg_cfg = sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(models.segmentation)
            ),
            num_threads=num_threads,
        )
        emb_cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(models.embedding),
            num_threads=num_threads,
        )
        clu_cfg = sherpa_onnx.FastClusteringConfig(
            num_clusters=num_speakers if num_speakers else -1,
            threshold=threshold,
        )
        cfg = sherpa_onnx.OfflineSpeakerDiarizationConfig(
            segmentation=seg_cfg,
            embedding=emb_cfg,
            clustering=clu_cfg,
            min_duration_on=0.3,
            min_duration_off=0.5,
        )

        self._sd: sherpa_onnx.OfflineSpeakerDiarization = sherpa_onnx.OfflineSpeakerDiarization(cfg)

    def run(
        self,
        samples: np.ndarray,
        progress: Callable[[int], None] | None = None,
    ) -> list[SpeakerTurn]:
        """Returns turns sorted by start time. Calls progress(pct) as chunks complete. Raises DiarizationError."""
        if len(samples) == 0:
            return []

        def _cb(processed: int, total: int) -> int:
            if progress and total:
                progress(int(processed * 100 / total))
            return 0

        try:
            result = self._sd.process(samples, _cb)
            # sort_by_start_time() returns the segment list; each has .start, .end, .speaker
            segments = list(result.sort_by_start_time())
        except Exception as exc:
            raise DiarizationError(f"speaker identification failed: {exc}") from exc

        # Relabel speakers by order of first appearance
        speaker_map: dict[int, int] = {}
        next_label = 1

        turns: list[SpeakerTurn] = []
        for seg in segments:
            raw_speaker = seg.speaker
            if raw_speaker not in speaker_map:
                speaker_map[raw_speaker] = next_label
                next_label += 1

            turns.append(
                SpeakerTurn(
                    start_sec=seg.start,
                    end_sec=seg.end,
                    speaker=speaker_map[raw_speaker],
                )
            )

        return turns


def assign_speakers(segment: TranscriptSegment, turns: list[SpeakerTurn]) -> list[TranscriptSegment]:
    """Return one or more segments, each with speaker set. Never returns an empty list for non-empty text."""
    if not turns:
        return [segment]

    if not segment.words:
        # Whole-segment overlap fallback
        speaker = _assign_speaker_to_interval(segment.start_sec, segment.end_sec, turns)
        return [
            TranscriptSegment(
                text=segment.text,
                start_sec=segment.start_sec,
                end_sec=segment.end_sec,
                speaker=speaker,
                words=[],
            )
        ]

    # Word-level assignment
    word_speakers: list[tuple[Word, int]] = []
    for word in segment.words:
        speaker = _assign_speaker_to_interval(word.start_sec, word.end_sec, turns)
        word_speakers.append((word, speaker))

    # Group consecutive same-speaker words
    result: list[TranscriptSegment] = []
    if not word_speakers:
        return [segment]

    current_speaker = word_speakers[0][1]
    current_words: list[Word] = [word_speakers[0][0]]

    for word, speaker in word_speakers[1:]:
        if speaker == current_speaker:
            current_words.append(word)
        else:
            # Emit current group
            text = " ".join(w.text.strip() for w in current_words)
            result.append(
                TranscriptSegment(
                    text=text,
                    start_sec=current_words[0].start_sec,
                    end_sec=current_words[-1].end_sec,
                    speaker=current_speaker,
                    words=current_words,
                )
            )
            # Start new group
            current_speaker = speaker
            current_words = [word]

    # Emit final group
    text = " ".join(w.text.strip() for w in current_words)
    result.append(
        TranscriptSegment(
            text=text,
            start_sec=current_words[0].start_sec,
            end_sec=current_words[-1].end_sec,
            speaker=current_speaker,
            words=current_words,
        )
    )

    return result


def _assign_speaker_to_interval(start_sec: float, end_sec: float, turns: list[SpeakerTurn]) -> int:
    """Assign speaker to an interval using overlap or nearest-boundary fallback."""
    best_speaker = turns[0].speaker
    best_overlap = 0.0

    # Find turn with greatest overlap
    for turn in turns:
        overlap_start = max(start_sec, turn.start_sec)
        overlap_end = min(end_sec, turn.end_sec)
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = turn.speaker

    # If no overlap, use nearest boundary
    if best_overlap == 0.0:
        midpoint = (start_sec + end_sec) / 2
        best_distance = float("inf")

        for turn in turns:
            # Distance from midpoint to nearest turn edge
            if midpoint < turn.start_sec:
                distance = turn.start_sec - midpoint
            elif midpoint > turn.end_sec:
                distance = midpoint - turn.end_sec
            else:
                distance = 0.0  # midpoint is inside the turn

            if distance < best_distance:
                best_distance = distance
                best_speaker = turn.speaker

    return best_speaker
