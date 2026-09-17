from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from kernellum.compiler import load_demo_data, train_demo_model
from kernellum.onnx_frontend import compile_onnx_dense


def export_demo_onnx(path: Path):
    X_train, X_test, y_train, _ = load_demo_data()
    clf = train_demo_model(X_train, y_train)

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
        "kernellum_digits_dense3",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 64])],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, 10])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)
    return X_train, X_test


def main() -> None:
    out = Path("artifacts/onnx_digits")
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "digits_dense3.onnx"
    X_train, X_test = export_demo_onnx(model_path)
    result = compile_onnx_dense(
        model_path,
        calibration=X_train,
        golden_inputs=X_test[:16],
        out_dir=out,
        target="ecp5-85f",
    )
    print(f"KERNELLUM_ONNX_BUILD dims={result.ir.dims}")
    print(f"architecture={result.lanes} lanes cycles={result.cycles}")
    print(f"modeled_latency_us={result.modeled_latency_us:.3f}")


if __name__ == "__main__":
    main()
