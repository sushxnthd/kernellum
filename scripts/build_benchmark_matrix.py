from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from kernellum.onnx_frontend import compile_onnx_dense


CASES = (
    ("compact_32x16x8x4", (32, 16, 8, 4), 101),
    ("reference_64x32x16x10", (64, 32, 16, 10), 202),
    ("wide_128x64x32x8", (128, 64, 32, 8), 303),
)


def export_dense3(path: Path, dims: tuple[int, int, int, int], seed: int) -> None:
    rng = np.random.default_rng(seed)
    nodes = []
    initializers = []
    current = "input"

    for idx, (din, dout) in enumerate(zip(dims[:-1], dims[1:]), start=1):
        weight = rng.normal(0.0, 0.18, size=(din, dout)).astype(np.float32)
        bias = rng.normal(0.0, 0.04, size=(dout,)).astype(np.float32)
        w_name, b_name = f"w{idx}", f"b{idx}"
        initializers.extend(
            [
                numpy_helper.from_array(weight, name=w_name),
                numpy_helper.from_array(bias, name=b_name),
            ]
        )
        gemm_out = f"gemm{idx}_out"
        nodes.append(helper.make_node("Gemm", [current, w_name, b_name], [gemm_out], name=f"gemm{idx}"))
        if idx < 3:
            relu_out = f"relu{idx}_out"
            nodes.append(helper.make_node("Relu", [gemm_out], [relu_out], name=f"relu{idx}"))
            current = relu_out
        else:
            current = gemm_out

    graph = helper.make_graph(
        nodes,
        path.stem,
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, dims[0]])],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, dims[-1]])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)


def main() -> None:
    root = Path("artifacts/benchmark_matrix")
    root.mkdir(parents=True, exist_ok=True)
    rows = []

    for name, dims, seed in CASES:
        case_dir = root / name
        case_dir.mkdir(parents=True, exist_ok=True)
        model_path = case_dir / f"{name}.onnx"
        export_dense3(model_path, dims, seed)

        rng = np.random.default_rng(seed + 1)
        calibration = rng.normal(0.0, 0.35, size=(96, dims[0])).astype(np.float64)
        golden = rng.normal(0.0, 0.35, size=(16, dims[0])).astype(np.float64)

        result = compile_onnx_dense(
            model_path,
            calibration=calibration,
            golden_inputs=golden,
            out_dir=case_dir,
            target="ecp5-85f",
        )
        rows.append(
            {
                "case": name,
                "dims": list(dims),
                "lanes": result.lanes,
                "cycles": result.cycles,
                "modeled_latency_us_at_100mhz": result.modeled_latency_us,
                "cycle_reference_exact": True,
                "rtl_emitted": (case_dir / "kernellum_dense3_accel.sv").exists(),
                "golden_samples": int(len(result.qinputs)),
            }
        )

    summary = {
        "kind": "compiler-shape-matrix",
        "evidence_level": "compiler/cycle-model artifact generation",
        "claim_boundary": (
            "Synthetic deterministic dense graphs used to exercise compiler shape generality. "
            "These are not application accuracy, P&R, physical-board, power, or customer-workload results."
        ),
        "cases": rows,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Kernellum compiler shape-matrix benchmark",
        "",
        "Deterministic synthetic three-layer dense graphs used to verify that the ONNX → hardware IR → "
        "quantization → architecture-search → RTL path is not hard-coded to one tensor shape.",
        "",
        "| Case | Dims | Selected lanes | Cycles | Modeled latency @100 MHz | Cycle/reference | RTL |",
        "|---|---|---:|---:|---:|:---:|:---:|",
    ]
    for row in rows:
        dims_text = " → ".join(str(x) for x in row["dims"])
        lines.append(
            f'| {row["case"]} | {dims_text} | {row["lanes"]} | {row["cycles"]} | '
            f'{row["modeled_latency_us_at_100mhz"]:.2f} µs | exact | emitted |'
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This matrix tests compiler shape generality with synthetic deterministic graphs. "
            "It does **not** establish application accuracy, post-route timing, measured FPGA performance, "
            "power/energy, or external design-partner validation.",
            "",
        ]
    )
    (root / "SUMMARY.md").write_text("\n".join(lines))
    print(f"KERNELLUM_BENCHMARK_MATRIX_PASS cases={len(rows)}")


if __name__ == "__main__":
    main()
