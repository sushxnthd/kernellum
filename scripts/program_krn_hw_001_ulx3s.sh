#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <kernellum_demo_top.bit> <measurement-session-dir>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BITSTREAM="$(realpath "$1")"
SESSION="$2"
REFERENCE_SHA256="19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415"
REFERENCE_WORKFLOW_RUN="35321132327"

if [[ -f "$SCRIPT_DIR/krn_hw_001.py" ]]; then
  HW_TOOL="$SCRIPT_DIR/krn_hw_001.py"
elif [[ -f "$ROOT/scripts/krn_hw_001.py" ]]; then
  HW_TOOL="$ROOT/scripts/krn_hw_001.py"
else
  echo "error: krn_hw_001.py was not found beside this script or under $ROOT/scripts" >&2
  exit 2
fi

if [[ ! -f "$BITSTREAM" ]]; then
  echo "error: bitstream not found: $BITSTREAM" >&2
  exit 2
fi
if ! command -v openFPGALoader >/dev/null; then
  echo "error: openFPGALoader is required" >&2
  exit 2
fi

actual_sha256="$(python "$HW_TOOL" hash "$BITSTREAM")"
if [[ "$actual_sha256" != "$REFERENCE_SHA256" && "${ALLOW_NONREFERENCE_BITSTREAM:-0}" != "1" ]]; then
  echo "error: bitstream SHA-256 does not match frozen KRN-PNR-001 reference" >&2
  echo "expected: $REFERENCE_SHA256" >&2
  echo "actual:   $actual_sha256" >&2
  echo "set ALLOW_NONREFERENCE_BITSTREAM=1 only for an explicitly documented alternate-build session" >&2
  exit 2
fi

python "$HW_TOOL" init --out "$SESSION" --bitstream "$BITSTREAM"

set +e
openFPGALoader --board=ulx3s "$BITSTREAM" 2>&1 | tee "$SESSION/programming.log"
program_rc=${PIPESTATUS[0]}
set -e

python - "$SESSION/metadata.json" "$program_rc" "$BITSTREAM" "$actual_sha256" "$REFERENCE_SHA256" "$REFERENCE_WORKFLOW_RUN" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

meta_path = Path(sys.argv[1])
rc = int(sys.argv[2])
bitstream = sys.argv[3]
actual_sha256 = sys.argv[4]
reference_sha256 = sys.argv[5]
reference_workflow_run = sys.argv[6]
meta = json.loads(meta_path.read_text())
meta["programming_command"] = f"openFPGALoader --board=ulx3s {bitstream}"
meta["programming_exit_code"] = rc
meta["programming_success"] = rc == 0
meta["programmed_utc"] = datetime.now(timezone.utc).isoformat()
meta["bitstream_path"] = bitstream
meta["bitstream_sha256"] = actual_sha256
meta["reference_bitstream_sha256"] = reference_sha256
meta["reference_bitstream_match"] = actual_sha256 == reference_sha256
if actual_sha256 == reference_sha256:
    meta["ci_workflow_run"] = reference_workflow_run
meta_path.write_text(json.dumps(meta, indent=2) + "\n")
PY

if [[ "$program_rc" -ne 0 ]]; then
  echo "KRN-HW-001 programming failed (exit $program_rc)." >&2
  exit "$program_rc"
fi

echo "KRN-HW-001 SRAM programming complete."
echo "Next: observe the class LEDs and run:"
echo "  python $HW_TOOL record-functional $SESSION <observed-class>"
echo "Then populate latency_us.csv, idle_power.csv and active_power.csv."
