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
REFERENCE_BITSTREAM_SHA256 = (
    "19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415"
)
REFERENCE_WORKFLOW_RUN = "35321132327"
MIN_LATENCY_TRIALS = 100
MIN_POWER_SAMPLES = 10


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
        "reference_bitstream_sha256": REFERENCE_BITSTREAM_SHA256,
        "reference_bitstream_match": digest == REFERENCE_BITSTREAM_SHA256,
        "ci_workflow_run": (
            REFERENCE_WORKFLOW_RUN if digest == REFERENCE_BITSTREAM_SHA256 else ""
        ),
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
        print(f"reference_bitstream_match={digest == REFERENCE_BITSTREAM_SHA256}")


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
            if value <= 0:
                raise SystemExit(f"non-positive {field} in {path}: {raw!r}")
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


def record_functional(session: Path, observed_class: int) -> bool:
    if not 0 <= observed_class <= 15:
        raise SystemExit("observed class must fit the four class LEDs (0..15)")
    meta_path = session / "metadata.json"
    if not meta_path.exists():
        raise SystemExit(f"missing metadata.json in {session}")
    metadata = json.loads(meta_path.read_text())
    expected = metadata.get("expected_class", EXPECTED_CLASS)
    passed = observed_class == expected
    metadata["observed_class"] = observed_class
    metadata["functional_pass"] = passed
    metadata["functional_check_utc"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        "KRN_HW_001_FUNCTIONAL "
        f"expected={expected} observed={observed_class} pass={str(passed).lower()}"
    )
    return passed


def _completion_checks(
    session: Path,
    metadata: dict[str, object],
    latency: list[float],
    idle_power: list[float],
    active_power: list[float],
) -> dict[str, bool]:
    observed = metadata.get("observed_class")
    expected = metadata.get("expected_class")
    functional_pass = bool(metadata.get("functional_pass")) and observed == expected
    measurement_fields = (
        "board_revision",
        "latency_method",
        "latency_instrument",
        "power_method",
        "power_instrument",
        "measurement_point",
    )
    programming_log = session / "programming.log"
    target_ok = metadata.get("target") == TARGET
    try:
        clock_ok = float(metadata.get("clock_mhz", 0)) == CLOCK_MHZ
    except (TypeError, ValueError):
        clock_ok = False
    dynamic_power_nonnegative = bool(
        idle_power
        and active_power
        and statistics.fmean(active_power) >= statistics.fmean(idle_power)
    )
    bitstream_sha256 = metadata.get("bitstream_sha256")
    return {
        f"latency_trials_at_least_{MIN_LATENCY_TRIALS}": len(latency)
        >= MIN_LATENCY_TRIALS,
        f"idle_power_samples_at_least_{MIN_POWER_SAMPLES}": len(idle_power)
        >= MIN_POWER_SAMPLES,
        f"active_power_samples_at_least_{MIN_POWER_SAMPLES}": len(active_power)
        >= MIN_POWER_SAMPLES,
        "functional_pass": functional_pass,
        "programming_success": bool(metadata.get("programming_success")),
        "programming_exit_code_zero": metadata.get("programming_exit_code") == 0,
        "programmed_utc_recorded": bool(metadata.get("programmed_utc")),
        "programming_log_recorded": programming_log.is_file()
        and programming_log.stat().st_size > 0,
        "reference_bitstream_sha256_match": bitstream_sha256
        == REFERENCE_BITSTREAM_SHA256,
        "reference_workflow_run_recorded": str(metadata.get("ci_workflow_run", ""))
        == REFERENCE_WORKFLOW_RUN,
        "target_identity_match": target_ok,
        "clock_25mhz_match": clock_ok,
        "fpga_density_85f_match": str(metadata.get("fpga_density", "")).upper()
        == "85F",
        "measurement_metadata_complete": all(metadata.get(key) for key in measurement_fields),
        "functional_check_utc_recorded": bool(metadata.get("functional_check_utc")),
        "dynamic_power_nonnegative": dynamic_power_nonnegative,
    }


def _read_optional_measurements(session: Path) -> tuple[list[float], list[float], list[float]]:
    latency_path = session / "latency_us.csv"
    idle_path = session / "idle_power.csv"
    active_path = session / "active_power.csv"
    latency = read_float_rows(latency_path, "latency_us") if latency_path.exists() else []
    idle = read_power(idle_path) if idle_path.exists() else []
    active = read_power(active_path) if active_path.exists() else []
    return latency, idle, active


def doctor_session(session: Path) -> dict[str, object]:
    meta_path = session / "metadata.json"
    if not meta_path.exists():
        raise SystemExit(f"missing metadata.json in {session}")
    metadata = json.loads(meta_path.read_text())
    latency, idle_power, active_power = _read_optional_measurements(session)
    checks = _completion_checks(session, metadata, latency, idle_power, active_power)
    report: dict[str, object] = {
        "evidence_id": "KRN-HW-001",
        "ready": all(checks.values()),
        "checks": checks,
        "sample_counts": {
            "latency": len(latency),
            "idle_power": len(idle_power),
            "active_power": len(active_power),
        },
    }
    print(json.dumps(report, indent=2))
    return report


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

    observed = metadata.get("observed_class")
    functional_pass = bool(metadata.get("functional_pass")) and observed == metadata.get(
        "expected_class"
    )
    checks = _completion_checks(session, metadata, latency, idle_power, active_power)
    evidence_complete = all(checks.values())

    result = {
        "evidence_id": "KRN-HW-001",
        "target": metadata.get("target", TARGET),
        "clock_mhz": metadata.get("clock_mhz", CLOCK_MHZ),
        "bitstream_sha256": metadata.get("bitstream_sha256", ""),
        "reference_bitstream_sha256": REFERENCE_BITSTREAM_SHA256,
        "reference_workflow_run": REFERENCE_WORKFLOW_RUN,
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
        "completion_requirements": checks,
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
        f"**Reference bitstream match:** {'YES' if checks['reference_bitstream_sha256_match'] else 'NO'}",
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
        "## Completion gate",
        "",
        *[
            f"- {'PASS' if passed else 'FAIL'} — `{name}`"
            for name, passed in checks.items()
        ],
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

    doctor_p = sub.add_parser("doctor", help="report the evidence-completion checklist")
    doctor_p.add_argument("session", type=Path)

    functional_p = sub.add_parser(
        "record-functional", help="record the observed class and pass/fail result"
    )
    functional_p.add_argument("session", type=Path)
    functional_p.add_argument("observed_class", type=int)

    hash_p = sub.add_parser("hash", help="print SHA-256 of a bitstream")
    hash_p.add_argument("bitstream", type=Path)

    args = parser.parse_args()
    if args.command == "init":
        init_session(args.out, args.bitstream)
    elif args.command == "analyze":
        analyze_session(args.session)
    elif args.command == "doctor":
        doctor_session(args.session)
    elif args.command == "record-functional":
        record_functional(args.session, args.observed_class)
    elif args.command == "hash":
        print(sha256_file(args.bitstream))


if __name__ == "__main__":
    main()
