#!/usr/bin/env bash
set -euo pipefail

# The pinned OpenROAD binary is built for x86-64 but executes an unsupported
# instruction in report_checks on some heterogeneous public-runner CPUs. Run
# only that reporting stage through a deterministic emulated CPU model.
exec /usr/local/bin/qemu-x86_64-static -cpu max \
  /OpenROAD-flow-scripts/tools/OpenROAD "$@"
