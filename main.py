"""
main.py — Entry point for the English sentence dataset generator.

Usage:
    python main.py [options]

Run `python main.py --help` for full usage.
"""

from __future__ import annotations

import logging
import sys
import time

# ── Configure logging before importing project modules ───────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

from cli import parse_args          # noqa: E402
from streamer import run            # noqa: E402


def main() -> None:
    config = parse_args()

    print("=" * 60)
    print("  English Sentence Dataset Generator")
    print("=" * 60)
    print(f"  Total rows      : {config.total_rows:,}")
    print(f"  Rows per chunk  : {config.rows_per_chunk:,}")
    print(f"  Number of files : {config.num_chunks:,}")
    print(f"  Random seed     : {config.seed}")
    print(f"  Output dir      : {config.output_dir}")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    run(config)
    elapsed = time.perf_counter() - t0

    rows_per_sec = config.total_rows / elapsed if elapsed > 0 else float("inf")
    print(f"\n⏱  Finished in {elapsed:.2f}s  ({rows_per_sec:,.0f} rows/sec)")


if __name__ == "__main__":
    main()
