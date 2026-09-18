from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path


KIT_VERSION = "0.1"
EVIDENCE_ID = "KRN-HW-001"
TARGET = "ULX3S-85F / LFE5U-85F-6BG381C / CABGA381"
CLOCK_MHZ = 25.0
EXPECTED_CLASS = 8
REFERENCE_BITSTREAM_SHA256 = (
    "19c403d3a169b320c8ae9584cb388255fdef784ad7d4651becaab690634be415"
)
REFERENCE_WORKFLOW_RUN = "35321132327"
REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILES = {
    REPO_ROOT / "HARDWARE_RUNBOOK.md": Path("README.md"),
    REPO_ROOT / "research/KRN-HW-001_PROTOCOL.md": Path("KRN-HW-001_PROTOCOL.md"),
    REPO_ROOT / "scripts/krn_hw_001.py": Path("tools/krn_hw_001.py"),
    REPO_ROOT / "scripts/package_krn_hw_001_kit.py": Path(
        "tools/package_krn_hw_001_kit.py"
    ),
    REPO_ROOT / "scripts/program_krn_hw_001_ulx3s.sh": Path(
        "tools/program_krn_hw_001_ulx3s.sh"
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, headers: list[str]) -> None:
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerow(headers)


def _write_session_template(
    session: Path, workflow_run: str, reference_bitstream_sha256: str
) -> None:
    session.mkdir(parents=True)
    metadata = {
        "evidence_id": EVIDENCE_ID,
        "created_utc": "",
        "target": TARGET,
        "clock_mhz": CLOCK_MHZ,
        "board_revision": "",
        "fpga_density": "85F",
        "bitstream_path": "../kernellum_demo_top.bit",
        "bitstream_sha256": reference_bitstream_sha256,
        "reference_bitstream_sha256": reference_bitstream_sha256,
        "reference_bitstream_match": True,
        "ci_workflow_run": workflow_run,
        "programmer": "openFPGALoader",
        "programming_command": "openFPGALoader --board=ulx3s ../kernellum_demo_top.bit",
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
    (session / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    _write_csv(session / "latency_us.csv", ["trial", "latency_us"])
    power_headers = ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"]
    _write_csv(session / "idle_power.csv", power_headers)
    _write_csv(session / "active_power.csv", power_headers)


def _file_record(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def create_deterministic_zip(kit_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in kit_dir.rglob("*") if item.is_file()):
            relative = Path(kit_dir.name) / path.relative_to(kit_dir)
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix == ".sh" else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def build_kit(
    bitstream: Path,
    out: Path,
    source_commit: str,
    workflow_run: str = REFERENCE_WORKFLOW_RUN,
    expected_sha256: str = REFERENCE_BITSTREAM_SHA256,
    zip_path: Path | None = None,
) -> dict[str, object]:
    bitstream = bitstream.resolve()
    if not bitstream.is_file():
        raise ValueError(f"bitstream not found: {bitstream}")
    actual_sha256 = sha256_file(bitstream)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "bitstream SHA-256 does not match the frozen reference: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory is not empty: {out}")

    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bitstream, out / "kernellum_demo_top.bit")
    for source, destination in SOURCE_FILES.items():
        if not source.is_file():
            raise ValueError(f"required source file not found: {source}")
        target = out / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (out / "tools/program_krn_hw_001_ulx3s.sh").chmod(0o755)
    _write_session_template(out / "session", workflow_run, expected_sha256)

    payload_files = sorted(
        item
        for item in out.rglob("*")
        if item.is_file() and item.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kit_version": KIT_VERSION,
        "evidence_id": EVIDENCE_ID,
        "target": TARGET,
        "clock_mhz": CLOCK_MHZ,
        "expected_class": EXPECTED_CLASS,
        "source_commit": source_commit,
        "reference_workflow_run": workflow_run,
        "reference_bitstream_sha256": expected_sha256,
        "files": [_file_record(path, out) for path in payload_files],
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    checksum_files = payload_files + [manifest_path]
    checksums = "".join(
        f"{sha256_file(path)}  {path.relative_to(out).as_posix()}\n"
        for path in sorted(checksum_files)
    )
    (out / "SHA256SUMS").write_text(checksums)

    verify_kit(out, expected_sha256=expected_sha256)
    if zip_path is not None:
        create_deterministic_zip(out, zip_path)
    return manifest


def verify_kit(
    kit_dir: Path, expected_sha256: str = REFERENCE_BITSTREAM_SHA256
) -> dict[str, object]:
    manifest_path = kit_dir / "manifest.json"
    checksums_path = kit_dir / "SHA256SUMS"
    if not manifest_path.is_file() or not checksums_path.is_file():
        raise ValueError("kit must contain manifest.json and SHA256SUMS")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("evidence_id") != EVIDENCE_ID:
        raise ValueError("manifest evidence_id is not KRN-HW-001")
    if manifest.get("reference_bitstream_sha256") != expected_sha256:
        raise ValueError("manifest reference bitstream SHA-256 is incorrect")

    listed: set[str] = set()
    for record in manifest.get("files", []):
        relative = str(record["path"])
        listed.add(relative)
        path = kit_dir / relative
        if not path.is_file():
            raise ValueError(f"manifest file is missing: {relative}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"manifest SHA-256 mismatch: {relative}")
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"manifest byte count mismatch: {relative}")

    actual_payload = {
        path.relative_to(kit_dir).as_posix()
        for path in kit_dir.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    }
    if listed != actual_payload:
        raise ValueError("manifest file set does not match kit contents")

    bitstream = kit_dir / "kernellum_demo_top.bit"
    if sha256_file(bitstream) != expected_sha256:
        raise ValueError("packaged bitstream SHA-256 is incorrect")

    expected_sums = {
        path.relative_to(kit_dir).as_posix(): sha256_file(path)
        for path in sorted([*(kit_dir / relative for relative in listed), manifest_path])
    }
    recorded_sums: dict[str, str] = {}
    for line in checksums_path.read_text().splitlines():
        digest, relative = line.split("  ", 1)
        recorded_sums[relative] = digest
    if recorded_sums != expected_sums:
        raise ValueError("SHA256SUMS does not match the kit contents")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or verify the KRN-HW-001 handoff kit")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build an integrity-checked hardware kit")
    build.add_argument("--bitstream", required=True, type=Path)
    build.add_argument("--out", required=True, type=Path)
    build.add_argument("--zip", dest="zip_path", type=Path)
    build.add_argument("--source-commit", required=True)
    build.add_argument("--workflow-run", default=REFERENCE_WORKFLOW_RUN)

    verify = sub.add_parser("verify", help="verify every packaged file and checksum")
    verify.add_argument("kit", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "build":
            manifest = build_kit(
                args.bitstream,
                args.out,
                args.source_commit,
                args.workflow_run,
                zip_path=args.zip_path,
            )
            print(
                "KRN_HW_001_KIT_BUILT "
                f"files={len(manifest['files'])} out={args.out}"
            )
        else:
            manifest = verify_kit(args.kit)
            print(
                "KRN_HW_001_KIT_VERIFIED "
                f"files={len(manifest['files'])} kit={args.kit}"
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f"KRN-HW-001 kit error: {exc}") from exc


if __name__ == "__main__":
    main()
