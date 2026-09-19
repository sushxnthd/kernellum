#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "k2_evn"
LPF = ROOT / "boards" / "ecp5_evn" / "k2.lpf"

VARIANTS = (
    {"name": "baseline_r08_c08_k32", "rows": 8, "cols": 8, "k_tile": 32},
    {"name": "active_r10_c12_k32", "rows": 10, "cols": 12, "k_tile": 32},
    {"name": "active_r08_c14_k64", "rows": 8, "cols": 14, "k_tile": 64},
)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_variant(v: dict) -> dict:
    d = BUILD / v["name"]
    d.mkdir(parents=True, exist_ok=True)
    design_json = d / "design.json"
    config = d / "design.config"
    bitstream = d / f"{v['name']}.bit"

    params = (
        f"chparam -set ROWS {v['rows']} -set COLS {v['cols']} "
        f"-set K_TILE {v['k_tile']} kernellum_k2_board_top"
    )
    script = (
        "read_verilog -sv rtl/kernellum_mac_array.sv "
        "rtl/kernellum_gemm_engine.sv "
        "rtl/kernellum_uart_rx.sv rtl/kernellum_uart_tx.sv "
        "rtl/kernellum_k2_board_top.sv; "
        f"{params}; hierarchy -check -top kernellum_k2_board_top; "
        f"synth_ecp5 -top kernellum_k2_board_top -json {design_json}"
    )
    y = run(["yosys", "-p", script])
    (d / "yosys.log").write_text(y.stdout + "\n" + y.stderr)
    if y.returncode != 0:
        raise RuntimeError(f"Yosys failed for {v['name']}")

    n = run([
        "nextpnr-ecp5",
        "--85k",
        "--package", "CABGA381",
        "--json", str(design_json),
        "--lpf", str(LPF),
        "--textcfg", str(config),
        "--freq", "12",
        "--seed", "1",
    ])
    (d / "nextpnr.log").write_text(n.stdout + "\n" + n.stderr)
    if n.returncode != 0:
        raise RuntimeError(f"nextpnr failed for {v['name']}")

    e = run(["ecppack", "--compress", str(config), str(bitstream)])
    (d / "ecppack.log").write_text(e.stdout + "\n" + e.stderr)
    if e.returncode != 0 or not bitstream.exists():
        raise RuntimeError(f"ecppack failed for {v['name']}")

    return {
        **v,
        "bitstream": str(bitstream.relative_to(ROOT)),
        "sha256": sha256(bitstream),
        "size_bytes": bitstream.stat().st_size,
        "program_sram": f"openFPGALoader -b ecp5_evn -m {bitstream.relative_to(ROOT)}",
    }


def main() -> int:
    missing = [t for t in ("yosys", "nextpnr-ecp5", "ecppack") if not shutil.which(t)]
    if missing:
        print("missing tools: " + ", ".join(missing), file=sys.stderr)
        return 2

    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = {
        "board": "LFE5UM5G-85F-EVN",
        "clock_mhz": 12,
        "uart_baud": 115200,
        "variants": [],
    }
    for v in VARIANTS:
        print(f"[k2] building {v['name']}", flush=True)
        manifest["variants"].append(build_variant(v))

    manifest_path = BUILD / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
