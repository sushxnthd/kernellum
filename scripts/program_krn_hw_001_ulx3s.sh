#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <kernellum_demo_top.bit> <measurement-session-dir>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BITSTREAM="$(realpath "$1")"
SESSION="$2"
REFERENCE_SHA256="19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415"

if [[ ! -f "$BITSTREAM" ]]; then
  echo "error: bitstream not found: $BITSTREAM" >&2
  exit 2
fi
if ! command -v openFPGALoader >/dev/null; then
  echo "error: openFPGALoader is required" >&2
  exit 2
fi

actual_sha256="$(python "$ROOT/scripts/krn_hw_001.py" hash "$BITSTREAM")"
if [[ "$actual_sha256" != "$REFERENCE_SHA256" && "${ALLOW_NONREFERENCE_BITSTREAM:-0}" != "1" ]]; then
  echo "error: bitstream SHA-256 does not match frozen KRN-PNR-001 reference" >&2
  echo "expected: $REFERENCE_SHA256" >&2
  echo "actual:   $actual_sha256" >&2
  echo "set ALLOW_NONREFERENCE_BITSTREAM=1 only for an explicitly documented alternate-build session" >&2
  exit 2
fi

python "$ROOT/scripts/krn_hw_001.py" init --out "$SESSION" --bitstream "$BITSTREAM"

set +e
openFPGALoader --board=ulx3s "$BITSTREAM" 2>&1 | tee "$SESSION/programming.log"
program_rc=${PIPESTATUS[0]}
set -e

python - "$SESSION/metadata.json" "$program_rc" "$BITSTREAM" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

meta_path = Path(sys.argv[1])
rc = int(sys.argv[2])
bitstream = sys.argv[3]
meta = json.loads(meta_path.read_text())
meta["programming_command"] = f"openFPGALoader --board=ulx3s {bitstream}"
meta["programming_exit_code"] = rc
meta["programming_success"] = rc == 0
meta["programmed_utc"] = datetime.now(timezone.utc).isoformat()
meta_path.write_text(json.dumps(meta, indent=2) + "\n")
PY

if [[ "$program_rc" -ne 0 ]]; then
  echo "KRN-HW-001 programming failed (exit $program_rc)." >&2
  exit "$program_rc"
fi

echo "KRN-HW-001 SRAM programming complete."
echo "Next: perform the class-8 functional check, then populate latency_us.csv, idle_power.csv and active_power.csv."
