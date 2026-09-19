from __future__ import annotations
from dataclasses import dataclass, asdict
from math import ceil
from kernellum.architecture import Architecture
from kernellum.workload import GEMMWorkload

@dataclass(frozen=True)
class Constraints:
    max_dsp: int = 1200
    max_bram: int = 600
    max_latency_ms: float | None = None
    allowed_precisions: tuple[int, ...] = (4, 8)

@dataclass(frozen=True)
class Estimate:
    latency_ms: float
    compute_ms: float
    memory_ms: float
    dsp: int
    bram: int
    memory_mb: float
    utilization: float
    energy_proxy_mj: float
    feasible: bool
    buffer_required_kb: float

    def to_dict(self) -> dict:
        return asdict(self)

def _ceildiv(a: int, b: int) -> int:
    return (a + b - 1) // b

def _traffic_bytes(w: GEMMWorkload, a: Architecture) -> tuple[float, float]:
    """Tile-level traffic estimate; analytical, not cycle-accurate."""
    bpe = a.precision_bits / 8.0
    mt, nt, kt = (_ceildiv(w.m, a.tile_m), _ceildiv(w.n, a.tile_n), _ceildiv(w.k, a.tile_k))
    am, an, ak = min(a.tile_m, w.m), min(a.tile_n, w.n), min(a.tile_k, w.k)
    a_tile = am * ak * bpe
    b_tile = ak * an * bpe
    c_tile = am * an * max(2.0, bpe)

    if a.dataflow == "weight_stationary":
        traffic = mt * nt * kt * a_tile + nt * kt * b_tile + mt * nt * c_tile
    elif a.dataflow == "output_stationary":
        traffic = mt * nt * kt * (a_tile + b_tile) + mt * nt * c_tile
    else:
        traffic = mt * kt * a_tile + nt * kt * b_tile + mt * nt * c_tile + 0.25 * mt * nt * kt * (a_tile + b_tile)

    required = 2.0 * (a_tile + b_tile) + c_tile
    return traffic, required

def estimate(w: GEMMWorkload, a: Architecture, c: Constraints = Constraints(), *, freq_mhz: float = 200.0, bandwidth_gbps: float = 12.8) -> Estimate:
    dsp = ceil(a.array_rows * a.array_cols * (a.precision_bits / 8.0))
    bram = ceil(a.buffer_kb * 1024 / 2304)

    m_util = min(1.0, w.m / max(a.array_rows, 1))
    n_util = min(1.0, w.n / max(a.array_cols, 1))
    edge_m = w.m / (_ceildiv(w.m, a.array_rows) * a.array_rows)
    edge_n = w.n / (_ceildiv(w.n, a.array_cols) * a.array_cols)
    utilization = max(0.05, min(1.0, m_util * n_util * edge_m * edge_n))

    packing = 8.0 / a.precision_bits
    macs_per_cycle = a.array_rows * a.array_cols * packing * utilization
    compute_cycles = w.macs / max(macs_per_cycle, 1e-9)
    tile_count = _ceildiv(w.m, a.tile_m) * _ceildiv(w.n, a.tile_n) * _ceildiv(w.k, a.tile_k)
    compute_cycles += tile_count * (a.array_rows + a.array_cols - 2)
    compute_ms = compute_cycles / (freq_mhz * 1e3)

    traffic_bytes, buffer_required = _traffic_bytes(w, a)
    memory_ms = traffic_bytes / (bandwidth_gbps * 1e9) * 1e3
    latency_ms = max(compute_ms, memory_ms) + 0.08 * min(compute_ms, memory_ms)
    buffer_required_kb = buffer_required / 1024.0

    op_pj = 0.15 if a.precision_bits == 4 else 0.35
    byte_pj = 12.0
    energy_proxy_mj = (w.macs * op_pj + traffic_bytes * byte_pj) * 1e-9

    feasible = (
        dsp <= c.max_dsp
        and bram <= c.max_bram
        and buffer_required_kb <= a.buffer_kb
        and a.precision_bits in c.allowed_precisions
    )
    if c.max_latency_ms is not None:
        feasible = feasible and latency_ms <= c.max_latency_ms

    return Estimate(latency_ms, compute_ms, memory_ms, dsp, bram, traffic_bytes/1e6, utilization, energy_proxy_mj, feasible, buffer_required_kb)

def scalar_objective(e: Estimate, c: Constraints) -> float:
    """Primary K0 objective: minimize latency subject to hard constraints."""
    if not e.feasible:
        return 1e9 + e.latency_ms
    return e.latency_ms
