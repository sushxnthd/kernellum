#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART_ROOT="$ROOT/artifacts/benchmark_matrix"
OUT_ROOT="$ROOT/artifacts/benchmark_pnr_ulx3s_85f"
LPF_PATH="$ROOT/boards/ulx3s_85f/kernellum_demo.lpf"
TARGET_MHZ=25

if [[ ! -f "$ART_ROOT/summary.json" ]]; then
  echo "error: benchmark matrix artifacts missing; run python scripts/build_benchmark_matrix.py first" >&2
  exit 2
fi

for tool in yosys nextpnr-ecp5 ecppack; do
  if ! command -v "$tool" >/dev/null; then
    echo "error: $tool is required" >&2
    exit 2
  fi
done

rm -rf "$OUT_ROOT"
mkdir -p "$OUT_ROOT"

mapfile -t CASES < <(
  cd "$ROOT"
  python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("artifacts/benchmark_matrix/summary.json").read_text())
for case in payload["cases"]:
    print(case["case"])
PY
)

for case_name in "${CASES[@]}"; do
  CASE_DIR="$ART_ROOT/$case_name"
  if [[ ! -f "$CASE_DIR/kernellum_dense3_accel.sv" || ! -f "$CASE_DIR/kernellum_demo_top.sv" ]]; then
    echo "error: generated RTL missing for $case_name" >&2
    exit 2
  fi

  for lanes in 1 2 4 8; do
    echo "=== KRN-BENCH-001: case=$case_name lanes=$lanes ==="
    OUT="$OUT_ROOT/$case_name/lanes$lanes"
    mkdir -p "$OUT"

    (
      cd "$CASE_DIR"
      yosys -p "read_verilog -sv kernellum_dense3_accel.sv kernellum_demo_top.sv; chparam -set ACCEL_LANES $lanes kernellum_demo_top; synth_ecp5 -top kernellum_demo_top -json $OUT/kernellum_demo_top.json; stat; check" \
        | tee "$OUT/yosys.log"

      set +e
      nextpnr-ecp5 \
        --85k \
        --package CABGA381 \
        --json "$OUT/kernellum_demo_top.json" \
        --lpf "$LPF_PATH" \
        --freq "$TARGET_MHZ" \
        --timing-allow-fail \
        --textcfg "$OUT/kernellum_demo_top.config" \
        2>&1 | tee "$OUT/nextpnr.log"
      route_rc=${PIPESTATUS[0]}
      set -e
      echo "$route_rc" > "$OUT/route_exit_code.txt"
    )
  done
done

cd "$ROOT"
python - <<'PY'
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from kernellum.compiler import compute_cycles

matrix_path = Path("artifacts/benchmark_matrix/summary.json")
out_root = Path("artifacts/benchmark_pnr_ulx3s_85f")
target_mhz = 25.0
matrix = json.loads(matrix_path.read_text())
aggregate = []

def parse_fmax(text: str):
    matches = re.findall(
        r"Max frequency for clock .*?:\s*([0-9.]+) MHz \((PASS|FAIL) at ([0-9.]+) MHz\)",
        text,
    )
    if not matches:
        return None, "ROUTE_FAIL"
    fmax, status, _ = matches[-1]
    return float(fmax), status

def parse_primitive(nextpnr_text: str, yosys_text: str, primitive: str):
    m = re.search(rf"{re.escape(primitive)}\s*:\s*([0-9,]+)\s*/\s*([0-9,]+)", nextpnr_text)
    if m:
        return {"used": int(m.group(1).replace(",", "")), "total": int(m.group(2).replace(",", ""))}
    m = re.search(rf"^\s*{re.escape(primitive)}\s+([0-9,]+)\s*$", yosys_text, re.MULTILINE)
    if m:
        return {"used": int(m.group(1).replace(",", "")), "total": None}
    return {"used": None, "total": None}

for case in matrix["cases"]:
    case_name = case["case"]
    dims = tuple(int(x) for x in case["dims"])
    rows = []

    for lanes in (1, 2, 4, 8):
        d = out_root / case_name / f"lanes{lanes}"
        nextpnr_text = (d / "nextpnr.log").read_text(errors="replace")
        yosys_text = (d / "yosys.log").read_text(errors="replace")
        route_exit_code = int((d / "route_exit_code.txt").read_text().strip())
        fmax, status = parse_fmax(nextpnr_text)
        cycles = compute_cycles(dims, lanes)
        route_success = route_exit_code == 0 and fmax is not None

        row = {
            "lanes": lanes,
            "modeled_cycles": cycles,
            "modeled_core_latency_us_at_25mhz": cycles / target_mhz,
            "route_success": route_success,
            "route_exit_code": route_exit_code,
            "postroute_fmax_mhz": fmax,
            "timing_met_25mhz": bool(route_success and fmax >= target_mhz),
            "nextpnr_status": status,
            "resources": {
                "TRELLIS_COMB": parse_primitive(nextpnr_text, yosys_text, "TRELLIS_COMB"),
                "TRELLIS_FF": parse_primitive(nextpnr_text, yosys_text, "TRELLIS_FF"),
                "TRELLIS_RAMW": parse_primitive(nextpnr_text, yosys_text, "TRELLIS_RAMW"),
                "MULT18X18D": parse_primitive(nextpnr_text, yosys_text, "MULT18X18D"),
            },
        }
        rows.append(row)

    feasible = [r for r in rows if r["timing_met_25mhz"]]
    selected = min(feasible, key=lambda r: (r["modeled_cycles"], r["lanes"])) if feasible else None

    case_out = out_root / case_name
    if selected is not None:
        selected_dir = case_out / f'lanes{selected["lanes"]}'
        selected_config = case_out / "selected.config"
        selected_bit = case_out / "kernellum_demo_top.bit"
        shutil.copy2(selected_dir / "kernellum_demo_top.config", selected_config)
        subprocess.run(["ecppack", str(selected_config), str(selected_bit)], check=True)
        selected["bitstream_sha256"] = hashlib.sha256(selected_bit.read_bytes()).hexdigest()

    payload = {
        "evidence_id": "KRN-BENCH-001",
        "case": case_name,
        "dims": list(dims),
        "target": "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381",
        "clock_target_mhz": target_mhz,
        "selection_rule": (
            "minimum modeled core cycles among swept configurations whose post-route Fmax meets the 25 MHz board clock"
        ),
        "selected": selected,
        "results": rows,
        "evidence_boundary": (
            "post-route reference-board evidence on deterministic synthetic dense graphs; "
            "not physical-board measurement and not external workload validation"
        ),
    }
    (case_out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        f"# KRN-BENCH-001 — {case_name}",
        "",
        f'Network shape: **{" → ".join(str(x) for x in dims)}**',
        "",
        "| lanes | modeled cycles | post-route Fmax | closes 25 MHz | modeled core latency @25 MHz | TRELLIS_COMB | MULT18X18D |",
        "|---:|---:|---:|:---:|---:|---:|---:|",
    ]
    for r in rows:
        comb = r["resources"]["TRELLIS_COMB"]["used"]
        dsp = r["resources"]["MULT18X18D"]["used"]
        fmax_text = (
            f'{r["postroute_fmax_mhz"]:.2f} MHz'
            if r["postroute_fmax_mhz"] is not None
            else "route fail"
        )
        lines.append(
            f'| {r["lanes"]} | {r["modeled_cycles"]} | {fmax_text} | '
            f'{"yes" if r["timing_met_25mhz"] else "no"} | {r["modeled_core_latency_us_at_25mhz"]:.2f} µs | '
            f'{comb if comb is not None else "n/a"} | {dsp if dsp is not None else "n/a"} |'
        )
    lines += [""]

    if selected is None:
        lines.append("**Selected:** none of the swept 1/2/4/8-lane variants closes 25 MHz.")
    else:
        lines.append(
            f'**Selected:** {selected["lanes"]} lanes at {selected["postroute_fmax_mhz"]:.2f} MHz post-route Fmax.'
        )
    lines += [
        "",
        "This is board-targeted place-and-route evidence. It is not measured physical-board latency, power, or energy.",
        "",
    ]
    (case_out / "SUMMARY.md").write_text("\n".join(lines))
    aggregate.append(payload)

aggregate_payload = {
    "evidence_id": "KRN-BENCH-001",
    "title": "Multi-workload physical-feedback benchmark",
    "target": "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381",
    "clock_target_mhz": target_mhz,
    "workloads": aggregate,
    "claim_boundary": (
        "The workloads are deterministic synthetic dense graphs chosen to test compiler and physical-feedback behavior "
        "across shapes. Results establish board-targeted P&R evidence only; they do not establish customer validation "
        "or physical-board measurements."
    ),
}
(out_root / "summary.json").write_text(json.dumps(aggregate_payload, indent=2) + "\n")

lines = [
    "# KRN-BENCH-001 — Multi-workload physical-feedback benchmark",
    "",
    "Three deterministic dense-network shapes are each swept across 1/2/4/8 MAC lanes using the same "
    "ULX3S-85F package, pin constraints and 25 MHz clock target.",
    "",
    "| workload | shape | selected lanes | selected Fmax | selected cycles | status |",
    "|---|---|---:|---:|---:|---|",
]
for payload in aggregate:
    selected = payload["selected"]
    shape = " → ".join(str(x) for x in payload["dims"])
    if selected is None:
        lines.append(f'| {payload["case"]} | {shape} | — | — | — | no swept variant closes 25 MHz |')
    else:
        lines.append(
            f'| {payload["case"]} | {shape} | {selected["lanes"]} | '
            f'{selected["postroute_fmax_mhz"]:.2f} MHz | {selected["modeled_cycles"]} | timing-feasible |'
        )
lines += [
    "",
    "## Selection rule",
    "",
    "For each workload, choose the minimum modeled cycle count among the swept architectures whose "
    "post-route Fmax meets the board's 25 MHz clock.",
    "",
    "## Evidence boundary",
    "",
    "These are deterministic synthetic dense graphs. The benchmark tests whether compiler decisions remain "
    "physically constrained across multiple shapes. It is not an external design-partner workload and does not "
    "claim measured FPGA latency, throughput, power, or energy.",
    "",
]
(out_root / "SUMMARY.md").write_text("\n".join(lines))
print("KERNELLUM_MULTIWORKLOAD_PNR_PASS workloads=%d" % len(aggregate))
PY

echo "KRN-BENCH-001 multi-workload ULX3S-85F P&R sweep complete."
