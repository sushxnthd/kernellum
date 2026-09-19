from __future__ import annotations
from dataclasses import dataclass, asdict
from itertools import product

DATAFLOWS = ("weight_stationary", "output_stationary", "row_stationary")

@dataclass(frozen=True)
class Architecture:
    array_rows: int
    array_cols: int
    precision_bits: int
    tile_m: int
    tile_n: int
    tile_k: int
    buffer_kb: int
    dataflow: str

    def to_dict(self) -> dict:
        return asdict(self)

def default_design_space():
    values = {
        "array_rows": (4, 8, 16, 32),
        "array_cols": (4, 8, 16, 32),
        "precision_bits": (4, 8),
        "tile_m": (16, 32, 64, 128),
        "tile_n": (16, 32, 64, 128),
        "tile_k": (16, 32, 64, 128),
        "buffer_kb": (64, 128, 256, 512),
        "dataflow": DATAFLOWS,
    }
    keys = tuple(values)
    for combo in product(*(values[k] for k in keys)):
        yield Architecture(**dict(zip(keys, combo)))

def design_axes() -> dict[str, tuple]:
    return {
        "array_rows": (4, 8, 16, 32),
        "array_cols": (4, 8, 16, 32),
        "precision_bits": (4, 8),
        "tile_m": (16, 32, 64, 128),
        "tile_n": (16, 32, 64, 128),
        "tile_k": (16, 32, 64, 128),
        "buffer_kb": (64, 128, 256, 512),
        "dataflow": DATAFLOWS,
    }
