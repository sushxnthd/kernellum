#!/usr/bin/env bash
set -euo pipefail

# ORFS launches Kepler Formal as a child of OpenROAD during final reporting.
# Run that bundled ELF under the same portable CPU model as OpenROAD so the
# LEC gate cannot escape emulation on heterogeneous public runners.
kepler_elf=/OpenROAD-flow-scripts/tools/install/kepler-formal/bin/kepler-formal
if [[ ! -x "$kepler_elf" ]]; then
  echo "Kepler Formal ELF not found or not executable: $kepler_elf" >&2
  exit 127
fi

echo "Kernellum QEMU Kepler: $kepler_elf" >&2
exec /usr/local/bin/qemu-x86_64-static -strace -L / -cpu max "$kepler_elf" "$@"
