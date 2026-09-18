from pathlib import Path
import numpy as np
import pytest

onnx = pytest.importorskip("onnx")
from onnx import TensorProto, helper, numpy_helper

from kernellum.compiler import load_demo_data, train_demo_model
from kernellum.onnx_frontend import compile_onnx_dense, lower_onnx_dense


def _export_demo_onnx(path: Path):
    X_train, X_test, y_train, _ = load_demo_data()
    clf = train_demo_model(X_train, y_train)
    initializers = []
    nodes = []
    current = "input"
    for i, (w, b) in enumerate(zip(clf.coefs_, clf.intercepts_), start=1):
        w_name, b_name = f"w{i}", f"b{i}"
        initializers += [
            numpy_helper.from_array(w.astype(np.float32), name=w_name),
            numpy_helper.from_array(b.astype(np.float32), name=b_name),
        ]
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
        "kernellum_demo_mlp",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 64])],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, 10])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)
    return X_train, X_test


def test_lower_real_onnx_graph(tmp_path: Path):
    model_path = tmp_path / "digits.onnx"
    _, _ = _export_demo_onnx(model_path)
    ir = lower_onnx_dense(model_path)
    assert ir.dims == (64, 32, 16, 10)
    assert [layer.relu for layer in ir.layers] == [True, True, False]


def test_onnx_to_rtl_alpha(tmp_path: Path):
    model_path = tmp_path / "digits.onnx"
    X_train, X_test = _export_demo_onnx(model_path)
    out = tmp_path / "compiled"
    result = compile_onnx_dense(model_path, X_train, X_test[:16], out)
    assert result.ir.dims == (64, 32, 16, 10)
    assert result.lanes == 4
    assert result.cycles == 796
    for rel in [
        "kernellum_dense3_accel.sv",
        "tb_kernellum_dense3_accel.sv",
        "manifest.json",
        "weights/w1.hex",
        "weights/w2.hex",
        "weights/w3.hex",
        "weights/golden_inputs.hex",
        "weights/golden_outputs.hex",
    ]:
        assert (out / rel).is_file(), rel
