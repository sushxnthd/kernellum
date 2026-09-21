#!/usr/bin/env bash
set -euo pipefail

# The pinned OpenROAD binary is built for x86-64 but executes an unsupported
# instruction in report_checks on some heterogeneous public-runner CPUs. Run
# only that reporting stage through a deterministic emulated CPU model.  The
# tools/OpenROAD path printed by env.sh is a launcher; QEMU linux-user must be
# given the installed ELF itself.
openroad_elf=/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad
if [[ ! -x "$openroad_elf" ]]; then
  echo "OpenROAD ELF not found or not executable: $openroad_elf" >&2
  exit 127
fi

exec /usr/local/bin/qemu-x86_64-static -L / -cpu max "$openroad_elf" "$@"
