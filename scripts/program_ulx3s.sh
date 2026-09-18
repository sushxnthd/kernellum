#!/usr/bin/env bash
set -euo pipefail

BIT="${1:-artifacts/digits_int8/pnr_ulx3s/lane_4/kernellum_ulx3s_85f.bit}"

if [[ ! -f "$BIT" ]]; then
  echo "error: bitstream not found: $BIT" >&2
  exit 2
fi

if command -v openFPGALoader >/dev/null; then
  exec openFPGALoader --board=ulx3s "$BIT"
elif command -v fujprog >/dev/null; then
  exec fujprog "$BIT"
else
  echo "error: install openFPGALoader or fujprog, then rerun." >&2
  echo "This script programs ULX3S SRAM only; it does not write flash." >&2
  exit 2
fi
