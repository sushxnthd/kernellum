from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier

from kernellum.compiler import (
    cycle_forward,
    int_forward,
    load_demo_data,
    quantize_inputs,
    quantize_model,
    search_architecture,
)
from kernellum.onnx_frontend import compile_onnx_dense, model_memory_report


CONFIGS = [
    ("tiny", (16,)),
    ("shallow", (32,)),
    ("baseline", (32, 16)),
    ("deep", (32, 24, 16)),
    ("wide", (64, 32)),
]


def export_mlp_onnx(clf: MLPClassifier, path: Path) -> None:
    nodes = []
    initializers = []
    current = "input"
    for i, (weight, bias) in enumerate(zip(clf.coefs_, clf.intercepts_), start=1):
        w_name, b_name = f"w{i}", f"b{i}"
        initializers.extend(
            [
                numpy_helper.from_array(weight.astype(np.float32), name=w_name),
                numpy_helper.from_array(bias.astype(np.float32), name=b_name),
            ]
        )
        gemm_out = f"gemm{i}_out"
        nodes.append(helper.make_node("Gemm", [current, w_name, b_name], [gemm_out], name=f"gemm{i}"))
        if i < len(clf.coefs_):
            relu_out = f"relu{i}_out"
            nodes.append(helper.make_node("Relu", [gemm_out], [relu_out], name=f"relu{i}"))
            current = relu_out
        else:
            current = gemm_out

    graph = helper.make_graph(
        nodes,
        "kernellum_benchmark",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 64])],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, 10])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)


def run() -> list[dict]:
    X_train, X_test, y_train, y_test = load_demo_data()
    root = Path("artifacts/benchmarks")
    root.mkdir(parents=True, exist_ok=True)
    rows = []

    for index, (name, hidden) in enumerate(CONFIGS):
        clf = MLPClassifier(
            hidden_layer_sizes=hidden,
            activation="relu",
            solver="adam",
            alpha=1e-4,
            learning_rate_init=1e-3,
            max_iter=1000,
            random_state=11 + index,
            early_stopping=False,
        )
        clf.fit(X_train, y_train)

        qmodel = quantize_model(clf, X_train)
        qinputs = quantize_inputs(X_test, qmodel.activation_scales[0])
        qoutputs = int_forward(qmodel, qinputs)
        float_pred = clf.predict(X_test)
        int_pred = np.argmax(qoutputs.astype(np.int16), axis=1)

        selected, candidates = search_architecture(qmodel.dims)
        cycle = cycle_forward(qmodel, qinputs, int(selected["lanes"]))
        exact = bool(np.array_equal(cycle, qoutputs))

        out = root / name
        out.mkdir(parents=True, exist_ok=True)
        model_path = out / f"{name}.onnx"
        export_mlp_onnx(clf, model_path)
        compiled = compile_onnx_dense(
            model_path,
            calibration=X_train,
            golden_inputs=X_test[:16],
            out_dir=out,
            target="ulx3s-85f",
        )

        memory = model_memory_report(qmodel)
        row = {
            "name": name,
            "dims": list(qmodel.dims),
            "dense_layers": len(qmodel.qweights),
            "float_accuracy": float(accuracy_score(y_test, float_pred)),
            "int8_accuracy": float(accuracy_score(y_test, int_pred)),
            "prediction_agreement": float(np.mean(float_pred == int_pred)),
            "cycle_exact_samples": int(len(X_test)) if exact else 0,
            "cycle_exact": exact,
            "selected_lanes": int(selected["lanes"]),
            "cycles": int(selected["cycles"]),
            "modeled_latency_us_100mhz": float(selected["latency_us"]),
            "weight_bytes": int(memory["weight_bytes"]),
            "bias_bytes": int(memory["bias_bytes"]),
            "parameter_bytes": int(memory["parameter_bytes"]),
            "peak_activation_bytes_proxy": int(memory["peak_activation_bytes_int8_double_buffer_proxy"]),
            "onnx_compiled_dims": list(compiled.ir.dims),
            "architecture_candidates": list(candidates),
        }
        rows.append(row)
        (out / "benchmark.json").write_text(json.dumps(row, indent=2) + "\n")
        print(
            f"{name}: dims={qmodel.dims} float={row['float_accuracy']:.4f} "
            f"int8={row['int8_accuracy']:.4f} lanes={row['selected_lanes']} cycles={row['cycles']}"
        )

    (root / "results.json").write_text(json.dumps({"schema": "kernellum.benchmarks.v1", "rows": rows}, indent=2) + "\n")
    fields = [
        "name", "dense_layers", "float_accuracy", "int8_accuracy", "prediction_agreement",
        "cycle_exact_samples", "selected_lanes", "cycles", "modeled_latency_us_100mhz",
        "weight_bytes", "bias_bytes", "parameter_bytes", "peak_activation_bytes_proxy",
    ]
    with (root / "results.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})

    md = [
        "# Kernellum v0.2 benchmark matrix",
        "",
        "| Model | Dims | Float acc. | INT8 acc. | Exact cycle | Lanes | Cycles | Model bytes |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        dims = "→".join(str(x) for x in row["dims"])
        md.append(
            f"| {row['name']} | {dims} | {row['float_accuracy']:.4f} | {row['int8_accuracy']:.4f} | "
            f"{row['cycle_exact_samples']} | {row['selected_lanes']} | {row['cycles']} | {row['parameter_bytes']} |"
        )
    md += [
        "",
        "Latency values in the JSON/CSV are cycle-count models at an assumed 100 MHz unless a separate P&R feedback file is supplied.",
    ]
    (root / "README.md").write_text("\n".join(md) + "\n")
    return rows


if __name__ == "__main__":
    run()
