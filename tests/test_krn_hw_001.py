from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


def _load_hw_tool():
    path = Path(__file__).resolve().parents[1] / "scripts" / "krn_hw_001.py"
    spec = importlib.util.spec_from_file_location("krn_hw_001", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _populate_valid_session(module, session: Path, latency_trials: int = 100) -> None:
    module.init_session(session, None)

    metadata_path = session / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata.update(
        {
            "board_revision": "test-board",
            "bitstream_sha256": "a" * 64,
            "programming_success": True,
            "observed_class": metadata["expected_class"],
            "functional_pass": True,
            "latency_instrument": "test logic analyzer",
            "power_instrument": "test power meter",
            "power_method": "synthetic regression fixture",
            "measurement_point": "board input",
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    with (session / "latency_us.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trial", "latency_us"])
        for i in range(latency_trials):
            writer.writerow([i, 61.0 + (i % 5) * 0.1])

    with (session / "idle_power.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "timestamp_s", "voltage_v", "current_a", "power_w"])
        for i in range(20):
            writer.writerow([i, i * 0.1, 5.0, 0.2, ""])

    with (session / "active_power.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "timestamp_s", "voltage_v", "current_a", "power_w"])
        for i in range(20):
            writer.writerow([i, i * 0.1, 5.0, 0.25, ""])


def test_krn_hw_001_complete_session(tmp_path: Path) -> None:
    module = _load_hw_tool()
    session = tmp_path / "complete"
    _populate_valid_session(module, session, latency_trials=100)

    module.analyze_session(session)
    result = json.loads((session / "result.json").read_text())

    assert result["evidence_complete"] is True
    assert result["completion_requirements"]["latency_trials_at_least_100"] is True
    assert result["functional"]["pass"] is True
    assert result["latency_us"]["n"] == 100
    assert abs(result["idle_power_w"]["mean"] - 1.0) < 1e-12
    assert abs(result["active_power_w"]["mean"] - 1.25) < 1e-12
    assert abs(result["dynamic_power_w"] - 0.25) < 1e-12

    mean_latency = result["latency_us"]["mean"]
    assert abs(result["energy_per_inference_uj"]["total_board_estimate"] - 1.25 * mean_latency) < 1e-9
    assert abs(result["energy_per_inference_uj"]["dynamic_increment_estimate"] - 0.25 * mean_latency) < 1e-9


def test_krn_hw_001_rejects_short_latency_campaign(tmp_path: Path) -> None:
    module = _load_hw_tool()
    session = tmp_path / "short"
    _populate_valid_session(module, session, latency_trials=99)

    module.analyze_session(session)
    result = json.loads((session / "result.json").read_text())

    assert result["evidence_complete"] is False
    assert result["completion_requirements"]["latency_trials_at_least_100"] is False
    assert result["functional"]["pass"] is True
