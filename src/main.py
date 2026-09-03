from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.capture import CaptureError
from src.config import Config, ConfigError, load_config
from src.file_input import FileInputError, FileSession
from src.session import LiveSession
from src.transcribe import Transcriber


def _positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if n < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return n


def _resolve_diarization(args: argparse.Namespace, config: Config) -> tuple[bool, int | None]:
    """Return (enabled, num_speakers). CLI values override config values.

    A config-only `diarize = true` applies to file mode only, so live sessions are unaffected.
    """
    cli_requested = bool(args.diarize) or args.num_speakers is not None
    enabled = cli_requested or (config.diarize and args.file is not None)
    num_speakers = args.num_speakers if args.num_speakers is not None else config.num_speakers
    return enabled, num_speakers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voicenotes",
        description="Capture voice to Markdown, locally and privately.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        metavar="AUDIO_FILE",
        help="Transcribe a .wav, .mp3, or .m4a file instead of live capture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="OUTPUT_PATH",
        help="Override the output file path (directory and filename).",
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Label speakers in the transcript (requires --file).",
    )
    parser.add_argument(
        "--num-speakers",
        type=_positive_int,
        metavar="N",
        help="Expected number of speakers; implies --diarize.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    # -- Config ----------------------------------------------------------
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    # -- Diarization guard and model setup -------------------------------
    cli_requested = bool(args.diarize) or args.num_speakers is not None
    if cli_requested and not args.file:
        print("Error: speaker diarization is only available with --file.", file=sys.stderr)
        sys.exit(1)

    diarize, num_speakers = _resolve_diarization(args, config)
    diarizer = None
    if diarize:
        from src.diarize import DiarizationError, Diarizer, ensure_models

        try:
            models = ensure_models()
            diarizer = Diarizer(models, num_speakers=num_speakers)
        except DiarizationError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    transcriber = Transcriber(config.model, language=config.language)
    output_dir = config.output_dir
    output_path = args.output.expanduser().resolve() if args.output else None

    # -- Dispatch --------------------------------------------------------
    if args.file:
        session = FileSession(
            config, transcriber, output_dir, output_path=output_path, diarizer=diarizer
        )
        try:
            ok = session.run(args.file)
        except FileInputError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        if ok is False:
            sys.exit(1)
    else:
        session = LiveSession(config, transcriber, output_dir, output_path=output_path)
        try:
            session.run()
        except CaptureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
