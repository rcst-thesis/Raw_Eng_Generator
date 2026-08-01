"""
config.py — Central configuration dataclass for the sentence generator.
All runtime parameters flow through this single object.
"""

import re
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import categories as cat_registry


# ── Series letter helpers ────────────────────────────────────────────────────

def _series_regex(prefix: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(prefix)}([A-Z])_\d+\.txt$", re.IGNORECASE)


def _next_series_letter(output_dir: Path, prefix: str) -> str:
    """
    Scan output_dir for existing <prefix><LETTER>_NNN.txt files and return the
    next unused uppercase letter (A → B → C … → Z).

    Each category keeps its own series, because the prefix differs per category.

    - If no matching files exist: returns 'A'.
    - If the highest letter found is 'D', returns 'E'.
    - Raises RuntimeError if all 26 letters are exhausted.
    """
    pattern = _series_regex(prefix)
    used: set[str] = set()
    for f in output_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            used.add(m.group(1).upper())

    if not used:
        return "A"

    next_ord = ord(max(used)) + 1
    if next_ord > ord("Z"):
        raise RuntimeError(
            f"All 26 series letters (A-Z) have been used for '{prefix}*' in "
            f"'{output_dir}'. Please use a new output directory."
        )
    return chr(next_ord)


# ── Config dataclass ─────────────────────────────────────────────────────────

@dataclass
class GeneratorConfig:
    """Immutable runtime configuration passed to all modules."""

    total_rows: int = 100_000
    rows_per_chunk: int = 1_000
    seed: Optional[int] = None
    output_dir: Path = field(default_factory=lambda: Path.cwd())
    categories: list[str] = field(default_factory=list)   # [] == every category
    preview: int = 0                                      # >0 → sample only, no files

    # Derived — computed in __post_init__
    num_chunks: int = field(init=False)
    series_letter: str = field(init=False)
    category_slug: str = field(init=False)

    def __post_init__(self) -> None:
        if self.total_rows < 1:
            raise ValueError("total_rows must be >= 1")
        if self.rows_per_chunk < 1:
            raise ValueError("rows_per_chunk must be >= 1")

        self.categories = cat_registry.expand(self.categories)
        self.category_slug = cat_registry.slug(self.categories)

        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.seed is None:
            self.seed = secrets.randbits(31)

        self.num_chunks = -(-self.total_rows // self.rows_per_chunk)
        self.series_letter = _next_series_letter(self.output_dir, self.file_prefix)

    @property
    def category_label(self) -> str:
        return ", ".join(self.categories) if self.categories else "all"

    @property
    def file_prefix(self) -> str:
        """
        Filename prefix, minus the series letter.

        Uncategorised runs keep the original 'eng_L_' scheme so they stay in
        the same series as previously generated files; categorised runs get
        their own prefix, and therefore their own A-Z series.
        """
        if not self.categories:
            return "eng_L_"
        return f"eng_{self.category_slug}_"

    @property
    def last_chunk_rows(self) -> int:
        remainder = self.total_rows % self.rows_per_chunk
        return remainder if remainder else self.rows_per_chunk

    def chunk_filename(self, chunk_index: int) -> Path:
        return self.output_dir / (
            f"{self.file_prefix}{self.series_letter}_{chunk_index:03d}.txt"
        )

    @property
    def seen_hashes_path(self) -> Path:
        return self.output_dir / ".seen_hashes.bin"

    @property
    def run_log_path(self) -> Path:
        return self.output_dir / "runs.log"
