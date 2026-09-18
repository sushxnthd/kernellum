#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
LANES="${LANES:-}"
OUT_SUFFIX=""
if [[ -n "$LANES" ]]; then OUT_SUFFIX="_lanes$LANES"; fi
OUT="$ART/pnr_ecp5$OUT_SUFFIX"
mkdir -p "$OUT"

DEVICE="${DEVICE:-85k}"
PACKAGE="${PACKAGE:-}"
LPF="${LPF:-}"
FREQ_MHZ="${FREQ_MHZ:-}"

if ! command -v yosys >/dev/null; then
  echo "error: yosys is required" >&2; exit 2
fi
if ! command -v nextpnr-ecp5 >/dev/null; then
  echo "error: nextpnr-ecp5 is required" >&2; exit 2
fi
if [[ -z "$PACKAGE" || -z "$LPF" || -z "$FREQ_MHZ" ]]; then
  cat >&2 <<'EOF'
Kernellum physical P&R scaffold

Required environment variables:
  PACKAGE   exact ECP5 package for the board
  LPF       path to the board pin/clock constraint file
  FREQ_MHZ  target clock frequency for timing analysis

Optional:
  DEVICE    ECP5 density selector (default: 85k)

Example only after a real board is selected:
  PACKAGE=<package> LPF=<board.lpf> FREQ_MHZ=<clock> bash scripts/run_pnr_ecp5.sh

This script intentionally refuses to invent a board/package/clock.
EOF
  exit 2
fi

cd "$ART"

CHPARAM=""
if [[ -n "$LANES" ]]; then
  CHPARAM="chparam -set ACCEL_LANES $LANES kernellum_demo_top;"
fi

yosys -p "read_verilog -sv kernellum_mlp_accel.sv kernellum_demo_top.sv; $CHPARAM synth_ecp5 -top kernellum_demo_top -json $OUT/kernellum_demo_top.json; stat; check" \
  | tee "$OUT/yosys.log"

TIMING_FLAG=()
if [[ "${ALLOW_TIMING_FAIL:-0}" == "1" ]]; then
  TIMING_FLAG+=(--timing-allow-fail)
fi

nextpnr-ecp5 \
  --"$DEVICE" \
  --package "$PACKAGE" \
  --json "$OUT/kernellum_demo_top.json" \
  --lpf "$LPF" \
  --freq "$FREQ_MHZ" \
  "${TIMING_FLAG[@]}" \
  --textcfg "$OUT/kernellum_demo_top.config" \
  2>&1 | tee "$OUT/nextpnr.log"

echo
echo "P&R complete. This establishes place-and-route evidence only."
echo "Board loading, measured latency, power, and energy remain separate evidence steps."
