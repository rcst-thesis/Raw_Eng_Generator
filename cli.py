"""
cli.py — Command-line interface using argparse.

Parses user arguments and returns a validated GeneratorConfig object.
If --output-dir is omitted, a GUI folder picker is launched (tkinter).
Falls back to the current working directory if tkinter is unavailable.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import GeneratorConfig

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> GeneratorConfig:
    parser = argparse.ArgumentParser(
        prog="sentence_gen",
        description=(
            "Stream millions of human-like English sentences into chunked .txt files.\n"
            "Output format per line:  id,english_text"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_EXAMPLES,
    )

    parser.add_argument(
        "--total-rows",
        type=int,
        default=100_000,
        metavar="N",
        help="Total number of rows to generate (default: 100,000)",
    )
    parser.add_argument(
        "--rows-per-chunk",
        type=int,
        default=1_000,
        metavar="N",
        help="Rows per output file (default: 1,000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        metavar="N",
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        metavar="PATH",
        help=(
            "Directory to write output files. "
            "Omit to open a folder picker dialog."
        ),
    )

    args = parser.parse_args(argv)

    # ── Validate ─────────────────────────────────────────────────────────
    if args.total_rows < 1:
        parser.error("--total-rows must be >= 1")
    if args.rows_per_chunk < 1:
        parser.error("--rows-per-chunk must be >= 1")

    # ── Resolve output directory ─────────────────────────────────────────
    if args.output_dir is None:
        output_dir = _pick_directory_gui()
    else:
        output_dir = Path(args.output_dir)

    return GeneratorConfig(
        total_rows=args.total_rows,
        rows_per_chunk=args.rows_per_chunk,
        seed=args.seed,
        output_dir=output_dir,
    )


def _pick_directory_gui() -> Path:
    """Open a cross-platform folder picker. Fall back to cwd on failure."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(title="Select output directory")
        root.destroy()

        if chosen:
            return Path(chosen)
        logger.warning("No directory selected — using current working directory.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("GUI folder picker unavailable (%s) — using cwd.", exc)

    return Path.cwd()


_EXAMPLES = """
examples:
  # Default: 100k rows, 1k rows/file, seed 42, cwd output
  python main.py

  # Custom rows and chunk size
  python main.py --total-rows 500000 --rows-per-chunk 5000

  # Specific output directory
  python main.py --output-dir ./output --total-rows 100000 --rows-per-chunk 1000

  # Reproducible run with explicit seed
  python main.py --seed 99 --total-rows 50000
"""
