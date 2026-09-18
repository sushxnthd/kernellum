#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/external_tiny_npu"
OUT_ROOT="$ART/pnr_ulx3s_85f"
LPF_PATH="$ROOT/boards/ulx3s_85f/kernellum_demo.lpf"
TARGET_MHZ=25

if [[ ! -f "$ART/manifest.json" || ! -f "$ART/kernellum_dense3_accel.sv" || ! -f "$ART/kernellum_demo_top.sv" ]]; then
  echo "error: external workload artifacts missing; run python scripts/build_external_tiny_npu.py first" >&2
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

for lanes in 1 2 4 8; do
  echo "=== KRN-EXT-001: tiny-NPU overlap_perf_test lanes=$lanes ==="
  OUT="$OUT_ROOT/lanes$lanes"
  mkdir -p "$OUT"

  (
    cd "$ART"
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

art = Path("artifacts/external_tiny_npu")
out_root = art / "pnr_ulx3s_85f"
manifest = json.loads((art / "manifest.json").read_text())
dims = tuple(int(x) for x in manifest["ir"]["dims"])
target_mhz = 25.0


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
    match = re.search(
        rf"{re.escape(primitive)}\s*:\s*([0-9,]+)\s*/\s*([0-9,]+)",
        nextpnr_text,
    )
    if match:
        return {
            "used": int(match.group(1).replace(",", "")),
            "total": int(match.group(2).replace(",", "")),
        }

    match = re.search(
        rf"^\s*{re.escape(primitive)}\s+([0-9,]+)\s*$",
        yosys_text,
        re.MULTILINE,
    )
    if match:
        return {"used": int(match.group(1).replace(",", "")), "total": None}
    return {"used": None, "total": None}


rows = []
for lanes in (1, 2, 4, 8):
    d = out_root / f"lanes{lanes}"
    nextpnr_text = (d / "nextpnr.log").read_text(errors="replace")
    yosys_text = (d / "yosys.log").read_text(errors="replace")
    route_exit_code = int((d / "route_exit_code.txt").read_text().strip())
    fmax, status = parse_fmax(nextpnr_text)
    route_success = route_exit_code == 0 and fmax is not None
    cycles = compute_cycles(dims, lanes)

    rows.append(
        {
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
    )

feasible = [row for row in rows if row["timing_met_25mhz"]]
selected = (
    min(feasible, key=lambda row: (row["modeled_cycles"], row["lanes"]))
    if feasible
    else None
)

if selected is not None:
    selected_dir = out_root / f'lanes{selected["lanes"]}'
    selected_config = out_root / "selected.config"
    selected_bit = out_root / "kernellum_demo_top.bit"
    shutil.copy2(selected_dir / "kernellum_demo_top.config", selected_config)
    subprocess.run(["ecppack", str(selected_config), str(selected_bit)], check=True)
    selected["bitstream_sha256"] = hashlib.sha256(selected_bit.read_bytes()).hexdigest()

payload = {
    "evidence_id": "KRN-EXT-001",
    "workload": "tiny-NPU overlap_perf_test",
    "upstream": manifest["upstream"],
    "dims": list(dims),
    "target": "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381",
    "clock_target_mhz": target_mhz,
    "selection_rule": (
        "minimum modeled core cycles among 1/2/4/8-lane configurations "
        "whose post-route Fmax meets the 25 MHz board clock"
    ),
    "selected": selected,
    "results": rows,
    "evidence_boundary": (
        "third-party public model graph/weights with Kernellum-generated synthetic "
        "calibration/golden inputs; board-targeted P&R evidence, not application "
        "accuracy, customer validation, or physical-board measurement"
    ),
}
(out_root / "summary.json").write_text(json.dumps(payload, indent=2) + chr(10))

lines = [
    "# KRN-EXT-001 — tiny-NPU external workload",
    "",
    "Pinned third-party model: **tiny-NPU / overlap_perf_test.onnx**",
    "",
    f'Network: **{" → ".join(str(x) for x in dims)}**',
    "",
    "| lanes | modeled cycles | post-route Fmax | closes 25 MHz | modeled latency @25 MHz | TRELLIS_COMB | MULT18X18D |",
    "|---:|---:|---:|:---:|---:|---:|---:|",
]

for row in rows:
    comb = row["resources"]["TRELLIS_COMB"]["used"]
    dsp = row["resources"]["MULT18X18D"]["used"]
    if row["postroute_fmax_mhz"] is None:
        fmax_text = "route fail"
    else:
        fmax_text = f'{row["postroute_fmax_mhz"]:.2f} MHz'
    lines.append(
        f'| {row["lanes"]} | {row["modeled_cycles"]} | {fmax_text} | '
        f'{"yes" if row["timing_met_25mhz"] else "no"} | '
        f'{row["modeled_core_latency_us_at_25mhz"]:.2f} µs | '
        f'{comb if comb is not None else "n/a"} | '
        f'{dsp if dsp is not None else "n/a"} |'
    )

lines.extend([""])
if selected is None:
    lines.append("**Selected:** no swept 1/2/4/8-lane design closes 25 MHz.")
else:
    lines.append(
        f'**Selected:** {selected["lanes"]} lanes; '
        f'{selected["postroute_fmax_mhz"]:.2f} MHz post-route Fmax; '
        f'{selected["modeled_cycles"]} modeled cycles.'
    )

lines.extend(
    [
        "",
        "## Evidence boundary",
        "",
        "The ONNX graph and weights are the pinned third-party upstream artifact. "
        "Kernellum supplies deterministic synthetic calibration/golden inputs because "
        "the upstream performance-test model does not include an application dataset.",
        "",
        "This result does not claim application accuracy, customer validation, measured "
        "FPGA latency, measured power, or measured energy.",
        "",
    ]
)
(out_root / "SUMMARY.md").write_text(chr(10).join(lines))

print(
    "KERNELLUM_EXT001_PNR_COMPLETE "
    + (
        "selected=none"
        if selected is None
        else f'selected_lanes={selected["lanes"]} fmax={selected["postroute_fmax_mhz"]:.2f}'
    )
)
PY

echo "KRN-EXT-001 external workload P&R sweep complete."
