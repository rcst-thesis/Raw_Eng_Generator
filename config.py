"""
config.py — Central configuration dataclass for the sentence generator.
All runtime parameters flow through this single object.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GeneratorConfig:
    """Immutable runtime configuration passed to all modules."""

    total_rows: int = 10_000_000
    rows_per_chunk: int = 1_000
    seed: int = 42
    output_dir: Path = field(default_factory=lambda: Path.cwd())

    # Derived — computed in __post_init__
    num_chunks: int = field(init=False)

    def __post_init__(self) -> None:
        if self.total_rows < 1:
            raise ValueError("total_rows must be >= 1")
        if self.rows_per_chunk < 1:
            raise ValueError("rows_per_chunk must be >= 1")
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Ceiling division so every row is written even if not evenly divisible
        self.num_chunks = -(-self.total_rows // self.rows_per_chunk)

    @property
    def last_chunk_rows(self) -> int:
        """Number of rows in the final (possibly partial) chunk."""
        remainder = self.total_rows % self.rows_per_chunk
        return remainder if remainder else self.rows_per_chunk

    def chunk_filename(self, chunk_index: int) -> Path:
        """Return the Path for a chunk file given its 1-based index."""
        return self.output_dir / f"file_{chunk_index:03d}.txt"
