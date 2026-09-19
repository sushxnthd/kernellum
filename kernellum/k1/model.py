from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt


@dataclass(frozen=True)
class K1Architecture:
    name: str
    rows: int
    cols: int
    k_tile: int

    @property
    def pe_count(self) -> int:
        return self.rows * self.cols

    @property
    def ideal_buffer_bits(self) -> int:
        return self.k_tile * (self.rows + self.cols) * 8


def candidate_set() -> tuple[K1Architecture, ...]:
    return (
        K1Architecture("r04_c04_k16", 4, 4, 16),
        K1Architecture("r04_c08_k32", 4, 8, 32),
        K1Architecture("r08_c04_k32", 8, 4, 32),
        K1Architecture("r08_c08_k16", 8, 8, 16),
        K1Architecture("r08_c08_k32", 8, 8, 32),
        K1Architecture("r08_c08_k64", 8, 8, 64),
        K1Architecture("r08_c12_k32", 8, 12, 32),
        K1Architecture("r12_c08_k32", 12, 8, 32),
        K1Architecture("r10_c10_k32", 10, 10, 32),
    )


def predicted_cycles(m: int, n: int, k: int, arch: K1Architecture) -> int:
    m_tiles = ceil(m / arch.rows)
    n_tiles = ceil(n / arch.cols)
    k_chunks = ceil(k / arch.k_tile)
    cycles_per_output_tile = 2 * k + 3 * k_chunks + 2
    return m_tiles * n_tiles * cycles_per_output_tile


def _rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + j - 1) / 2 + 1
        for q in range(i, j):
            ranks[indexed[q][0]] = avg
        i = j
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("rank vectors must be non-empty and equal length")
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sqrt(sum((x - ma) ** 2 for x in a))
    db = sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return 1.0 if a == b else 0.0
    return numerator / (da * db)


def spearman(a: list[float], b: list[float]) -> float:
    return _pearson(_rank(a), _rank(b))
