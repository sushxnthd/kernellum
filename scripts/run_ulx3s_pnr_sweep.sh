#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
BOARD="$ROOT/boards/ulx3s"
OUT="$ART/pnr_ulx3s"
LANES_LIST="${LANES_LIST:-1 2 4 8 16}"
TARGET_MHZ="${TARGET_MHZ:-100}"
BOARD_CLOCK_MHZ="${BOARD_CLOCK_MHZ:-25}"

for tool in yosys nextpnr-ecp5 ecppack; do
  if ! command -v "$tool" >/dev/null; then
    echo "error: $tool is required" >&2
    exit 2
  fi
done

mkdir -p "$OUT"
# Keep the physical-board LPF at its real 25 MHz clock, but remove only its
# FREQUENCY line for the implementation-frequency sweep so --freq drives timing.
grep -v '^FREQUENCY PORT "clk_25mhz"' "$BOARD/kernellum_ulx3s.lpf" > "$OUT/kernellum_ulx3s_timing.lpf"

cd "$ART"

for lanes in $LANES_LIST; do
  lane_out="$OUT/lane_$lanes"
  mkdir -p "$lane_out"
  echo "=== Kernellum ULX3S P&R: LANES=$lanes target=$TARGET_MHZ MHz ==="

  yosys -p "read_verilog -sv kernellum_mlp_accel.sv kernellum_demo_top.sv $BOARD/kernellum_ulx3s_top.sv;     chparam -set LANES $lanes kernellum_ulx3s_top;     hierarchy -top kernellum_ulx3s_top;     synth_ecp5 -top kernellum_ulx3s_top -json '$lane_out/design.json';     check; stat" | tee "$lane_out/yosys.log"

  nextpnr-ecp5     --85k     --package CABGA381     --speed 6     --json "$lane_out/design.json"     --lpf "$OUT/kernellum_ulx3s_timing.lpf"     --freq "$TARGET_MHZ"     --timing-allow-fail     --textcfg "$lane_out/design.config"     --report "$lane_out/nextpnr_report.json"     --placed-svg "$lane_out/placed.svg"     --routed-svg "$lane_out/routed.svg"     2>&1 | tee "$lane_out/nextpnr.log"

  ecppack "$lane_out/design.config" "$lane_out/kernellum_ulx3s_85f.bit"
done

cd "$ROOT"
python scripts/collect_pnr_feedback.py   --root "$OUT"   --target-mhz "$TARGET_MHZ"   --board-clock-mhz "$BOARD_CLOCK_MHZ"

echo "ULX3S lane-sweep P&R complete. Results are post-route estimates, not physical measurements."
