"""
cli.py — Command-line interface using argparse.

Parses user arguments and returns a validated GeneratorConfig object.
If --output-dir is omitted, a GUI folder picker is launched (tkinter).
If --category is omitted, an interactive category picker is shown.
Both fall back sensibly when tkinter or a terminal is unavailable.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import categories as cat_registry
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
        "--category", "-c",
        action="append",
        default=None,
        metavar="NAME",
        help=(
            "Topic to generate (repeatable, or comma-separated): "
            "school, animals, nature, conversation, greetings, people, food … "
            "Groups such as 'daily' or 'travelpack' expand to several topics. "
            "Use 'all' for everything. Omit to pick interactively. "
            "See --list-categories."
        ),
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="Print every available category and group, then exit.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        metavar="N",
        help="Print N sample sentences for the chosen categories and exit "
             "(nothing is written to disk).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Random seed for reproducibility. "
            "Omit (recommended) to auto-generate a fresh seed each run, "
            "ensuring every run produces unique output. "
            "The seed used is printed at startup and saved to runs.log."
        ),
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

    if args.list_categories:
        print(cat_registry.describe_table())
        raise SystemExit(0)

    # ── Validate ─────────────────────────────────────────────────────────
    if args.total_rows < 1:
        parser.error("--total-rows must be >= 1")
    if args.rows_per_chunk < 1:
        parser.error("--rows-per-chunk must be >= 1")

    # ── Resolve categories ───────────────────────────────────────────────
    raw_categories = args.category if args.category is not None else _pick_categories()
    try:
        selection = cat_registry.expand(raw_categories)
    except ValueError as exc:
        parser.error(str(exc))

    # ── Resolve output directory ─────────────────────────────────────────
    if args.preview > 0:
        output_dir = Path.cwd()
    elif args.output_dir is None:
        output_dir = _pick_directory_gui()
    else:
        output_dir = Path(args.output_dir)

    return GeneratorConfig(
        total_rows=args.total_rows,
        rows_per_chunk=args.rows_per_chunk,
        seed=args.seed,        # None → auto-random inside GeneratorConfig
        output_dir=output_dir,
        categories=selection,
        preview=args.preview,
    )


# ── Interactive pickers ──────────────────────────────────────────────────

def _pick_categories() -> list[str]:
    """
    Ask which topics to generate. Console menu when a terminal is attached,
    otherwise fall back to every category.
    """
    if not sys.stdin.isatty():
        logger.info("No terminal attached — generating from all categories.")
        return []

    keys = cat_registry.category_keys()
    print()
    print("=" * 68)
    print("  Which topics should the sentences cover?")
    print("=" * 68)
    for i, key in enumerate(keys, start=1):
        cat = cat_registry.CATEGORIES[key]
        print(f"  {i:>2}. {key.ljust(14)} {cat.label}")
    print()
    print("  Groups: " + ", ".join(cat_registry.group_keys()))
    print("  Enter numbers or names separated by commas (e.g. '3,7' or")
    print("  'animals,nature'), a group name, or press Enter for ALL.")
    print("=" * 68)

    while True:
        try:
            raw = input("  Categories [all]: ").strip()
        except EOFError:
            return []
        if not raw:
            return []

        chosen: list[str] = []
        unknown: list[str] = []
        for part in (p.strip().lower() for p in raw.split(",") if p.strip()):
            if part.isdigit() and 1 <= int(part) <= len(keys):
                chosen.append(keys[int(part) - 1])
            elif part in cat_registry.CATEGORIES or part in cat_registry.GROUPS \
                    or part == cat_registry.ALL:
                chosen.append(part)
            else:
                unknown.append(part)

        if unknown:
            print(f"  Not recognised: {', '.join(unknown)} — try again.")
            continue
        return chosen


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
  # Interactive: pick topics from a menu, then pick an output folder
  python main.py

  # See every topic and group
  python main.py --list-categories

  # One topic
  python main.py --category school --total-rows 50000

  # Several topics (repeat the flag or use commas)
  python main.py -c animals -c nature -c conversation
  python main.py --category animals,nature,conversation

  # A ready-made bundle (daily, travelpack, beginner, academic, worklife, world)
  python main.py --category travelpack --total-rows 200000

  # Everything, no prompts
  python main.py --category all --output-dir ./output

  # Try before generating: 20 sample sentences, nothing written
  python main.py --category greetings --preview 20

  # Resume / reproduce a previous run (use seed from runs.log)
  python main.py --seed 1748291023 --category all
"""
