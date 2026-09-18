from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "krn_hw_001.py"
SPEC = importlib.util.spec_from_file_location("krn_hw_001", SCRIPT)
assert SPEC and SPEC.loader
hw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hw)


def _write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def test_complete_measurement_session(tmp_path: Path) -> None:
    hw.init_session(tmp_path, None)

    meta_path = tmp_path / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta.update(
        {
            "board_revision": "test-board",
            "bitstream_sha256": hw.REFERENCE_BITSTREAM_SHA256,
            "reference_bitstream_match": True,
            "ci_workflow_run": hw.REFERENCE_WORKFLOW_RUN,
            "programming_success": True,
            "programming_exit_code": 0,
            "programmed_utc": "2026-09-18T00:00:00+00:00",
            "observed_class": 8,
            "functional_pass": True,
            "functional_check_utc": "2026-09-18T00:01:00+00:00",
            "latency_instrument": "test-scope",
            "power_instrument": "test-meter",
            "power_method": "inline test",
            "measurement_point": "board input",
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    (tmp_path / "programming.log").write_text("openFPGALoader test success\n")

    _write_csv(
        tmp_path / "latency_us.csv",
        ["trial", "latency_us"],
        [[i + 1, 60.0] for i in range(100)],
    )
    _write_csv(
        tmp_path / "idle_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
        [[i + 1, i * 0.1, "", "", 1.0] for i in range(10)],
    )
    _write_csv(
        tmp_path / "active_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
        [[i + 1, i * 0.1, "", "", 1.5] for i in range(10)],
    )

    hw.analyze_session(tmp_path)
    result = json.loads((tmp_path / "result.json").read_text())

    assert result["evidence_complete"] is True
    assert result["functional"]["pass"] is True
    assert result["latency_us"]["n"] == 100
    assert result["latency_us"]["mean"] == 60.0
    assert result["idle_power_w"]["mean"] == 1.0
    assert result["active_power_w"]["mean"] == 1.5
    assert result["dynamic_power_w"] == 0.5
    assert result["energy_per_inference_uj"]["total_board_estimate"] == 90.0
    assert result["energy_per_inference_uj"]["dynamic_increment_estimate"] == 30.0


def test_session_not_complete_without_functional_pass(tmp_path: Path) -> None:
    hw.init_session(tmp_path, None)
    meta_path = tmp_path / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta.update(
        {
            "board_revision": "test-board",
            "bitstream_sha256": hw.REFERENCE_BITSTREAM_SHA256,
            "reference_bitstream_match": True,
            "ci_workflow_run": hw.REFERENCE_WORKFLOW_RUN,
            "programming_success": True,
            "programming_exit_code": 0,
            "programmed_utc": "2026-09-18T00:00:00+00:00",
            "observed_class": 7,
            "functional_pass": True,
            "functional_check_utc": "2026-09-18T00:01:00+00:00",
            "latency_instrument": "test-scope",
            "power_instrument": "test-meter",
            "power_method": "inline test",
            "measurement_point": "board input",
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    (tmp_path / "programming.log").write_text("openFPGALoader test success\n")

    _write_csv(
        tmp_path / "latency_us.csv",
        ["trial", "latency_us"],
        [[i + 1, 60.0] for i in range(100)],
    )
    _write_csv(
        tmp_path / "idle_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
        [[i + 1, i * 0.1, "", "", 1.0] for i in range(10)],
    )
    _write_csv(
        tmp_path / "active_power.csv",
        ["sample", "timestamp_s", "voltage_v", "current_a", "power_w"],
        [[i + 1, i * 0.1, "", "", 1.5] for i in range(10)],
    )

    hw.analyze_session(tmp_path)
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["functional"]["pass"] is False
    assert result["evidence_complete"] is False
