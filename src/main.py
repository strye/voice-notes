from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.capture import CaptureError
from src.config import ConfigError, load_config
from src.file_input import FileInputError, FileSession
from src.session import LiveSession
from src.transcribe import Transcriber


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="voicenotes",
        description="Capture voice to Markdown, locally and privately.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        metavar="AUDIO_FILE",
        help="Transcribe a .wav or .mp3 file instead of live capture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="OUTPUT_PATH",
        help="Override the output file path (directory and filename).",
    )
    args = parser.parse_args()

    # -- Config ----------------------------------------------------------
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    transcriber = Transcriber(config.model, language=config.language)
    output_dir = config.output_dir
    output_path = args.output.expanduser().resolve() if args.output else None

    # -- Dispatch --------------------------------------------------------
    if args.file:
        session = FileSession(config, transcriber, output_dir, output_path=output_path)
        try:
            session.run(args.file)
        except FileInputError as exc:
            print(f"Error: {exc}", file=sys.stderr)
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
