"""
streamer.py — Chunked file writer.

Consumes rows from the generator and streams them into numbered .txt files
with buffered I/O. Never accumulates more than one chunk in RAM at a time.

Output format per line (no header, no quotes):
    id,english_text
"""

from __future__ import annotations

import itertools
import logging
import sys
import time
from typing import Generator

from config import GeneratorConfig
from generator import Row, SentenceGenerator

# ── Optional tqdm — fall back to a lightweight stdlib progress bar ───────────
try:
    from tqdm import tqdm as _tqdm

    def _make_bar(total: int, desc: str, leave: bool = True):
        return _tqdm(total=total, desc=desc, unit="row",
                     colour="green", dynamic_ncols=True, leave=leave)

except ImportError:  # pragma: no cover

    class _FallbackBar:  # type: ignore[no-redef]
        """Minimal tqdm-compatible progress bar using only stdlib."""

        def __init__(self, total: int, desc: str, leave: bool = True) -> None:
            self._total = total
            self._n = 0
            self._desc = desc
            self._leave = leave
            self._t0 = time.perf_counter()
            self._last_print = 0.0

        def update(self, n: int = 1) -> None:
            self._n += n
            now = time.perf_counter()
            if now - self._last_print >= 0.5 or self._n >= self._total:
                pct = self._n / self._total * 100 if self._total else 0
                elapsed = now - self._t0
                rate = self._n / elapsed if elapsed > 0 else 0
                sys.stderr.write(
                    f"\r  {self._desc:<20} {self._n:>8,}/{self._total:,}"
                    f"  [{pct:5.1f}%]  {rate:,.0f} rows/s   "
                )
                sys.stderr.flush()
                self._last_print = now

        def close(self) -> None:
            if self._leave:
                sys.stderr.write("\n")
                sys.stderr.flush()
            else:
                sys.stderr.write("\r" + " " * 70 + "\r")
                sys.stderr.flush()

    def _make_bar(total: int, desc: str, leave: bool = True):  # type: ignore[misc]
        return _FallbackBar(total=total, desc=desc, leave=leave)

logger = logging.getLogger(__name__)

# Tune to OS page size for maximum throughput (~64 KB is a safe default)
_IO_BUFFER_BYTES = 65_536


def run(config: GeneratorConfig) -> None:
    """
    Entry-point for the streaming pipeline.

    1. Instantiate the sentence generator with the configured seed.
    2. Pull rows in chunks.
    3. Write each chunk to its own .txt file with buffered I/O.
    4. Show tqdm progress at both chunk and global level.
    """
    logger.info(
        "Starting generation: %d rows → %d chunks of %d rows each",
        config.total_rows,
        config.num_chunks,
        config.rows_per_chunk,
    )

    gen = SentenceGenerator(seed=config.seed,
                            seen_hashes_file=config.seen_hashes_path,
                            categories=config.categories)
    logger.info("Content selection: %s", gen.describe_selection())
    row_stream = gen.stream(config.total_rows)

    global_bar = _make_bar(config.total_rows, "Total rows", leave=True)

    written_total = 0

    for chunk_idx in range(1, config.num_chunks + 1):
        # Last chunk may be smaller
        chunk_size = (
            config.last_chunk_rows
            if chunk_idx == config.num_chunks
            else config.rows_per_chunk
        )

        filepath = config.chunk_filename(chunk_idx)

        with open(filepath, "w", encoding="utf-8", buffering=_IO_BUFFER_BYTES) as fh:
            chunk_bar = _make_bar(chunk_size, filepath.name, leave=False)

            rows_written = 0
            for row in _take(row_stream, chunk_size):
                fh.write(_format_row(row))
                rows_written += 1
                chunk_bar.update(1)
                global_bar.update(1)

            chunk_bar.close()

        written_total += rows_written
        logger.debug("Wrote %d rows to %s", rows_written, filepath.name)

    global_bar.close()
    logger.info("Generation complete. %d rows written to %s", written_total, config.output_dir)
    print(f"\n✅  Done! {written_total:,} rows → {config.num_chunks} files in '{config.output_dir}'")


def preview(config: GeneratorConfig) -> None:
    """Print sample sentences for the chosen categories. Writes nothing."""
    gen = SentenceGenerator(seed=config.seed, categories=config.categories)
    print(f"  Selection : {gen.describe_selection()}")
    print("-" * 68)
    for row in gen.stream(config.preview):
        print(f"  {row.id:>3}. {row.english_text}")
    print("-" * 68)
    print("  Preview only — no files were written.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_row(row: Row) -> str:
    """Return a single newline-terminated line: id,english_text"""
    return f"{row.id},{row.english_text}\n"


def _take(stream: Generator[Row, None, None], n: int) -> Generator[Row, None, None]:
    """Yield exactly `n` items from `stream` without consuming an extra element."""
    yield from itertools.islice(stream, n)
