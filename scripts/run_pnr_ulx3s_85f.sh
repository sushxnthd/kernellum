#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
LPF_PATH="$ROOT/boards/ulx3s_85f/kernellum_demo.lpf"

DEVICE=85k PACKAGE=CABGA381 LPF="$LPF_PATH" FREQ_MHZ=25 bash "$ROOT/scripts/run_pnr_ecp5.sh"

if ! command -v ecppack >/dev/null; then
  echo "error: ecppack is required for ULX3S bitstream generation" >&2
  exit 2
fi

ecppack   "$ART/pnr_ecp5/kernellum_demo_top.config"   "$ART/pnr_ecp5/kernellum_demo_top.bit"

echo
echo "ULX3S-85F reference P&R + bitstream generation complete."
echo "This is a board-targeted build artifact, not physical-board validation."
