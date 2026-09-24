#!/usr/bin/env python3
"""Synthesis-only canary for preserved B-local/A-sign-local transport."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts.similarity_asic_transfer_route import IMAGE, parse_synthesis

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DFFS = {(5, 8): 1979, (8, 5): 1972}
LOCAL_DFFS = {(5, 8): 2284, (8, 5): 2232}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("nangate45", "sky130hd"), required=True)
    parser.add_argument("--rows", choices=(5, 8), type=int, required=True)
    parser.add_argument("--cols", choices=(5, 8), type=int, required=True)
    parser.add_argument("--flow-root", type=Path, required=True)
    args = parser.parse_args()
    if (args.rows, args.cols) not in EXPECTED_DFFS:
        parser.error("only opened 5x8 and 8x5 shapes are permitted")
    flow = args.flow_root.resolve()
    config = f"/work/asic/blocal/config_{args.platform}.mk"
    common = (
        f"DESIGN_CONFIG={config} DESIGN_NAME=similarity_asic_transfer_blocal "
        f"VERILOG_DEFINES='-D ASIC_ROWS={args.rows} -D ASIC_COLS={args.cols}'"
    )
    command = [
        "docker", "run", "--rm", "-v", f"{ROOT}:/work:ro",
        "-v", f"{flow}:/OpenROAD-flow-scripts/flow", IMAGE,
        "bash", "-lc", "source /OpenROAD-flow-scripts/env.sh && "
        "cd /OpenROAD-flow-scripts/flow && " f"make {common} synth",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=1800, check=False,
    )
    output_dir = ROOT / "results" / "similarity_blocal_preservation"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.platform}_{args.rows}x{args.cols}"
    (output_dir / f"{stem}.log").write_text(completed.stdout, encoding="utf-8")
    result = {
        "platform": args.platform, "rows": args.rows, "cols": args.cols,
        "source_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "synth_exit_code": completed.returncode,
        "expected_dffs": EXPECTED_DFFS[args.rows, args.cols],
        "local_dffs": LOCAL_DFFS[args.rows, args.cols],
    }
    report = (flow / "reports" / args.platform /
              "similarity_asic_transfer_blocal" / "base" / "synth_stat.txt")
    if completed.returncode == 0 and report.exists():
        result.update(parse_synthesis(report))
    result["replicas_preserved"] = (
        result.get("dff_cells") == result["expected_dffs"]
        and result.get("dff_cells", result["local_dffs"]) <= .90*result["local_dffs"]
    )
    (output_dir / f"{stem}.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return 0 if result["replicas_preserved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
