#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
LPF_PATH="$ROOT/boards/ulx3s_85f/kernellum_demo.lpf"
SUMMARY="$ART/pnr_sweep_ulx3s_85f"
mkdir -p "$SUMMARY"

for lanes in 1 2 4 8; do
  echo "=== ULX3S-85F P&R sweep: lanes=$lanes ==="
  DEVICE=85k \
  PACKAGE=CABGA381 \
  LPF="$LPF_PATH" \
  FREQ_MHZ=25 \
  LANES="$lanes" \
  ALLOW_TIMING_FAIL=1 \
  bash "$ROOT/scripts/run_pnr_ecp5.sh"
done

python - <<'PY'
import json, re, shutil
from pathlib import Path
from kernellum.compiler import compute_cycles

root = Path("artifacts/digits_int8")
summary_dir = root / "pnr_sweep_ulx3s_85f"
target_mhz = 25.0
dims = (64, 32, 16, 10)
rows = []

for lanes in (1, 2, 4, 8):
    d = root / f"pnr_ecp5_lanes{lanes}"
    log = (d / "nextpnr.log").read_text(errors="replace")
    matches = re.findall(r"Max frequency for clock .*?:\s*([0-9.]+) MHz \((PASS|FAIL) at ([0-9.]+) MHz\)", log)
    if not matches:
        raise SystemExit(f"could not parse nextpnr Fmax for lanes={lanes}")
    fmax, status, requested = matches[-1]
    fmax = float(fmax)
    cycles = compute_cycles(dims, lanes)
    latency_us_at_25 = cycles / target_mhz
    rows.append({
        "lanes": lanes,
        "cycles": cycles,
        "target_mhz": target_mhz,
        "postroute_fmax_mhz": fmax,
        "timing_met": fmax >= target_mhz,
        "modeled_core_latency_us_at_25mhz": latency_us_at_25,
        "nextpnr_status": status,
    })

feasible = [r for r in rows if r["timing_met"]]
if not feasible:
    (summary_dir / "summary.json").write_text(json.dumps({"target":"ULX3S-85F","results":rows}, indent=2)+"\n")
    raise SystemExit("no swept architecture closes 25 MHz")

selected = min(feasible, key=lambda r: (r["cycles"], r["lanes"]))
payload = {
    "target": "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381",
    "clock_target_mhz": target_mhz,
    "selection_rule": "minimum modeled core cycles among configurations whose post-route Fmax meets the board clock",
    "selected": selected,
    "results": rows,
    "evidence_boundary": "post-route reference-board evidence; not physical-board measurement",
}
(summary_dir / "summary.json").write_text(json.dumps(payload, indent=2)+"\n")

lines = [
    "# ULX3S-85F physical-feedback architecture sweep",
    "",
    "| lanes | modeled cycles | post-route Fmax | closes 25 MHz | modeled core latency @25 MHz |",
    "|---:|---:|---:|:---:|---:|",
]
for r in rows:
    lines.append(f'| {r["lanes"]} | {r["cycles"]} | {r["postroute_fmax_mhz"]:.2f} MHz | {"yes" if r["timing_met"] else "no"} | {r["modeled_core_latency_us_at_25mhz"]:.2f} µs |')
lines += [
    "",
    f'**Selected:** {selected["lanes"]} lanes — fastest modeled configuration that closes the 25 MHz reference-board target.',
    "",
    "This is post-route reference-target evidence, not measured physical-board latency or power.",
]
(summary_dir / "SUMMARY.md").write_text("\n".join(lines)+"\n")

src = root / f'pnr_ecp5_lanes{selected["lanes"]}' / "kernellum_demo_top.config"
shutil.copy2(src, summary_dir / "selected.config")
print(f'KERNELLUM_PNR_SELECTED lanes={selected["lanes"]} fmax_mhz={selected["postroute_fmax_mhz"]:.2f} cycles={selected["cycles"]} latency_us_at_25mhz={selected["modeled_core_latency_us_at_25mhz"]:.2f}')
PY

if ! command -v ecppack >/dev/null; then
  echo "error: ecppack is required for bitstream generation" >&2
  exit 2
fi

ecppack "$SUMMARY/selected.config" "$SUMMARY/kernellum_demo_top.bit"

echo "ULX3S-85F physical-feedback sweep + selected bitstream complete."
echo "Physical board loading and measurement remain separate evidence steps."
