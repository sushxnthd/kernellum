from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .compiler import compute_cycles


@dataclass(frozen=True)
class PNRPoint:
    lanes: int
    cycles: int
    target_mhz: float
    achieved_fmax_mhz: float | None
    timing_met: bool | None
    board_clock_mhz: float
    board_clock_core_latency_us: float
    post_route_core_latency_us_at_fmax: float | None
    slices_used: int | None
    slices_available: int | None
    multipliers_used: int | None
    multipliers_available: int | None
    utilization: dict[str, Any]
    report_path: str


def _used_available(utilization: dict[str, Any], names: tuple[str, ...]) -> tuple[int | None, int | None]:
    normalized = {k.upper(): v for k, v in utilization.items()}
    for name in names:
        for key, value in normalized.items():
            if name in key and isinstance(value, dict):
                used = value.get("used")
                available = value.get("available")
                return (
                    int(used) if used is not None else None,
                    int(available) if available is not None else None,
                )
    return None, None


def parse_nextpnr_report(
    path: str | Path,
    *,
    lanes: int,
    dims: tuple[int, ...] = (64, 32, 16, 10),
    target_mhz: float = 100.0,
    board_clock_mhz: float = 25.0,
) -> PNRPoint:
    path = Path(path)
    report = json.loads(path.read_text())
    fmax = report.get("fmax") or {}
    frequencies = []
    for name, value in fmax.items():
        if not isinstance(value, dict):
            continue
        achieved = value.get("achieved")
        constraint = value.get("constraint")
        if achieved is not None:
            frequencies.append((str(name), float(achieved), float(constraint) if constraint is not None else None))

    # One clock is expected. If tools expose more than one, use the slowest achieved
    # frequency so feedback stays conservative.
    achieved_fmax = min((x[1] for x in frequencies), default=None)
    timing_met = None
    if frequencies:
        timing_met = all(constraint is None or achieved >= constraint for _, achieved, constraint in frequencies)

    utilization = report.get("utilization") or {}
    slices_used, slices_available = _used_available(utilization, ("TRELLIS_SLICE", "SLICE"))
    mult_used, mult_available = _used_available(utilization, ("MULT18X18D", "MULT"))

    cycles = compute_cycles(dims, lanes)
    board_latency = cycles / board_clock_mhz
    pnr_latency = cycles / achieved_fmax if achieved_fmax and achieved_fmax > 0 else None

    return PNRPoint(
        lanes=int(lanes),
        cycles=int(cycles),
        target_mhz=float(target_mhz),
        achieved_fmax_mhz=achieved_fmax,
        timing_met=timing_met,
        board_clock_mhz=float(board_clock_mhz),
        board_clock_core_latency_us=float(board_latency),
        post_route_core_latency_us_at_fmax=float(pnr_latency) if pnr_latency is not None else None,
        slices_used=slices_used,
        slices_available=slices_available,
        multipliers_used=mult_used,
        multipliers_available=mult_available,
        utilization=utilization,
        report_path=str(path),
    )


def collect_pnr_directory(
    root: str | Path,
    *,
    lane_options: tuple[int, ...] = (1, 2, 4, 8, 16),
    dims: tuple[int, ...] = (64, 32, 16, 10),
    target_mhz: float = 100.0,
    board_clock_mhz: float = 25.0,
) -> list[PNRPoint]:
    root = Path(root)
    points: list[PNRPoint] = []
    for lanes in lane_options:
        report = root / f"lane_{lanes}" / "nextpnr_report.json"
        if report.is_file():
            points.append(
                parse_nextpnr_report(
                    report,
                    lanes=lanes,
                    dims=dims,
                    target_mhz=target_mhz,
                    board_clock_mhz=board_clock_mhz,
                )
            )
    return points


def write_feedback(points: list[PNRPoint], out_json: str | Path, out_csv: str | Path | None = None) -> None:
    payload = {
        "schema": "kernellum.pnr_feedback.v1",
        "evidence_level": "post-route implementation estimate; not physical measurement",
        "points": [asdict(p) for p in points],
    }
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n")

    if out_csv is not None:
        out_csv = Path(out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "lanes", "cycles", "target_mhz", "achieved_fmax_mhz", "timing_met",
            "board_clock_mhz", "board_clock_core_latency_us",
            "post_route_core_latency_us_at_fmax", "slices_used", "slices_available",
            "multipliers_used", "multipliers_available",
        ]
        with out_csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for p in points:
                row = asdict(p)
                writer.writerow({k: row.get(k) for k in fields})


def load_feedback(path: str | Path) -> dict[int, dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    return {int(p["lanes"]): p for p in payload.get("points", [])}
