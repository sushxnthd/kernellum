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
    assert result.cycles == 680
    for rel in [
        "kernellum_dense_accel.sv",
        "tb_kernellum_dense_accel.sv",
        "manifest.json",
        "weights/w1.hex",
        "weights/w2.hex",
        "weights/w3.hex",
        "weights/golden_inputs.hex",
        "weights/golden_outputs.hex",
    ]:
        assert (out / rel).is_file(), rel


def _export_variable_depth_onnx(path: Path, hidden: tuple[int, ...], *, flatten_input: bool = False):
    rng = np.random.default_rng(7)
    nodes = []
    initializers = []
    current = "input"
    input_shape = [None, 8, 8] if flatten_input else [None, 64]
    if flatten_input:
        flat_out = "flat"
        nodes.append(helper.make_node("Flatten", [current], [flat_out], axis=1, name="flatten"))
        current = flat_out

    dims = (64,) + hidden + (10,)
    for i, (din, dout) in enumerate(zip(dims[:-1], dims[1:]), start=1):
        w_name, b_name = f"vw{i}", f"vb{i}"
        weight = (rng.standard_normal((din, dout)) * 0.08).astype(np.float32)
        bias = (rng.standard_normal(dout) * 0.02).astype(np.float32)
        initializers += [
            numpy_helper.from_array(weight, name=w_name),
            numpy_helper.from_array(bias, name=b_name),
        ]
        gemm_out = f"vgemm{i}_out"
        nodes.append(helper.make_node("Gemm", [current, w_name, b_name], [gemm_out], name=f"vgemm{i}"))
        if i < len(dims) - 1:
            relu_out = f"vrelu{i}_out"
            nodes.append(helper.make_node("Relu", [gemm_out], [relu_out], name=f"vrelu{i}"))
            current = relu_out
        else:
            current = gemm_out

    graph = helper.make_graph(
        nodes,
        "kernellum_variable_depth",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, input_shape)],
        [helper.make_tensor_value_info(current, TensorProto.FLOAT, [None, 10])],
        initializer=initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    onnx.save(model, path)


@pytest.mark.parametrize("hidden", [(16,), (32, 24, 16)])
def test_variable_depth_backend(tmp_path: Path, hidden: tuple[int, ...]):
    model_path = tmp_path / "variable.onnx"
    _export_variable_depth_onnx(model_path, hidden)
    rng = np.random.default_rng(9)
    calibration = rng.random((64, 64), dtype=np.float64)
    golden = rng.random((8, 64), dtype=np.float64)
    out = tmp_path / "compiled_variable"
    result = compile_onnx_dense(model_path, calibration, golden, out)
    assert result.ir.dims == (64,) + hidden + (10,)
    assert (out / "kernellum_dense_accel.sv").is_file()
    manifest = __import__("json").loads((out / "manifest.json").read_text())
    assert len(manifest["quantization"]) == len(hidden) + 1
    assert manifest["memory"]["parameter_bytes"] > 0


def test_flatten_input_shape_is_lowered(tmp_path: Path):
    model_path = tmp_path / "flatten.onnx"
    _export_variable_depth_onnx(model_path, (16,), flatten_input=True)
    ir = lower_onnx_dense(model_path)
    assert ir.input_dim == 64
    assert ir.dims == (64, 16, 10)
