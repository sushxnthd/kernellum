from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def read_windows(path: Path) -> list[tuple[float, float]]:
    windows: list[tuple[float, float]] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if not {"start_s", "done_s"}.issubset(reader.fieldnames or []):
            raise ValueError("latency CSV must contain start_s,done_s columns")
        for row in reader:
            if not row.get("start_s") or not row.get("done_s"):
                continue
            start, done = float(row["start_s"]), float(row["done_s"])
            if done <= start:
                raise ValueError(f"invalid window: start={start} done={done}")
            windows.append((start, done))
    if not windows:
        raise ValueError("no measurement windows found")
    return windows


def read_power(path: Path) -> tuple[np.ndarray, np.ndarray]:
    times, watts = [], []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if not {"time_s", "power_w"}.issubset(reader.fieldnames or []):
            raise ValueError("power CSV must contain time_s,power_w columns")
        for row in reader:
            if not row.get("time_s") or not row.get("power_w"):
                continue
            times.append(float(row["time_s"]))
            watts.append(float(row["power_w"]))
    if len(times) < 2:
        raise ValueError("power trace requires at least two samples")
    order = np.argsort(times)
    return np.asarray(times)[order], np.asarray(watts)[order]


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q))


def integrate_power_window(
    times: np.ndarray,
    power: np.ndarray,
    start: float,
    done: float,
    idle_power_w: float | None,
) -> float:
    mask = (times >= start) & (times <= done)
    t = times[mask]
    p = power[mask]
    # Interpolate exact endpoints if the trace spans them.
    if times[0] <= start <= times[-1]:
        p_start = float(np.interp(start, times, power))
        if len(t) == 0 or t[0] > start:
            t = np.insert(t, 0, start)
            p = np.insert(p, 0, p_start)
    if times[0] <= done <= times[-1]:
        p_done = float(np.interp(done, times, power))
        if len(t) == 0 or t[-1] < done:
            t = np.append(t, done)
            p = np.append(p, p_done)
    if len(t) < 2:
        raise ValueError(f"power trace does not span measurement window {start}..{done}")
    if idle_power_w is not None:
        p = np.maximum(p - float(idle_power_w), 0.0)
    return float(np.trapezoid(p, t))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze physical Kernellum ULX3S measurements")
    parser.add_argument("latency_csv", type=Path, help="CSV with start_s,done_s rows from GP0/GN0")
    parser.add_argument("--power-csv", type=Path, default=None, help="optional time_s,power_w trace")
    parser.add_argument("--idle-power-w", type=float, default=None, help="optional idle baseline to subtract")
    parser.add_argument("--out", type=Path, default=Path("hardware/ulx3s/measurement_summary.json"))
    args = parser.parse_args()

    windows = read_windows(args.latency_csv)
    latency_us = np.asarray([(done - start) * 1e6 for start, done in windows], dtype=np.float64)
    result = {
        "schema": "kernellum.physical_measurement.v1",
        "evidence_level": "physical measurement",
        "latency": {
            "samples": int(len(latency_us)),
            "min_us": float(np.min(latency_us)),
            "median_us": float(np.median(latency_us)),
            "mean_us": float(np.mean(latency_us)),
            "p95_us": percentile(latency_us, 95),
            "max_us": float(np.max(latency_us)),
        },
        "power": None,
    }

    if args.power_csv is not None:
        times, power = read_power(args.power_csv)
        energies = np.asarray(
            [
                integrate_power_window(times, power, start, done, args.idle_power_w)
                for start, done in windows
            ],
            dtype=np.float64,
        )
        result["power"] = {
            "trace_samples": int(len(times)),
            "mean_power_w": float(np.mean(power)),
            "idle_power_subtracted_w": args.idle_power_w,
            "energy_per_inference_j": {
                "median": float(np.median(energies)),
                "mean": float(np.mean(energies)),
                "p95": percentile(energies, 95),
            },
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
