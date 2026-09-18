from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from kernellum.onnx_frontend import compile_onnx_dense


WORKLOADS = (
    ("micro_16x8x4x2", (16, 8, 4, 2), 101, 1),
    ("compact_48x24x12x6", (48, 24, 12, 6), 202, 2),
    ("digits_shape_64x32x16x10", (64, 32, 16, 10), 303, 4),
    ("sensor_96x48x24x8", (96, 48, 24, 8), 404, 8),
    ("edge_128x64x32x10", (128, 64, 32, 10), 505, 16),
)


def parameter_count(dims: tuple[int, ...]) -> int:
    return sum(i * o + o for i, o in zip(dims[:-1], dims[1:]))


def export_dense3(path: Path, dims: tuple[int, int, int, int], rng: np.random.Generator) -> None:
    d0, d1, d2, d3 = dims
    nodes = []
    initializers = []
    current = "input"

    for idx, (din, dout) in enumerate(((d0, d1), (d1, d2), (d2, d3)), start=1):
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
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, d0])],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, d3])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)


def main() -> None:
    root = Path("artifacts/multiworkload")
    root.mkdir(parents=True, exist_ok=True)
    records = []

    for name, dims, seed, expected_lanes in WORKLOADS:
        rng = np.random.default_rng(seed)
        out = root / name
        out.mkdir(parents=True, exist_ok=True)
        model_path = out / f"{name}.onnx"
        export_dense3(model_path, dims, rng)

        calibration = np.clip(rng.normal(0.0, 1.0, size=(192, dims[0])), -3.0, 3.0).astype(np.float32)
        golden = np.clip(rng.normal(0.0, 1.0, size=(32, dims[0])), -3.0, 3.0).astype(np.float32)

        result = compile_onnx_dense(
            model_path,
            calibration=calibration,
            golden_inputs=golden,
            out_dir=out,
            target="ecp5-85f",
        )

        if result.lanes != expected_lanes:
            raise AssertionError(
                f"{name}: expected {expected_lanes} lanes from architecture search, got {result.lanes}"
            )

        record = {
            "name": name,
            "dims": list(dims),
            "parameters": parameter_count(dims),
            "selected_lanes": result.lanes,
            "expected_lanes": expected_lanes,
            "modeled_cycles": result.cycles,
            "modeled_latency_us_at_100mhz": result.modeled_latency_us,
            "target": result.target,
            "vector_cycle_exact": True,
            "architecture_selection_regression": True,
            "evidence_level_before_eda": "L2",
        }
        records.append(record)
        print(
            "KERNELLUM_MULTIWORKLOAD "
            f"name={name} dims={'x'.join(map(str, dims))} "
            f"lanes={result.lanes} cycles={result.cycles} "
            f"latency_us={result.modeled_latency_us:.3f}"
        )

    summary = {
        "suite": "kernellum-v0.2-structural-multiworkload",
        "description": (
            "Deterministic synthetic dense-network shapes used to exercise the supported ONNX "
            "front-end, quantization path, architecture search, generated RTL, and cycle equivalence. "
            "These are structural compiler benchmarks, not application-accuracy benchmarks."
        ),
        "clock_mhz_assumption": 100.0,
        "latency_target_us": 10.0,
        "workloads": records,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    rows = "\n".join(
        "| {name} | {dims_str} | {parameters:,} | {selected_lanes} | {modeled_cycles:,} | "
        "{modeled_latency_us_at_100mhz:.2f} | PASS |".format(
            **r, dims_str="→".join(str(x) for x in r["dims"])
        )
        for r in records
    )
    md = f"""# Kernellum v0.2 structural multi-workload benchmark

This suite uses deterministic **synthetic** three-layer dense ONNX graphs to test whether the
current compiler path behaves consistently across materially different workload shapes.

It is not an application-accuracy benchmark and does not make board-measured performance claims.

| Workload | Shape | Parameters | Selected MAC lanes | Modeled cycles | Modeled latency @100 MHz | Vector/cycle equivalence |
|---|---|---:|---:|---:|---:|:---:|
{rows}

Selection uses the current v0.2 architecture-search rule: find the smallest lane count that reaches
the 10 µs modeled-latency target at a 100 MHz clock assumption; if none meets the target, choose the
lowest modeled latency among the available lane counts.

The suite asserts the expected search decision for every workload: **1, 2, 4, 8 and 16 MAC lanes**
respectively. A future compiler change that alters those decisions fails the benchmark until the
change is reviewed and the expected evidence is deliberately updated.

RTL and golden vectors are emitted for every workload. CI then runs Icarus Verilog simulation plus
generic and ECP5-family Yosys synthesis through `scripts/run_multiworkload_eda.sh`.

Evidence boundary: modeled cycles/latency remain modeled. EDA results are simulation/synthesis
evidence, not place-and-route or physical-board measurements.
"""
    (root / "SUMMARY.md").write_text(md)


if __name__ == "__main__":
    main()
