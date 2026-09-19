#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from kernellum.k2 import K2Link, run_random_trials


class SerialTransport:
    def __init__(self, port: str, baud: int, timeout: float):
        try:
            import serial
        except ImportError as exc:
            raise SystemExit("pyserial is required: python -m pip install pyserial") from exc
        self.serial = serial.Serial(port, baudrate=baud, timeout=timeout)

    def write(self, data: bytes) -> int:
        return self.serial.write(data)

    def read(self, size: int) -> bytes:
        return self.serial.read(size)


def main() -> int:
    p = argparse.ArgumentParser(description="Kernellum K2 physical FPGA validation")
    p.add_argument("--port", required=True, help="USB-UART port, e.g. COM6 or /dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--timeout", type=float, default=2.0)
    p.add_argument("--trials", type=int, default=100)
    p.add_argument("--seed", type=int, default=20260919)
    p.add_argument("--json-out", default="results/k2_board_trials.json")
    args = p.parse_args()

    link = K2Link(SerialTransport(args.port, args.baud, args.timeout))
    if not link.ping():
        raise SystemExit("K2 board did not return the expected PING response")

    info = link.info()
    print(f"K2 board: rows={info.rows} cols={info.cols} k_tile={info.k_tile} clock={info.clock_mhz} MHz")

    trials = run_random_trials(link, trials=args.trials, seed=args.seed)
    correct = sum(x.correct for x in trials)
    cycle_exact = sum(x.cycles == x.expected_cycles for x in trials)

    report = {
        "info": asdict(info),
        "seed": args.seed,
        "trial_count": len(trials),
        "correct_count": correct,
        "cycle_exact_count": cycle_exact,
        "bit_exact_rate": correct / len(trials),
        "cycle_exact_rate": cycle_exact / len(trials),
        "trials": [asdict(x) for x in trials],
    }
    report["physical_gate_partial_pass"] = (
        report["bit_exact_rate"] == 1.0 and report["cycle_exact_rate"] == 1.0
    )

    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "trials"}, indent=2))
    return 0 if report["physical_gate_partial_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
