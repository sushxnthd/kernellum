#!/usr/bin/env python3
"""Opened-geometry canary for deterministic headless final-report completion."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from scripts import similarity_asic_transfer_route as common


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
REMOVED = """# Save a final image if openroad is compiled with the gui
if { [ord::openroad_gui_compiled] } {
  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false
}
"""
REPLACEMENT = """# Optional GUI images intentionally disabled for deterministic headless evidence.
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_flow(flow_root: Path, manifest_path: Path) -> None:
    target = flow_root / "scripts" / "final_outputs.tcl"
    before = target.read_bytes()
    needle = REMOVED.encode()
    count = before.count(needle)
    if count != 1:
        raise RuntimeError(f"expected one frozen GUI block, found {count}")
    after = before.replace(needle, REPLACEMENT.encode(), 1)
    target.write_bytes(after)
    manifest = {
        "schema_version": 1,
        "orfs_image": IMAGE,
        "workflow_source_sha": os.environ.get("GITHUB_SHA", "local"),
        "target": "flow/scripts/final_outputs.tcl",
        "replacement_count": count,
        "before_sha256": digest(before),
        "after_sha256": digest(after),
        "removed_text": REMOVED,
        "replacement_text": REPLACEMENT,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-root", type=Path, required=True)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = parser.parse_args()

    output_dir = ROOT / "results" / "similarity_final_report_canary"
    manifest = output_dir / "flow_patch_manifest.json"
    patch_flow(args.flow_root.resolve(), manifest)

    common.BUILD = ROOT / "build" / "similarity_final_report_canary"
    row = common.route_one(
        "sky130hd", "opened_canary", "blocal", 173, 8, 6,
        args.flow_root.resolve(), args.qemu.resolve(),
        "/work/asic/blocal/config_sky130hd.mk",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "similarity_final_report_canary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=common.FIELDS)
        writer.writeheader()
        writer.writerow(row)
    print(json.dumps({key: row[key] for key in (
        "platform", "topology", "rows", "cols", "seed", "route_ok", "error_stage"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
