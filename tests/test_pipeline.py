from pathlib import Path
import numpy as np

from kernellum.compiler import (
    build_demo,
    cycle_forward,
    generate_demo_artifacts,
    int_forward,
    search_architecture,
)


def test_demo_quality_and_cycle_model():
    build = build_demo()
    assert build.float_accuracy >= 0.95
    assert build.int_accuracy >= 0.95
    assert build.prediction_agreement >= 0.99
    assert build.lanes == 4
    assert build.cycles == 680
    cycled = cycle_forward(build.model, build.qinputs, build.lanes)
    assert np.array_equal(cycled, int_forward(build.model, build.qinputs))


def test_architecture_search_selects_smallest_feasible():
    selected, candidates = search_architecture((64, 32, 16, 10))
    assert selected["lanes"] == 4
    assert [c["lanes"] for c in candidates] == [1, 2, 4, 8, 16]


def test_artifact_generation(tmp_path: Path):
    out = tmp_path / "digits"
    generate_demo_artifacts(out)
    required = [
        "kernellum_mlp_accel.sv",
        "kernellum_demo_top.sv",
        "tb_kernellum_mlp_accel.sv",
        "manifest.json",
        "REPORT.md",
        "weights/w1.hex",
        "weights/w2.hex",
        "weights/w3.hex",
        "weights/b1.hex",
        "weights/b2.hex",
        "weights/b3.hex",
        "weights/golden_inputs.hex",
        "weights/golden_outputs.hex",
        "weights/demo_input.hex",
    ]
    for rel in required:
        assert (out / rel).is_file(), rel
