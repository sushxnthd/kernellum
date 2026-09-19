from __future__ import annotations

from dataclasses import dataclass
from math import log2, sqrt
from pathlib import Path
import csv
import random

from kernellum.k1.model import K1Architecture, predicted_cycles


@dataclass(frozen=True)
class RoutedObservation:
    arch: K1Architecture
    fmax_mhz: float


def expanded_pool() -> tuple[K1Architecture, ...]:
    rows_cols = (2, 4, 6, 8, 10, 12, 14)
    k_tiles = (8, 16, 32, 64)
    out = []
    for r in rows_cols:
        for c in rows_cols:
            if r * c > 120:
                continue
            for k in k_tiles:
                out.append(K1Architecture(f"r{r:02d}_c{c:02d}_k{k:02d}", r, c, k))
    return tuple(out)


def feature_vector(arch: K1Architecture) -> tuple[float, float, float, float]:
    return (
        arch.pe_count / 120.0,
        log2(arch.k_tile) / 6.0,
        log2(arch.rows / arch.cols),
        abs(arch.rows - arch.cols) / 14.0,
    )


def feature_distance(a: K1Architecture, b: K1Architecture) -> float:
    xa, xb = feature_vector(a), feature_vector(b)
    return sqrt(sum((u - v) ** 2 for u, v in zip(xa, xb)))


def load_observations(path: str | Path) -> list[RoutedObservation]:
    rows = list(csv.DictReader(Path(path).open()))
    out: list[RoutedObservation] = []
    for row in rows:
        if str(row.get("route_ok", "")).lower() != "true":
            continue
        arch = K1Architecture(
            row["name"],
            int(row["rows"]),
            int(row["cols"]),
            int(row["k_tile"]),
        )
        out.append(RoutedObservation(arch, float(row["fmax_mhz"])))
    return out


def predict_fmax(
    arch: K1Architecture,
    observations: list[RoutedObservation],
    *,
    neighbors: int = 4,
) -> tuple[float, float]:
    if not observations:
        raise ValueError("at least one routed observation is required")

    distances = sorted(
        ((feature_distance(arch, obs.arch), obs) for obs in observations),
        key=lambda x: x[0],
    )
    if distances[0][0] < 1e-12:
        return distances[0][1].fmax_mhz, 0.0

    chosen = distances[: min(neighbors, len(distances))]
    weights = [1.0 / (d + 0.03) ** 2 for d, _ in chosen]
    pred = sum(w * obs.fmax_mhz for w, (_, obs) in zip(weights, chosen)) / sum(weights)
    uncertainty = chosen[0][0]
    return pred, uncertainty


def current_best_latency_ms(
    workload,
    observations: list[RoutedObservation],
) -> float:
    values = [
        predicted_cycles(workload.m, workload.n, workload.k, obs.arch)
        / (obs.fmax_mhz * 1e3)
        for obs in observations
    ]
    return min(values)


def active_proposals(
    observations: list[RoutedObservation],
    workloads,
    *,
    n: int = 4,
) -> list[dict]:
    seen = {obs.arch.name for obs in observations}
    baselines = {
        w.name: current_best_latency_ms(w, observations)
        for w in workloads
    }
    scored: list[dict] = []
    for arch in expanded_pool():
        if arch.name in seen:
            continue
        pred_fmax, uncertainty = predict_fmax(arch, observations)
        optimistic_fmax = pred_fmax + 6.0 * uncertainty
        ratios = []
        for w in workloads:
            latency = predicted_cycles(w.m, w.n, w.k, arch) / (optimistic_fmax * 1e3)
            ratios.append(latency / baselines[w.name])
        scored.append({
            "arch": arch,
            "predicted_fmax_mhz": pred_fmax,
            "uncertainty": uncertainty,
            "optimistic_fmax_mhz": optimistic_fmax,
            "acquisition_score": sum(ratios) / len(ratios),
        })
    scored.sort(key=lambda x: (x["acquisition_score"], x["uncertainty"], x["arch"].name))
    return scored[:n]


def random_controls(
    observations: list[RoutedObservation],
    active: list[dict],
    *,
    n: int = 4,
    seed: int = 20260919,
) -> list[K1Architecture]:
    excluded = {obs.arch.name for obs in observations}
    excluded.update(x["arch"].name for x in active)
    pool = [a for a in expanded_pool() if a.name not in excluded]
    rng = random.Random(seed)
    return rng.sample(pool, n)
