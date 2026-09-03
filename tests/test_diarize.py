from __future__ import annotations

import hashlib
import tarfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch
from urllib.error import URLError

import numpy as np
import pytest

from src.diarize import (
    DIARIZATION_CACHE_DIR,
    EMBEDDING_MODEL,
    SEGMENTATION_MODEL,
    Diarizer,
    DiarizationError,
    DiarizationModels,
    ModelSpec,
    SpeakerTurn,
    assign_speakers,
    ensure_models,
)
from src.transcribe import TranscriptSegment, Word


# ---------------------------------------------------------------------------
# Model downloader tests
# ---------------------------------------------------------------------------


def test_ensure_models_cached_file_skips_network(tmp_path: Path) -> None:
    """If both models already exist, urlopen is never called."""
    cache = tmp_path / "cache"
    cache.mkdir()

    # Create fake existing files
    (cache / SEGMENTATION_MODEL.filename).write_text("fake seg model")
    (cache / EMBEDDING_MODEL.filename).write_text("fake emb model")

    with patch("src.diarize.urllib.request.urlopen") as mock_urlopen:
        result = ensure_models(cache_dir=cache)

    mock_urlopen.assert_not_called()
    assert result.segmentation == cache / SEGMENTATION_MODEL.filename
    assert result.embedding == cache / EMBEDDING_MODEL.filename


def test_download_progress_contains_percentage_and_mb(tmp_path: Path, capsys) -> None:
    """Progress output includes percentage and MB during download."""
    cache = tmp_path / "cache"
    cache.mkdir()

    # Create a small fake model spec
    fake_content = b"x" * 5_000_000  # 5 MB
    fake_hash = hashlib.sha256(fake_content).hexdigest()

    spec = ModelSpec(
        filename="test.onnx",
        url="http://example.com/test.onnx",
        sha256=fake_hash,
        size_bytes=len(fake_content),
    )

    # Mock urlopen to return chunked content
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    chunks = [fake_content[i : i + 1_048_576] for i in range(0, len(fake_content), 1_048_576)]
    mock_response.read = MagicMock(side_effect=chunks + [b""])

    with patch("src.diarize.urllib.request.urlopen", return_value=mock_response):
        from src.diarize import _ensure_model

        _ensure_model(spec, cache)

    captured = capsys.readouterr()
    assert "%" in captured.out
    assert "MB" in captured.out
    assert spec.filename in captured.out


def test_download_size_mismatch_removes_part_and_raises(tmp_path: Path) -> None:
    """If downloaded size doesn't match expected, .part is removed and DiarizationError raised."""
    cache = tmp_path / "cache"
    cache.mkdir()

    fake_content = b"wrong size"
    spec = ModelSpec(
        filename="test.onnx",
        url="http://example.com/test.onnx",
        sha256="abc123",
        size_bytes=999_999,  # doesn't match content
    )

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read = MagicMock(side_effect=[fake_content, b""])

    with patch("src.diarize.urllib.request.urlopen", return_value=mock_response):
        from src.diarize import _ensure_model

        with pytest.raises(DiarizationError, match="failed verification.*expected.*bytes"):
            _ensure_model(spec, cache)

    assert not (cache / f"{spec.filename}.part").exists()


def test_download_checksum_mismatch_removes_file_and_raises(tmp_path: Path) -> None:
    """If SHA-256 doesn't match, file is removed and DiarizationError raised."""
    cache = tmp_path / "cache"
    cache.mkdir()

    fake_content = b"x" * 1000
    actual_hash = hashlib.sha256(fake_content).hexdigest()
    wrong_hash = "0" * 64

    spec = ModelSpec(
        filename="test.onnx",
        url="http://example.com/test.onnx",
        sha256=wrong_hash,
        size_bytes=len(fake_content),
    )

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read = MagicMock(side_effect=[fake_content, b""])

    with patch("src.diarize.urllib.request.urlopen", return_value=mock_response):
        from src.diarize import _ensure_model

        with pytest.raises(DiarizationError, match="failed verification.*sha256"):
            _ensure_model(spec, cache)

    assert not (cache / spec.filename).exists()
    assert not (cache / f"{spec.filename}.part").exists()


def test_download_urlerror_wrapped_as_diarization_error(tmp_path: Path) -> None:
    """URLError is wrapped in DiarizationError with 'failed to download' message."""
    cache = tmp_path / "cache"
    cache.mkdir()

    spec = ModelSpec(
        filename="test.onnx",
        url="http://example.com/test.onnx",
        sha256="abc",
        size_bytes=1000,
    )

    with patch("src.diarize.urllib.request.urlopen", side_effect=URLError("network error")):
        from src.diarize import _ensure_model

        with pytest.raises(DiarizationError, match="failed to download test.onnx"):
            _ensure_model(spec, cache)


def test_archive_extraction_and_verification(tmp_path: Path) -> None:
    """Archive is extracted, member verified, and archive deleted."""
    cache = tmp_path / "cache"
    cache.mkdir()

    # Create a real .tar.bz2 with nested path
    member_content = b"model content here"
    member_path = "nested/dir/model.onnx"
    member_hash = hashlib.sha256(member_content).hexdigest()

    # Build archive in memory
    archive_buf = BytesIO()
    with tarfile.open(fileobj=archive_buf, mode="w:bz2") as tar:
        info = tarfile.TarInfo(name=member_path)
        info.size = len(member_content)
        tar.addfile(info, BytesIO(member_content))

    archive_bytes = archive_buf.getvalue()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()

    spec = ModelSpec(
        filename="extracted.onnx",
        url="http://example.com/archive.tar.bz2",
        sha256=member_hash,
        size_bytes=len(archive_bytes),
        archive_member=member_path,
        archive_sha256=archive_hash,
    )

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read = MagicMock(side_effect=[archive_bytes, b""])

    with patch("src.diarize.urllib.request.urlopen", return_value=mock_response):
        from src.diarize import _ensure_model

        result = _ensure_model(spec, cache)

    # Verify extracted file exists and has correct content
    assert result == cache / spec.filename
    assert result.read_bytes() == member_content

    # Verify archive was deleted
    assert not (cache / f"{spec.filename}.part").exists()


def test_ensure_models_returns_both_paths(tmp_path: Path) -> None:
    """ensure_models returns DiarizationModels with both paths."""
    cache = tmp_path / "cache"
    cache.mkdir()

    # Create fake files
    (cache / SEGMENTATION_MODEL.filename).write_text("seg")
    (cache / EMBEDDING_MODEL.filename).write_text("emb")

    result = ensure_models(cache_dir=cache)

    assert isinstance(result, DiarizationModels)
    assert result.segmentation == cache / SEGMENTATION_MODEL.filename
    assert result.embedding == cache / EMBEDDING_MODEL.filename


# ---------------------------------------------------------------------------
# Diarizer tests
# ---------------------------------------------------------------------------


def _sherpa_modules(mock_sd_instance: MagicMock | None = None) -> dict:
    """Build sys.modules stub for sherpa_onnx."""
    mock_sherpa = MagicMock()

    # Mock the config classes
    mock_sherpa.OfflineSpeakerSegmentationPyannoteModelConfig = MagicMock()
    mock_sherpa.OfflineSpeakerSegmentationModelConfig = MagicMock()
    mock_sherpa.SpeakerEmbeddingExtractorConfig = MagicMock()
    mock_sherpa.FastClusteringConfig = MagicMock()
    mock_sherpa.OfflineSpeakerDiarizationConfig = MagicMock()

    if mock_sd_instance:
        mock_sherpa.OfflineSpeakerDiarization.return_value = mock_sd_instance

    return {"sherpa_onnx": mock_sherpa}


def test_diarizer_fast_clustering_defaults(tmp_path: Path) -> None:
    """FastClusteringConfig receives num_clusters=-1 and threshold=0.8 by default."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    with patch.dict("sys.modules", _sherpa_modules()):
        import sherpa_onnx

        Diarizer(models)

        # Verify FastClusteringConfig was called with defaults
        sherpa_onnx.FastClusteringConfig.assert_called_once()
        call_kwargs = sherpa_onnx.FastClusteringConfig.call_args[1]
        assert call_kwargs["num_clusters"] == -1
        assert call_kwargs["threshold"] == 0.8


def test_diarizer_num_speakers_hint_sets_num_clusters(tmp_path: Path) -> None:
    """When num_speakers is provided, FastClusteringConfig receives it as num_clusters."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    with patch.dict("sys.modules", _sherpa_modules()):
        import sherpa_onnx

        Diarizer(models, num_speakers=3)

        call_kwargs = sherpa_onnx.FastClusteringConfig.call_args[1]
        assert call_kwargs["num_clusters"] == 3


def test_diarizer_relabels_speaker_ids_by_first_appearance(tmp_path: Path) -> None:
    """Raw speaker IDs [7, 2, 7, 5] are relabelled to [1, 2, 1, 3] by first appearance."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    # Mock result with arbitrary speaker IDs
    mock_result = MagicMock()
    mock_result.num_segments = 4

    mock_segments = [
        MagicMock(start=0.0, end=1.0, speaker=7),
        MagicMock(start=1.0, end=2.0, speaker=2),
        MagicMock(start=2.0, end=3.0, speaker=7),
        MagicMock(start=3.0, end=4.0, speaker=5),
    ]
    mock_result.sort_by_start_time.return_value = mock_segments

    mock_sd = MagicMock()
    mock_sd.process.return_value = mock_result

    with patch.dict("sys.modules", _sherpa_modules(mock_sd)):
        diarizer = Diarizer(models)
        samples = np.ones(16000, dtype=np.float32)
        turns = diarizer.run(samples)

    assert len(turns) == 4
    assert [t.speaker for t in turns] == [1, 2, 1, 3]


def test_diarizer_progress_callback_converts_to_percentage(tmp_path: Path) -> None:
    """Progress callback receives chunk counts and forwards percentage."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    mock_result = MagicMock()
    mock_result.sort_by_start_time.return_value = []

    def capture_callback(samples, callback):
        # Simulate progress: 5 out of 10 chunks processed
        callback(5, 10)
        return mock_result

    mock_sd = MagicMock()
    mock_sd.process = capture_callback

    progress_values = []

    def progress_fn(pct: int) -> None:
        progress_values.append(pct)

    with patch.dict("sys.modules", _sherpa_modules(mock_sd)):
        diarizer = Diarizer(models)
        samples = np.ones(16000, dtype=np.float32)
        diarizer.run(samples, progress=progress_fn)

    assert 50 in progress_values


def test_diarizer_process_exception_wrapped(tmp_path: Path) -> None:
    """Exception from process() is wrapped in DiarizationError."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    mock_sd = MagicMock()
    mock_sd.process.side_effect = RuntimeError("model error")

    with patch.dict("sys.modules", _sherpa_modules(mock_sd)):
        diarizer = Diarizer(models)
        samples = np.ones(16000, dtype=np.float32)

        with pytest.raises(DiarizationError, match="speaker identification failed"):
            diarizer.run(samples)


def test_diarizer_empty_samples_returns_empty_list(tmp_path: Path) -> None:
    """Empty input returns [] without calling process()."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    mock_sd = MagicMock()

    with patch.dict("sys.modules", _sherpa_modules(mock_sd)):
        diarizer = Diarizer(models)
        samples = np.array([], dtype=np.float32)
        result = diarizer.run(samples)

    assert result == []
    mock_sd.process.assert_not_called()


def test_diarizer_import_error_wrapped(tmp_path: Path) -> None:
    """ImportError when sherpa_onnx is not installed is wrapped with helpful message."""
    models = DiarizationModels(
        segmentation=tmp_path / "seg.onnx",
        embedding=tmp_path / "emb.onnx",
    )

    # Make import fail by setting module to None
    with patch.dict("sys.modules", {"sherpa_onnx": None}):
        with pytest.raises(DiarizationError, match="sherpa-onnx is not installed"):
            Diarizer(models)


# ---------------------------------------------------------------------------
# assign_speakers tests
# ---------------------------------------------------------------------------


def test_assign_speakers_segment_fully_inside_one_turn() -> None:
    """Segment completely within one turn gets that speaker."""
    segment = TranscriptSegment(
        text="Hello world",
        start_sec=1.0,
        end_sec=2.0,
        words=[
            Word("Hello", 1.0, 1.5),
            Word("world", 1.5, 2.0),
        ],
    )
    turns = [SpeakerTurn(0.0, 3.0, speaker=1)]

    result = assign_speakers(segment, turns)

    assert len(result) == 1
    assert result[0].speaker == 1
    assert result[0].text == "Hello world"


def test_assign_speakers_segment_spanning_two_turns_splits() -> None:
    """Segment spanning two speaker turns splits into two segments."""
    segment = TranscriptSegment(
        text="First speaker then second speaker",
        start_sec=0.0,
        end_sec=4.0,
        words=[
            Word("First", 0.5, 1.0),
            Word("speaker", 1.0, 1.5),
            Word("then", 2.5, 3.0),
            Word("second", 3.0, 3.5),
            Word("speaker", 3.5, 4.0),
        ],
    )
    turns = [
        SpeakerTurn(0.0, 2.0, speaker=1),
        SpeakerTurn(2.0, 5.0, speaker=2),
    ]

    result = assign_speakers(segment, turns)

    assert len(result) == 2
    assert result[0].speaker == 1
    assert result[0].text == "First speaker"
    assert result[0].start_sec == 0.5
    assert result[0].end_sec == 1.5

    assert result[1].speaker == 2
    assert result[1].text == "then second speaker"
    assert result[1].start_sec == 2.5
    assert result[1].end_sec == 4.0


def test_assign_speakers_word_with_no_overlap_uses_nearest_turn() -> None:
    """Word overlapping no turn takes the speaker of the nearest turn boundary."""
    segment = TranscriptSegment(
        text="gap word",
        start_sec=0.0,
        end_sec=3.0,
        words=[
            Word("gap", 1.5, 2.0),  # between turns, closer to first turn's end
            Word("word", 5.5, 6.0),  # between turns, closer to second turn's start
        ],
    )
    turns = [
        SpeakerTurn(0.0, 1.0, speaker=1),
        SpeakerTurn(5.0, 7.0, speaker=2),
    ]

    result = assign_speakers(segment, turns)

    # First word closer to turn 1's boundary (distance 0.5 from midpoint 1.75 to turn end 1.0)
    # Second word closer to turn 2's boundary (distance 0.25 from midpoint 5.75 to turn start 5.0)
    assert len(result) == 2
    assert result[0].speaker == 1
    assert result[1].speaker == 2


def test_assign_speakers_no_words_uses_whole_segment_overlap() -> None:
    """When segment has no words, use whole-segment overlap to assign speaker."""
    segment = TranscriptSegment(
        text="Some text",
        start_sec=1.0,
        end_sec=3.0,
        words=[],  # no word timestamps
    )
    turns = [
        SpeakerTurn(0.0, 2.0, speaker=1),
        SpeakerTurn(2.0, 4.0, speaker=2),
    ]

    result = assign_speakers(segment, turns)

    assert len(result) == 1
    # Segment [1.0, 3.0] overlaps turn 1 by 1.0 and turn 2 by 1.0 (tie)
    # Should pick first one with best overlap
    assert result[0].speaker in (1, 2)
    assert result[0].text == "Some text"


def test_assign_speakers_empty_turns_returns_unchanged() -> None:
    """Empty turns list returns segment unchanged with speaker=None."""
    segment = TranscriptSegment(
        text="Hello",
        start_sec=1.0,
        end_sec=2.0,
        words=[Word("Hello", 1.0, 2.0)],
    )
    turns: list[SpeakerTurn] = []

    result = assign_speakers(segment, turns)

    assert len(result) == 1
    assert result[0] == segment
    assert result[0].speaker is None


def test_assign_speakers_never_returns_empty_for_nonempty_text() -> None:
    """Result is never empty when segment has text."""
    segment = TranscriptSegment(
        text="Text",
        start_sec=1.0,
        end_sec=2.0,
        words=[Word("Text", 1.0, 2.0)],
    )
    turns = [SpeakerTurn(0.0, 3.0, speaker=1)]

    result = assign_speakers(segment, turns)

    assert len(result) > 0


def test_assign_speakers_strips_word_text() -> None:
    """Leading/trailing spaces on word text are stripped when joining."""
    segment = TranscriptSegment(
        text="hello world",
        start_sec=0.0,
        end_sec=2.0,
        words=[
            Word(" hello ", 0.0, 1.0),
            Word("  world  ", 1.0, 2.0),
        ],
    )
    turns = [SpeakerTurn(0.0, 3.0, speaker=1)]

    result = assign_speakers(segment, turns)

    assert result[0].text == "hello world"


# ---------------------------------------------------------------------------
# Real-library smoke test — skipped unless models are already cached.
# Guards against sherpa-onnx API drift that the mocked tests cannot see.
# ---------------------------------------------------------------------------


def test_real_sherpa_onnx_api_smoke() -> None:
    from src.diarize import DIARIZATION_CACHE_DIR, EMBEDDING_MODEL, SEGMENTATION_MODEL

    seg = DIARIZATION_CACHE_DIR / SEGMENTATION_MODEL.filename
    emb = DIARIZATION_CACHE_DIR / EMBEDDING_MODEL.filename
    if not (seg.exists() and emb.exists()):
        pytest.skip("diarization models not cached")
    pytest.importorskip("sherpa_onnx")

    diarizer = Diarizer(DiarizationModels(segmentation=seg, embedding=emb), num_threads=1)
    turns = diarizer.run(np.zeros(16_000, dtype=np.float32))  # one second of silence
    assert turns == []
