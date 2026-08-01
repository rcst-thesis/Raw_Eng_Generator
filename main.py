"""
main.py — Entry point for the English sentence dataset generator.

Usage:
    python main.py [options]

Run `python main.py --help` for full usage.
"""

from __future__ import annotations

import datetime
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

from cli import parse_args               # noqa: E402
from streamer import preview, run        # noqa: E402


def main() -> None:
    config = parse_args()

    if config.preview:
        print("=" * 68)
        print(f"  Preview — {config.preview} sample sentences")
        print("=" * 68)
        preview(config)
        return

    # ── Count sentences already generated in this output directory ───────
    cache = config.seen_hashes_path
    prior_count = 0
    if cache.exists():
        prior_count = cache.stat().st_size // 8   # 8 bytes per hash

    print("=" * 68)
    print("  English Sentence Dataset Generator")
    print("=" * 68)
    print(f"  Categories      : {config.category_label}")
    print(f"  Total rows      : {config.total_rows:,}")
    print(f"  Rows per chunk  : {config.rows_per_chunk:,}")
    print(f"  File pattern    : {config.chunk_filename(1).name}")
    print(f"  Number of files : {config.num_chunks:,}")
    print(f"  Random seed     : {config.seed}  <- save this to reproduce")
    print(f"  Output dir      : {config.output_dir}")
    if prior_count:
        print(f"  Already seen    : {prior_count:,} sentences (will be skipped)")
    print("=" * 68)
    print()

    t0 = time.perf_counter()
    run(config)
    elapsed = time.perf_counter() - t0

    rows_per_sec = config.total_rows / elapsed if elapsed > 0 else float("inf")
    print(f"\n⏱  Finished in {elapsed:.2f}s  ({rows_per_sec:,.0f} rows/sec)")

    # ── Append to runs.log so the seed is always recoverable ─────────────
    _write_run_log(config, elapsed)


def _write_run_log(config, elapsed: float) -> None:
    """Append one line to runs.log with the seed and run parameters."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"{timestamp}  seed={config.seed}  "
        f"categories={config.category_label}  "
        f"rows={config.total_rows:,}  chunk={config.rows_per_chunk:,}  "
        f"elapsed={elapsed:.1f}s\n"
    )
    try:
        with open(config.run_log_path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        logging.getLogger(__name__).warning("Could not write runs.log: %s", exc)


if __name__ == "__main__":
    main()
