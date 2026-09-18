from __future__ import annotations

import argparse
from pathlib import Path

from kernellum.pnr_feedback import collect_pnr_directory, write_feedback


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ULX3S nextpnr lane-sweep feedback")
    parser.add_argument("--root", default="artifacts/digits_int8/pnr_ulx3s")
    parser.add_argument("--target-mhz", type=float, default=100.0)
    parser.add_argument("--board-clock-mhz", type=float, default=25.0)
    args = parser.parse_args()

    root = Path(args.root)
    points = collect_pnr_directory(
        root,
        target_mhz=args.target_mhz,
        board_clock_mhz=args.board_clock_mhz,
    )
    if not points:
        raise SystemExit("no nextpnr reports found")

    write_feedback(points, root / "implementation_feedback.json", root / "implementation_feedback.csv")
    for p in points:
        print(
            f"LANES={p.lanes} cycles={p.cycles} fmax={p.achieved_fmax_mhz} "
            f"pnr_latency_us={p.post_route_core_latency_us_at_fmax} "
            f"slices={p.slices_used} mult={p.multipliers_used}"
        )


if __name__ == "__main__":
    main()
