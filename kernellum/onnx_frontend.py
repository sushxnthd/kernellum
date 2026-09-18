from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .compiler import QuantizedModel, cycle_forward, int_forward, search_architecture
from .ir import DenseLayerIR, FPGA_TARGETS, HardwareIR


class UnsupportedONNXGraph(ValueError):
    """Raised when the current alpha front-end cannot lower a graph safely."""


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


def lower_onnx_dense(path: str | Path) -> HardwareIR:
    """Lower a strict sequential Gemm/ReLU ONNX subset into HardwareIR.

    Supported graph form:
        input -> Gemm -> [Relu] -> Gemm -> [Relu] -> ... -> Gemm -> output

    Gemm weights/biases must be constant initializers. transA != 0, non-unit alpha/beta,
    branching, residuals and unsupported operators are rejected explicitly.
    """
    onnx, numpy_helper = _onnx_modules()
    model = onnx.load(str(path))
    onnx.checker.check_model(model)
    graph = model.graph

    init = {x.name: numpy_helper.to_array(x).astype(np.float64) for x in graph.initializer}
    real_inputs = [x for x in graph.input if x.name not in init]
    if len(real_inputs) != 1:
        raise UnsupportedONNXGraph("v0.2 alpha requires exactly one non-initializer input")
    if len(graph.output) != 1:
        raise UnsupportedONNXGraph("v0.2 alpha requires exactly one graph output")

    tensor_type = real_inputs[0].type.tensor_type
    dims = [d.dim_value for d in tensor_type.shape.dim]
    if not dims or dims[-1] <= 0:
        raise UnsupportedONNXGraph("input feature dimension must be statically known")
    input_dim = int(dims[-1])
    current = real_inputs[0].name
    layers: list[DenseLayerIR] = []

    for node_idx, node in enumerate(graph.node):
        if node.op_type == "Gemm":
            if len(node.input) < 3:
                raise UnsupportedONNXGraph("Gemm must have A, B and C inputs")
            if node.input[0] != current:
                raise UnsupportedONNXGraph("branching/non-sequential dataflow is not supported")
            attrs = _attrs(node)
            trans_a = int(attrs.get("transA", 0))
            trans_b = int(attrs.get("transB", 0))
            alpha = float(attrs.get("alpha", 1.0))
            beta = float(attrs.get("beta", 1.0))
            if trans_a != 0 or alpha != 1.0 or beta != 1.0:
                raise UnsupportedONNXGraph("only transA=0, alpha=1, beta=1 Gemm is supported")
            if node.input[1] not in init or node.input[2] not in init:
                raise UnsupportedONNXGraph("Gemm weight and bias must be constant initializers")
            weight = init[node.input[1]]
            bias = init[node.input[2]]
            if trans_b:
                weight = weight.T
            if weight.ndim != 2 or bias.ndim != 1:
                raise UnsupportedONNXGraph("Gemm weight must be rank-2 and bias rank-1")
            layer = DenseLayerIR(
                name=node.name or f"gemm_{node_idx}",
                weight=np.asarray(weight, dtype=np.float64),
                bias=np.asarray(bias, dtype=np.float64),
                relu=False,
            )
            layers.append(layer)
            current = node.output[0]
        elif node.op_type == "Relu":
            if not layers or node.input[0] != current:
                raise UnsupportedONNXGraph("Relu must directly follow a supported Gemm")
            if layers[-1].relu:
                raise UnsupportedONNXGraph("duplicate Relu after the same Gemm is not supported")
            layers[-1].relu = True
            current = node.output[0]
        elif node.op_type == "Identity":
            if node.input[0] != current:
                raise UnsupportedONNXGraph("non-sequential Identity is not supported")
            current = node.output[0]
        else:
            raise UnsupportedONNXGraph(f"unsupported ONNX operator: {node.op_type}")

    if current != graph.output[0].name:
        raise UnsupportedONNXGraph("graph output is not the terminal sequential tensor")

    ir = HardwareIR(
        input_name=real_inputs[0].name,
        output_name=graph.output[0].name,
        input_dim=input_dim,
        layers=layers,
    )
    ir.validate()
    return ir


def float_forward_ir(ir: HardwareIR, x: np.ndarray, capture: bool = False):
    a = np.asarray(x, dtype=np.float64)
    activations = [a]
    for layer in ir.layers:
        a = a @ layer.weight + layer.bias
        if layer.relu:
            a = np.maximum(a, 0.0)
        activations.append(a)
    return activations if capture else a


def quantize_ir(ir: HardwareIR, calibration: np.ndarray, requant_shift: int = 30) -> QuantizedModel:
    calibration = np.asarray(calibration, dtype=np.float64)
    if calibration.ndim != 2 or calibration.shape[1] != ir.input_dim:
        raise ValueError(f"calibration data must have shape [N, {ir.input_dim}]")
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


def quantize_inputs(x: np.ndarray, scale: float) -> np.ndarray:
    return np.clip(np.rint(np.asarray(x, dtype=np.float64) / scale), -128, 127).astype(np.int8)


def _hex_lines(values: np.ndarray, bits: int) -> str:
    width = bits // 4
    mask = (1 << bits) - 1
    flat = np.asarray(values).reshape(-1)
    return "\n".join(f"{int(v) & mask:0{width}x}" for v in flat) + "\n"


def _addr_width(n: int) -> int:
    return max(1, int(math.ceil(math.log2(n))))


def _emit_dense3_rtl(result: ONNXCompileResult, out_dir: Path) -> None:
    qmodel = result.model
    d0, d1, d2, d3 = qmodel.dims
    if len(qmodel.qweights) != 3:
        raise UnsupportedONNXGraph("current RTL backend requires exactly three Gemm layers")
    m1, m2, m3 = qmodel.multipliers
    shift = qmodel.requant_shift
    lanes = result.lanes
    iw, ow = _addr_width(d0), _addr_width(d3)

    rtl = f'''`timescale 1ns/1ps
module kernellum_dense3_accel #(
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
    localparam int D0={d0}, D1={d1}, D2={d2}, D3={d3};
    localparam int SHIFT={shift};
    localparam logic [2:0] S_IDLE=3'd0, S_L1=3'd1, S_L2=3'd2, S_L3=3'd3, S_RQ_MUL=3'd4, S_RQ_WRITE=3'd5, S_DONE=3'd6;

    logic signed [7:0] a0 [0:D0-1];
    logic signed [7:0] a1 [0:D1-1];
    logic signed [7:0] a2 [0:D2-1];
    logic signed [7:0] a3 [0:D3-1];
    logic signed [7:0] w1 [0:D1*D0-1];
    logic signed [7:0] w2 [0:D2*D1-1];
    logic signed [7:0] w3 [0:D3*D2-1];
    logic signed [31:0] b1 [0:D1-1];
    logic signed [31:0] b2 [0:D2-1];
    logic signed [31:0] b3 [0:D3-1];

    logic [2:0] state;
    integer out_idx;
    integer base_idx;
    integer lane;
    logic signed [31:0] acc;
    logic signed [31:0] mac_sum;
    logic signed [31:0] next_acc;
    logic [1:0] rq_layer;
    logic signed [31:0] rq_input;
    logic signed [31:0] rq_mult;
    logic signed [63:0] rq_prod;
    logic rq_relu;

    always_comb begin
        case (rq_layer)
            2'd1: begin rq_mult = 32'sd{m1}; rq_relu = 1'b1; end
            2'd2: begin rq_mult = 32'sd{m2}; rq_relu = 1'b1; end
            default: begin rq_mult = 32'sd{m3}; rq_relu = 1'b0; end
        endcase
    end

    function automatic signed [7:0] rq8_from_prod(input signed [63:0] prod, input bit relu);
        logic signed [63:0] rounded, shifted;
        begin
            if (prod >= 0) rounded = prod + (64'sd1 <<< (SHIFT-1));
            else rounded = prod - (64'sd1 <<< (SHIFT-1));
            shifted = rounded >>> SHIFT;
            if (relu && shifted < 0) shifted = 0;
            if (shifted > 127) rq8_from_prod = 8'sd127;
            else if (shifted < -128) rq8_from_prod = -8'sd128;
            else rq8_from_prod = shifted[7:0];
        end
    endfunction

    initial begin
        $readmemh("weights/w1.hex", w1); $readmemh("weights/b1.hex", b1);
        $readmemh("weights/w2.hex", w2); $readmemh("weights/b2.hex", b2);
        $readmemh("weights/w3.hex", w3); $readmemh("weights/b3.hex", b3);
    end

    always_comb begin
        mac_sum = 32'sd0;
        lane = 0;
        case (state)
            S_L1: for (lane = 0; lane < LANES; lane = lane + 1)
                if (base_idx + lane < D0)
                    mac_sum = mac_sum + $signed(a0[base_idx+lane]) * $signed(w1[out_idx*D0 + base_idx+lane]);
            S_L2: for (lane = 0; lane < LANES; lane = lane + 1)
                if (base_idx + lane < D1)
                    mac_sum = mac_sum + $signed(a1[base_idx+lane]) * $signed(w2[out_idx*D1 + base_idx+lane]);
            S_L3: for (lane = 0; lane < LANES; lane = lane + 1)
                if (base_idx + lane < D2)
                    mac_sum = mac_sum + $signed(a2[base_idx+lane]) * $signed(w3[out_idx*D2 + base_idx+lane]);
            default: mac_sum = 32'sd0;
        endcase
        next_acc = acc + mac_sum;
    end

    assign out_data = a3[out_addr];

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE; busy <= 1'b0; done <= 1'b0;
            out_idx <= 0; base_idx <= 0; acc <= 0;
            rq_layer <= 0; rq_input <= 0; rq_prod <= 0;
        end else begin
            done <= 1'b0;
            if (in_we && !busy) a0[in_addr] <= in_data;
            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin busy <= 1'b1; state <= S_L1; out_idx <= 0; base_idx <= 0; acc <= 0; end
                end
                S_L1: begin
                    if (base_idx + LANES >= D0) begin
                        rq_input <= next_acc + b1[out_idx];
                        rq_layer <= 2'd1;
                        state <= S_RQ_MUL;
                    end else begin acc <= next_acc; base_idx <= base_idx + LANES; end
                end
                S_L2: begin
                    if (base_idx + LANES >= D1) begin
                        rq_input <= next_acc + b2[out_idx];
                        rq_layer <= 2'd2;
                        state <= S_RQ_MUL;
                    end else begin acc <= next_acc; base_idx <= base_idx + LANES; end
                end
                S_L3: begin
                    if (base_idx + LANES >= D2) begin
                        rq_input <= next_acc + b3[out_idx];
                        rq_layer <= 2'd3;
                        state <= S_RQ_MUL;
                    end else begin acc <= next_acc; base_idx <= base_idx + LANES; end
                end
                S_RQ_MUL: begin
                    rq_prod <= $signed(rq_input) * $signed(rq_mult);
                    state <= S_RQ_WRITE;
                end
                S_RQ_WRITE: begin
                    acc <= 0; base_idx <= 0;
                    case (rq_layer)
                        2'd1: begin
                            a1[out_idx] <= rq8_from_prod(rq_prod, rq_relu);
                            if (out_idx == D1-1) begin state <= S_L2; out_idx <= 0; end
                            else begin state <= S_L1; out_idx <= out_idx + 1; end
                        end
                        2'd2: begin
                            a2[out_idx] <= rq8_from_prod(rq_prod, rq_relu);
                            if (out_idx == D2-1) begin state <= S_L3; out_idx <= 0; end
                            else begin state <= S_L2; out_idx <= out_idx + 1; end
                        end
                        default: begin
                            a3[out_idx] <= rq8_from_prod(rq_prod, rq_relu);
                            if (out_idx == D3-1) begin state <= S_DONE; out_idx <= 0; end
                            else begin state <= S_L3; out_idx <= out_idx + 1; end
                        end
                    endcase
                end
                S_DONE: begin busy <= 1'b0; done <= 1'b1; state <= S_IDLE; end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
'''
    (out_dir / "kernellum_dense3_accel.sv").write_text(rtl)

    ns = min(16, len(result.qinputs))
    tb = f'''`timescale 1ns/1ps
module tb_kernellum_dense3_accel;
    localparam int NS={ns}, IN0={d0}, OUT={d3};
    logic clk=0; always #5 clk=~clk;
    logic rst,start,in_we; logic [{iw-1}:0] in_addr; logic signed [7:0] in_data;
    logic [{ow-1}:0] out_addr; logic signed [7:0] out_data; logic busy,done;
    logic signed [7:0] golden_inputs [0:NS*IN0-1];
    logic signed [7:0] golden_outputs [0:NS*OUT-1];
    integer s,i,j,errors=0;
    kernellum_dense3_accel dut(.clk(clk),.rst(rst),.start(start),.in_we(in_we),.in_addr(in_addr),.in_data(in_data),.out_addr(out_addr),.out_data(out_data),.busy(busy),.done(done));
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
    (out_dir / "tb_kernellum_dense3_accel.sv").write_text(tb)


def compile_onnx_dense(
    model_path: str | Path,
    calibration: np.ndarray,
    golden_inputs: np.ndarray,
    out_dir: str | Path,
    *,
    target: str = "ecp5-85f",
    clock_mhz_assumption: float = 100.0,
    latency_target_us: float = 10.0,
) -> ONNXCompileResult:
    if target not in FPGA_TARGETS:
        raise ValueError(f"unknown FPGA target: {target}")
    ir = lower_onnx_dense(model_path)
    if len(ir.layers) != 3 or [layer.relu for layer in ir.layers] != [True, True, False]:
        raise UnsupportedONNXGraph(
            "current v0.2 RTL backend supports exactly Gemm→Relu→Gemm→Relu→Gemm"
        )
    qmodel = quantize_ir(ir, calibration)
    selected, candidates = search_architecture(
        qmodel.dims,
        clock_mhz_assumption=clock_mhz_assumption,
        latency_target_us=latency_target_us,
    )
    qinputs = quantize_inputs(golden_inputs, qmodel.activation_scales[0])
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
    )
    out = Path(out_dir)
    weights = out / "weights"
    weights.mkdir(parents=True, exist_ok=True)
    for idx, qw in enumerate(qmodel.qweights, 1):
        (weights / f"w{idx}.hex").write_text(_hex_lines(qw.T, 8))
    for idx, qb in enumerate(qmodel.qbiases, 1):
        (weights / f"b{idx}.hex").write_text(_hex_lines(qb, 32))
    (weights / "golden_inputs.hex").write_text(_hex_lines(qinputs[:16], 8))
    (weights / "golden_outputs.hex").write_text(_hex_lines(qoutputs[:16], 8))
    _emit_dense3_rtl(result, out)
    manifest = {
        "frontend": "onnx-v0.2-alpha",
        "supported_subset": "sequential Gemm/ReLU; current RTL backend = 3 dense layers",
        "ir": ir.summary(),
        "target": FPGA_TARGETS[target].__dict__,
        "lanes": result.lanes,
        "cycles": result.cycles,
        "modeled_latency_us": result.modeled_latency_us,
        "architecture_candidates": list(candidates),
        "golden_samples": int(min(16, len(qinputs))),
        "cycle_model_exact": True,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Kernellum Compiler v0.2 alpha ONNX front-end")
    parser.add_argument("model", help="ONNX model path")
    parser.add_argument("--calibration", required=True, help=".npy calibration matrix")
    parser.add_argument("--golden", required=True, help=".npy golden input matrix")
    parser.add_argument("--out", default="artifacts/onnx_dense3")
    parser.add_argument("--target", default="ecp5-85f", choices=sorted(FPGA_TARGETS))
    args = parser.parse_args()
    result = compile_onnx_dense(
        args.model,
        np.load(args.calibration),
        np.load(args.golden),
        args.out,
        target=args.target,
    )
    print(f"lowered dims: {result.ir.dims}")
    print(f"target: {result.target}")
    print(f"architecture: {result.lanes} lanes, {result.cycles} cycles")
    print(f"modeled latency: {result.modeled_latency_us:.3f} us")


if __name__ == "__main__":
    main()
