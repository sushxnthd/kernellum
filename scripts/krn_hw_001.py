from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

TARGET = "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381"
CLOCK_MHZ = 25.0
EXPECTED_CLASS = 8


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv_template(path: Path, headers: list[str]) -> None:
    if path.exists():
        return
    with path.open("w", newline="") as f:
        csv.writer(f).writerow(headers)


def init_session(out: Path, bitstream: Path | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    digest = ""
    bitstream_path = ""
    if bitstream is not None:
        bitstream = bitstream.expanduser().resolve()
        if not bitstream.exists():
            raise SystemExit(f"bitstream not found: {bitstream}")
        digest = sha256_file(bitstream)
        bitstream_path = str(bitstream)

    metadata = {
        "evidence_id": "KRN-HW-001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "target": TARGET,
        "clock_mhz": CLOCK_MHZ,
        "board_revision": "",
        "fpga_density": "85F",
        "bitstream_path": bitstream_path,
        "bitstream_sha256": digest,
        "ci_workflow_run": "",
        "programmer": "openFPGALoader",
        "programming_command": (
            f"openFPGALoader --board=ulx3s {bitstream_path}"
            if bitstream_path
            else "openFPGALoader --board=ulx3s <bitstream.bit>"
        ),
        "programming_success": False,
        "expected_class": EXPECTED_CLASS,
        "observed_class": None,
        "functional_pass": False,
        "latency_method": "start_btn active edge to done_led active edge",
        "latency_instrument": "",
        "power_method": "",
        "power_instrument": "",
        "measurement_point": "",
        "warmup_inferences": 10,
        "notes": "",
    }
    meta_path = out / "metadata.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

    write_csv_template(out / "latency_us.csv", ["trial", "latency_us"])
    write_csv_template(
        out / "idle_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
    )
    write_csv_template(
        out / "active_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
    )

    print(f"KRN-HW-001 session initialized: {out}")
    if digest:
        print(f"bitstream_sha256={digest}")


def read_float_rows(path: Path, field: str) -> list[float]:
    values: list[float] = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            raw = (row.get(field) or "").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError as exc:
                raise SystemExit(f"invalid {field} in {path}: {raw!r}") from exc
            if not math.isfinite(value):
                raise SystemExit(f"non-finite {field} in {path}: {raw!r}")
            values.append(value)
    return values


def read_power(path: Path) -> list[float]:
    powers: list[float] = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            direct = (row.get("power_w") or "").strip()
            if direct:
                value = float(direct)
            else:
                v = (row.get("voltage_v") or "").strip()
                i = (row.get("current_a") or "").strip()
                if not v or not i:
                    continue
                value = float(v) * float(i)
            if not math.isfinite(value):
                raise SystemExit(f"non-finite power sample in {path}")
            if value < 0:
                raise SystemExit(f"negative power sample in {path}: {value}")
            powers.append(value)
    return powers


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def stats(values: list[float]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "p95": percentile(values, 0.95),
    }


def analyze_session(session: Path) -> None:
    meta_path = session / "metadata.json"
    if not meta_path.exists():
        raise SystemExit(f"missing metadata.json in {session}")
    metadata = json.loads(meta_path.read_text())

    latency = read_float_rows(session / "latency_us.csv", "latency_us")
    idle_power = read_power(session / "idle_power.csv")
    active_power = read_power(session / "active_power.csv")

    if not latency:
        raise SystemExit("no latency samples")
    if not idle_power:
        raise SystemExit("no idle power samples")
    if not active_power:
        raise SystemExit("no active power samples")

    latency_stats = stats(latency)
    idle_stats = stats(idle_power)
    active_stats = stats(active_power)

    dynamic_power_w = float(active_stats["mean"]) - float(idle_stats["mean"])
    mean_latency_us = float(latency_stats["mean"])
    total_energy_uj = float(active_stats["mean"]) * mean_latency_us
    dynamic_energy_uj = dynamic_power_w * mean_latency_us

    required_metadata = {
        "board_revision": metadata.get("board_revision"),
        "bitstream_sha256": metadata.get("bitstream_sha256"),
        "latency_instrument": metadata.get("latency_instrument"),
        "power_instrument": metadata.get("power_instrument"),
        "power_method": metadata.get("power_method"),
        "measurement_point": metadata.get("measurement_point"),
    }
    bit_hash = required_metadata["bitstream_sha256"]
    hash_ok = isinstance(bit_hash, str) and len(bit_hash) == 64
    observed = metadata.get("observed_class")
    functional_pass = bool(metadata.get("functional_pass")) and observed == metadata.get(
        "expected_class"
    )
    metadata_complete = all(
        value
        for key, value in required_metadata.items()
        if key != "bitstream_sha256"
    )
    evidence_complete = bool(
        len(latency) >= 100
        and functional_pass
        and metadata.get("programming_success")
        and hash_ok
        and metadata_complete
    )

    result = {
        "evidence_id": "KRN-HW-001",
        "target": metadata.get("target", TARGET),
        "clock_mhz": metadata.get("clock_mhz", CLOCK_MHZ),
        "bitstream_sha256": metadata.get("bitstream_sha256", ""),
        "functional": {
            "expected_class": metadata.get("expected_class"),
            "observed_class": observed,
            "pass": functional_pass,
        },
        "latency_us": latency_stats,
        "idle_power_w": idle_stats,
        "active_power_w": active_stats,
        "dynamic_power_w": dynamic_power_w,
        "energy_per_inference_uj": {
            "total_board_estimate": total_energy_uj,
            "dynamic_increment_estimate": dynamic_energy_uj,
        },
        "evidence_complete": evidence_complete,
        "completion_requirements": {
            "latency_trials_at_least_100": len(latency) >= 100,
            "functional_pass": functional_pass,
            "programming_success": bool(metadata.get("programming_success")),
            "bitstream_sha256_recorded": hash_ok,
            "measurement_metadata_complete": metadata_complete,
        },
        "claim_boundary": (
            "physical ULX3S board-level measurement; not ASIC performance, "
            "production power efficiency, or customer validation"
        ),
    }
    (session / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    status = "COMPLETE" if evidence_complete else "INCOMPLETE"
    md = [
        "# KRN-HW-001 — Physical ULX3S-85F Measurement",
        "",
        f"**Evidence status:** {status}",
        "",
        f"**Bitstream SHA-256:** {result['bitstream_sha256'] or 'not recorded'}",
        "",
        "## Functional result",
        "",
        f"- Expected class: **{result['functional']['expected_class']}**",
        f"- Observed class: **{result['functional']['observed_class']}**",
        f"- Functional pass: **{'YES' if result['functional']['pass'] else 'NO'}**",
        "",
        "## Measured latency",
        "",
        f"- Trials: **{latency_stats['n']}**",
        f"- Mean: **{latency_stats['mean']:.3f} µs**",
        f"- Median: **{latency_stats['median']:.3f} µs**",
        f"- p95: **{latency_stats['p95']:.3f} µs**",
        f"- Min / max: **{latency_stats['min']:.3f} / {latency_stats['max']:.3f} µs**",
        f"- Standard deviation: **{latency_stats['stdev']:.3f} µs**",
        "",
        "## Measured board power",
        "",
        f"- Idle mean: **{idle_stats['mean']:.6f} W**",
        f"- Active mean: **{active_stats['mean']:.6f} W**",
        f"- Dynamic increment: **{dynamic_power_w:.6f} W**",
        "",
        "## Energy per inference",
        "",
        f"- Total board estimate: **{total_energy_uj:.3f} µJ/inference**",
        f"- Dynamic increment estimate: **{dynamic_energy_uj:.3f} µJ/inference**",
        "",
        "## Claim boundary",
        "",
        result["claim_boundary"] + ".",
        "",
    ]
    (session / "RESULT.md").write_text("\n".join(md))
    print(f"KRN_HW_001_ANALYSIS status={status}")
    print(f"latency_mean_us={latency_stats['mean']:.6f}")
    print(f"active_power_w={active_stats['mean']:.6f}")
    print(f"energy_total_uj={total_energy_uj:.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="KRN-HW-001 physical measurement session tool")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="initialize a measurement session")
    init_p.add_argument("--out", required=True, type=Path)
    init_p.add_argument("--bitstream", type=Path)

    analyze_p = sub.add_parser("analyze", help="analyze populated measurement CSV files")
    analyze_p.add_argument("session", type=Path)

    hash_p = sub.add_parser("hash", help="print SHA-256 of a bitstream")
    hash_p.add_argument("bitstream", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        init_session(args.out, args.bitstream)
    elif args.command == "analyze":
        analyze_session(args.session)
    elif args.command == "hash":
        print(sha256_file(args.bitstream))


if __name__ == "__main__":
    main()
