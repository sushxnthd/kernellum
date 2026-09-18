from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .compiler import QuantizedModel, cycle_forward, int_forward, search_architecture
from .ir import DenseLayerIR, FPGA_TARGETS, HardwareIR


SUPPORTED_SUBSET = "strict sequential Gemm/Relu with shape-only Flatten/Reshape/Identity"


class UnsupportedONNXGraph(ValueError):
    """Raised when the current front-end cannot lower a graph safely."""


@dataclass
class ONNXCompileResult:
    ir: HardwareIR
    model: QuantizedModel
    qinputs: np.ndarray
    qoutputs: np.ndarray
    lanes: int
    cycles: int
    modeled_latency_us: float
    target: str
    architecture_candidates: tuple[dict[str, Any], ...]


def _onnx_modules():
    try:
        import onnx
        from onnx import numpy_helper
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "ONNX support is optional. Install with: pip install -e '.[onnx]'"
        ) from exc
    return onnx, numpy_helper


def _attrs(node) -> dict[str, object]:
    onnx, _ = _onnx_modules()
    out: dict[str, object] = {}
    for attr in node.attribute:
        out[attr.name] = onnx.helper.get_attribute_value(attr)
    return out


def _node_error(node_idx: int, node, reason: str) -> UnsupportedONNXGraph:
    name = node.name or f"node_{node_idx}"
    return UnsupportedONNXGraph(
        f"{name} [{node.op_type}] at index {node_idx}: {reason}. "
        f"Supported subset: {SUPPORTED_SUBSET}."
    )


def _static_input_dim(value_info) -> int:
    dims: list[int | None] = []
    for dim in value_info.type.tensor_type.shape.dim:
        dims.append(int(dim.dim_value) if int(dim.dim_value) > 0 else None)

    if not dims:
        raise UnsupportedONNXGraph("input tensor must have a declared shape")
    feature_dims = dims[1:] if len(dims) >= 2 else dims
    if not feature_dims or any(d is None for d in feature_dims):
        raise UnsupportedONNXGraph(
            "all non-batch input dimensions must be statically known"
        )
    return int(np.prod([int(d) for d in feature_dims], dtype=np.int64))


def _validate_shape_only_reshape(shape: np.ndarray, current_dim: int, node_idx: int, node) -> None:
    target = [int(v) for v in np.asarray(shape).reshape(-1)]
    if not target:
        raise _node_error(node_idx, node, "Reshape target is empty")

    feature = target[1:] if len(target) >= 2 else target
    if any(v == 0 for v in feature):
        raise _node_error(
            node_idx,
            node,
            "Reshape with zero-copy feature dimensions is not yet supported",
        )
    if sum(v == -1 for v in feature) > 1 or any(v < -1 for v in feature):
        raise _node_error(node_idx, node, "invalid Reshape target")

    known = 1
    for value in feature:
        if value > 0:
            known *= value

    if -1 in feature:
        if known <= 0 or current_dim % known != 0:
            raise _node_error(node_idx, node, "Reshape cannot preserve feature count")
    elif known != current_dim:
        raise _node_error(
            node_idx,
            node,
            f"Reshape changes flattened feature count from {current_dim} to {known}",
        )


def lower_onnx_dense(path: str | Path) -> HardwareIR:
    """Lower a strict sequential dense ONNX subset into HardwareIR.

    Supported forms include variable-depth sequential Gemm/ReLU networks and
    shape-only Identity/Flatten/Reshape nodes. Branching, residual connections,
    dynamic feature dimensions and unsupported arithmetic are rejected explicitly.
    """
    onnx, numpy_helper = _onnx_modules()
    model = onnx.load(str(path))
    onnx.checker.check_model(model)
    graph = model.graph

    init = {x.name: numpy_helper.to_array(x) for x in graph.initializer}
    real_inputs = [x for x in graph.input if x.name not in init]
    if len(real_inputs) != 1:
        raise UnsupportedONNXGraph("compiler requires exactly one non-initializer input")
    if len(graph.output) != 1:
        raise UnsupportedONNXGraph("compiler requires exactly one graph output")

    input_dim = _static_input_dim(real_inputs[0])
    current = real_inputs[0].name
    current_dim = input_dim
    layers: list[DenseLayerIR] = []

    for node_idx, node in enumerate(graph.node):
        if node.op_type == "Gemm":
            if len(node.input) < 3:
                raise _node_error(node_idx, node, "Gemm must have A, B and C inputs")
            if node.input[0] != current:
                raise _node_error(node_idx, node, "branching/non-sequential dataflow")
            attrs = _attrs(node)
            trans_a = int(attrs.get("transA", 0))
            trans_b = int(attrs.get("transB", 0))
            alpha = float(attrs.get("alpha", 1.0))
            beta = float(attrs.get("beta", 1.0))
            if trans_a != 0 or alpha != 1.0 or beta != 1.0:
                raise _node_error(
                    node_idx,
                    node,
                    "only transA=0, alpha=1 and beta=1 Gemm is supported",
                )
            if node.input[1] not in init or node.input[2] not in init:
                raise _node_error(
                    node_idx,
                    node,
                    "Gemm weight and bias must be constant initializers",
                )
            weight = np.asarray(init[node.input[1]], dtype=np.float64)
            bias = np.asarray(init[node.input[2]], dtype=np.float64)
            if trans_b:
                weight = weight.T
            if weight.ndim != 2 or bias.ndim != 1:
                raise _node_error(
                    node_idx, node, "Gemm weight must be rank-2 and bias rank-1"
                )
            if int(weight.shape[0]) != current_dim:
                raise _node_error(
                    node_idx,
                    node,
                    f"Gemm input width {weight.shape[0]} does not match current width {current_dim}",
                )
            if int(weight.shape[1]) != int(bias.shape[0]):
                raise _node_error(node_idx, node, "Gemm bias/output width mismatch")

            layer = DenseLayerIR(
                name=node.name or f"gemm_{node_idx}",
                weight=weight,
                bias=bias,
                relu=False,
            )
            layers.append(layer)
            current_dim = layer.output_dim
            current = node.output[0]

        elif node.op_type == "Relu":
            if not layers or node.input[0] != current:
                raise _node_error(
                    node_idx, node, "Relu must directly follow the current supported tensor"
                )
            if layers[-1].relu:
                raise _node_error(node_idx, node, "duplicate Relu after the same Gemm")
            layers[-1].relu = True
            current = node.output[0]

        elif node.op_type == "Identity":
            if node.input[0] != current:
                raise _node_error(node_idx, node, "non-sequential Identity")
            current = node.output[0]

        elif node.op_type == "Flatten":
            if node.input[0] != current:
                raise _node_error(node_idx, node, "non-sequential Flatten")
            axis = int(_attrs(node).get("axis", 1))
            if axis != 1:
                raise _node_error(
                    node_idx,
                    node,
                    "only batch-preserving Flatten(axis=1) is supported",
                )
            current = node.output[0]

        elif node.op_type == "Reshape":
            if not node.input or node.input[0] != current:
                raise _node_error(node_idx, node, "non-sequential Reshape")
            if len(node.input) < 2 or node.input[1] not in init:
                raise _node_error(
                    node_idx,
                    node,
                    "Reshape target must be a constant initializer",
                )
            _validate_shape_only_reshape(init[node.input[1]], current_dim, node_idx, node)
            current = node.output[0]

        else:
            raise _node_error(node_idx, node, "unsupported operator")

    if not layers:
        raise UnsupportedONNXGraph("graph contains no supported Gemm layers")
    if current != graph.output[0].name:
        raise UnsupportedONNXGraph(
            "graph output is not the terminal sequential tensor; branching is not supported"
        )

    ir = HardwareIR(
        input_name=real_inputs[0].name,
        output_name=graph.output[0].name,
        input_dim=input_dim,
        layers=layers,
    )
    ir.validate()
    return ir


def float_forward_ir(ir: HardwareIR, x: np.ndarray, capture: bool = False):
    a = np.asarray(x, dtype=np.float64).reshape(len(x), ir.input_dim)
    activations = [a]
    for layer in ir.layers:
        a = a @ layer.weight + layer.bias
        if layer.relu:
            a = np.maximum(a, 0.0)
        activations.append(a)
    return activations if capture else a


def quantize_ir(ir: HardwareIR, calibration: np.ndarray, requant_shift: int = 30) -> QuantizedModel:
    calibration = np.asarray(calibration, dtype=np.float64).reshape(len(calibration), ir.input_dim)
    acts = float_forward_ir(ir, calibration, capture=True)
    activation_scales: list[float] = []
    for a in acts:
        peak = float(np.max(np.abs(a)))
        activation_scales.append(peak / 127.0 if peak else 1.0)

    qweights: list[np.ndarray] = []
    qbiases: list[np.ndarray] = []
    weight_scales: list[float] = []
    multipliers: list[int] = []
    for idx, layer in enumerate(ir.layers):
        peak = float(np.max(np.abs(layer.weight)))
        w_scale = peak / 127.0 if peak else 1.0
        qw = np.clip(np.rint(layer.weight / w_scale), -128, 127).astype(np.int8)
        qb = np.rint(layer.bias / (activation_scales[idx] * w_scale)).astype(np.int32)
        ratio = activation_scales[idx] * w_scale / activation_scales[idx + 1]
        multiplier = int(round(ratio * (1 << requant_shift)))
        qweights.append(qw)
        qbiases.append(qb)
        weight_scales.append(w_scale)
        multipliers.append(multiplier)

    return QuantizedModel(
        dims=ir.dims,
        qweights=tuple(qweights),
        qbiases=tuple(qbiases),
        activation_scales=tuple(activation_scales),
        weight_scales=tuple(weight_scales),
        multipliers=tuple(multipliers),
        requant_shift=requant_shift,
    )


def quantize_inputs(x: np.ndarray, scale: float, input_dim: int | None = None) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if input_dim is not None:
        arr = arr.reshape(len(arr), input_dim)
    return np.clip(np.rint(arr / scale), -128, 127).astype(np.int8)


def model_memory_report(model: QuantizedModel) -> dict[str, Any]:
    layer_rows = []
    for idx, (qw, qb) in enumerate(zip(model.qweights, model.qbiases), start=1):
        layer_rows.append(
            {
                "layer": idx,
                "input_dim": int(qw.shape[0]),
                "output_dim": int(qw.shape[1]),
                "weight_bytes": int(qw.size * qw.dtype.itemsize),
                "bias_bytes": int(qb.size * qb.dtype.itemsize),
            }
        )
    weight_bytes = sum(r["weight_bytes"] for r in layer_rows)
    bias_bytes = sum(r["bias_bytes"] for r in layer_rows)
    peak_activation_bytes = max(
        int(a + b) for a, b in zip(model.dims[:-1], model.dims[1:])
    )
    return {
        "layers": layer_rows,
        "weight_bytes": int(weight_bytes),
        "bias_bytes": int(bias_bytes),
        "parameter_bytes": int(weight_bytes + bias_bytes),
        "peak_activation_bytes_int8_double_buffer_proxy": int(peak_activation_bytes),
    }


def quantization_report(ir: HardwareIR, model: QuantizedModel) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, layer in enumerate(ir.layers):
        rows.append(
            {
                "layer": idx + 1,
                "name": layer.name,
                "input_dim": layer.input_dim,
                "output_dim": layer.output_dim,
                "relu": bool(layer.relu),
                "input_activation_scale": float(model.activation_scales[idx]),
                "output_activation_scale": float(model.activation_scales[idx + 1]),
                "weight_scale": float(model.weight_scales[idx]),
                "requant_multiplier": int(model.multipliers[idx]),
                "requant_shift": int(model.requant_shift),
            }
        )
    return rows


def _hex_lines(values: np.ndarray, bits: int) -> str:
    width = bits // 4
    mask = (1 << bits) - 1
    flat = np.asarray(values).reshape(-1)
    return "\n".join(f"{int(v) & mask:0{width}x}" for v in flat) + "\n"


def _addr_width(n: int) -> int:
    return max(1, int(math.ceil(math.log2(n))))


def _emit_dense_rtl(result: ONNXCompileResult, out_dir: Path) -> None:
    qmodel = result.model
    dims = qmodel.dims
    nlayers = len(qmodel.qweights)
    if nlayers < 1:
        raise UnsupportedONNXGraph("RTL backend requires at least one dense layer")

    lanes = result.lanes
    shift = qmodel.requant_shift
    iw, ow = _addr_width(dims[0]), _addr_width(dims[-1])
    state_w = max(1, int(math.ceil(math.log2(nlayers + 2))))

    dim_params = ", ".join(f"D{i}={d}" for i, d in enumerate(dims))
    state_defs = ["S_IDLE=0"] + [f"S_L{i+1}={i+1}" for i in range(nlayers)] + [f"S_DONE={nlayers+1}"]
    state_param = ", ".join(state_defs)

    activations = "\n".join(
        f"    logic signed [7:0] a{i} [0:D{i}-1];" for i in range(nlayers + 1)
    )
    weights = "\n".join(
        f"    logic signed [7:0] w{i+1} [0:D{i+1}*D{i}-1];\n"
        f"    logic signed [31:0] b{i+1} [0:D{i+1}-1];"
        for i in range(nlayers)
    )
    reads = "\n".join(
        f'        $readmemh("weights/w{i+1}.hex", w{i+1}); '
        f'$readmemh("weights/b{i+1}.hex", b{i+1});'
        for i in range(nlayers)
    )
    mac_cases = "\n".join(
        f"""            S_L{i+1}: for (lane = 0; lane < LANES; lane = lane + 1)
                if (base_idx + lane < D{i})
                    mac_sum = mac_sum + $signed(a{i}[base_idx+lane]) * $signed(w{i+1}[out_idx*D{i} + base_idx+lane]);"""
        for i in range(nlayers)
    )

    ff_cases = []
    for i in range(nlayers):
        next_state = f"S_L{i+2}" if i + 1 < nlayers else "S_DONE"
        relu = "1'b1" if result.ir.layers[i].relu else "1'b0"
        mult = qmodel.multipliers[i]
        ff_cases.append(
            f"""                S_L{i+1}: begin
                    if (base_idx + LANES >= D{i}) begin
                        a{i+1}[out_idx] <= rq8(next_acc + b{i+1}[out_idx], 32'sd{mult}, {relu});
                        acc <= 0; base_idx <= 0;
                        if (out_idx == D{i+1}-1) begin state <= {next_state}; out_idx <= 0; end
                        else out_idx <= out_idx + 1;
                    end else begin acc <= next_acc; base_idx <= base_idx + LANES; end
                end"""
        )
    ff_cases_text = "\n".join(ff_cases)

    tick = chr(96)
    rtl = f'''{tick}timescale 1ns/1ps
module kernellum_dense_accel #(
    parameter int LANES = {lanes}
)(
    input  logic clk,
    input  logic rst,
    input  logic start,
    input  logic in_we,
    input  logic [{iw-1}:0] in_addr,
    input  logic signed [7:0] in_data,
    input  logic [{ow-1}:0] out_addr,
    output logic signed [7:0] out_data,
    output logic busy,
    output logic done
);
    localparam int {dim_params};
    localparam int SHIFT={shift};
    localparam int STATE_W={state_w};
    localparam logic [STATE_W-1:0] {state_param};

{activations}
{weights}

    logic [STATE_W-1:0] state;
    integer out_idx;
    integer base_idx;
    integer lane;
    logic signed [31:0] acc;
    logic signed [31:0] mac_sum;
    logic signed [31:0] next_acc;

    function automatic signed [7:0] rq8(input signed [31:0] value, input signed [31:0] mult, input bit relu);
        logic signed [63:0] prod, rounded, shifted;
        begin
            prod = $signed(value) * $signed(mult);
            if (prod >= 0) rounded = prod + (64'sd1 <<< (SHIFT-1));
            else rounded = prod - (64'sd1 <<< (SHIFT-1));
            shifted = rounded >>> SHIFT;
            if (relu && shifted < 0) shifted = 0;
            if (shifted > 127) rq8 = 8'sd127;
            else if (shifted < -128) rq8 = -8'sd128;
            else rq8 = shifted[7:0];
        end
    endfunction

    initial begin
{reads}
    end

    always_comb begin
        mac_sum = 32'sd0;
        lane = 0;
        case (state)
{mac_cases}
            default: mac_sum = 32'sd0;
        endcase
        next_acc = acc + mac_sum;
    end

    assign out_data = a{nlayers}[out_addr];

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE; busy <= 1'b0; done <= 1'b0;
            out_idx <= 0; base_idx <= 0; acc <= 0;
        end else begin
            done <= 1'b0;
            if (in_we && !busy) a0[in_addr] <= in_data;
            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin busy <= 1'b1; state <= S_L1; out_idx <= 0; base_idx <= 0; acc <= 0; end
                end
{ff_cases_text}
                S_DONE: begin busy <= 1'b0; done <= 1'b1; state <= S_IDLE; end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
'''
    (out_dir / "kernellum_dense_accel.sv").write_text(rtl)

    ns = min(16, len(result.qinputs))
    tb = f'''{tick}timescale 1ns/1ps
module tb_kernellum_dense_accel;
    localparam int NS={ns}, IN0={dims[0]}, OUT={dims[-1]};
    logic clk=0; always #5 clk=~clk;
    logic rst,start,in_we; logic [{iw-1}:0] in_addr; logic signed [7:0] in_data;
    logic [{ow-1}:0] out_addr; logic signed [7:0] out_data; logic busy,done;
    logic signed [7:0] golden_inputs [0:NS*IN0-1];
    logic signed [7:0] golden_outputs [0:NS*OUT-1];
    integer s,i,j,errors=0;
    kernellum_dense_accel dut(.clk(clk),.rst(rst),.start(start),.in_we(in_we),.in_addr(in_addr),.in_data(in_data),.out_addr(out_addr),.out_data(out_data),.busy(busy),.done(done));
    initial begin
      $readmemh("weights/golden_inputs.hex", golden_inputs); $readmemh("weights/golden_outputs.hex", golden_outputs);
      rst=1; start=0; in_we=0; in_addr=0; in_data=0; out_addr=0; repeat(4) @(posedge clk); rst<=0;
      for(s=0;s<NS;s=s+1) begin
        for(i=0;i<IN0;i=i+1) begin @(negedge clk); in_we<=1; in_addr<=i; in_data<=golden_inputs[s*IN0+i]; end
        @(negedge clk); in_we<=0; start<=1; @(negedge clk); start<=0; wait(done===1'b1);
        for(j=0;j<OUT;j=j+1) begin out_addr=j; #1; if($signed(out_data)!==$signed(golden_outputs[s*OUT+j])) errors=errors+1; end
        @(posedge clk);
      end
      if(errors==0) begin $display("KERNELLUM_ONNX_RTL_PASS samples=%0d",NS); $finish; end
      else begin $display("KERNELLUM_ONNX_RTL_FAIL errors=%0d",errors); $fatal(1); end
    end
endmodule
'''
    (out_dir / "tb_kernellum_dense_accel.sv").write_text(tb)


def compile_onnx_dense(
    model_path: str | Path,
    calibration: np.ndarray,
    golden_inputs: np.ndarray,
    out_dir: str | Path,
    *,
    target: str = "ulx3s-85f",
    clock_mhz_assumption: float = 100.0,
    latency_target_us: float = 10.0,
) -> ONNXCompileResult:
    if target not in FPGA_TARGETS:
        raise ValueError(f"unknown FPGA target: {target}")

    ir = lower_onnx_dense(model_path)
    qmodel = quantize_ir(ir, calibration)
    selected, candidates = search_architecture(
        qmodel.dims,
        clock_mhz_assumption=clock_mhz_assumption,
        latency_target_us=latency_target_us,
    )

    qinputs = quantize_inputs(golden_inputs, qmodel.activation_scales[0], ir.input_dim)
    qoutputs = int_forward(qmodel, qinputs)
    cycle = cycle_forward(qmodel, qinputs, int(selected["lanes"]))
    if not np.array_equal(qoutputs, cycle):
        raise AssertionError("ONNX-lowered cycle model does not match vector INT8 reference")

    result = ONNXCompileResult(
        ir=ir,
        model=qmodel,
        qinputs=qinputs,
        qoutputs=qoutputs,
        lanes=int(selected["lanes"]),
        cycles=int(selected["cycles"]),
        modeled_latency_us=float(selected["latency_us"]),
        target=target,
        architecture_candidates=tuple(candidates),
    )

    out = Path(out_dir)
    weights_dir = out / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    for idx, qw in enumerate(qmodel.qweights, 1):
        (weights_dir / f"w{idx}.hex").write_text(_hex_lines(qw.T, 8))
    for idx, qb in enumerate(qmodel.qbiases, 1):
        (weights_dir / f"b{idx}.hex").write_text(_hex_lines(qb, 32))
    (weights_dir / "golden_inputs.hex").write_text(_hex_lines(qinputs[:16], 8))
    (weights_dir / "golden_outputs.hex").write_text(_hex_lines(qoutputs[:16], 8))

    _emit_dense_rtl(result, out)

    manifest = {
        "frontend": "onnx-v0.2",
        "supported_subset": SUPPORTED_SUBSET,
        "ir": ir.summary(),
        "target": FPGA_TARGETS[target].__dict__,
        "lanes": result.lanes,
        "cycles": result.cycles,
        "clock_mhz_assumption": float(clock_mhz_assumption),
        "latency_target_us": float(latency_target_us),
        "modeled_latency_us": result.modeled_latency_us,
        "architecture_candidates": list(candidates),
        "golden_samples": int(min(16, len(qinputs))),
        "cycle_model_exact": True,
        "memory": model_memory_report(qmodel),
        "quantization": quantization_report(ir, qmodel),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Kernellum Compiler v0.2 ONNX front-end")
    parser.add_argument("model", help="ONNX model path")
    parser.add_argument("--calibration", required=True, help=".npy calibration matrix")
    parser.add_argument("--golden", required=True, help=".npy golden input matrix")
    parser.add_argument("--out", default="artifacts/onnx_dense")
    parser.add_argument("--target", default="ulx3s-85f", choices=sorted(FPGA_TARGETS))
    parser.add_argument("--clock-mhz", type=float, default=100.0)
    parser.add_argument("--latency-us", type=float, default=10.0)
    args = parser.parse_args()

    result = compile_onnx_dense(
        args.model,
        np.load(args.calibration),
        np.load(args.golden),
        args.out,
        target=args.target,
        clock_mhz_assumption=args.clock_mhz,
        latency_target_us=args.latency_us,
    )
    print(f"lowered dims: {result.ir.dims}")
    print(f"target: {result.target}")
    print(f"architecture: {result.lanes} lanes, {result.cycles} cycles")
    print(f"modeled latency: {result.modeled_latency_us:.3f} us")


if __name__ == "__main__":
    main()
