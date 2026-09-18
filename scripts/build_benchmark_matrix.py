from __future__ import annotations

import json
import math
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


def _hex_lines(values: np.ndarray, bits: int = 8) -> str:
    width = bits // 4
    mask = (1 << bits) - 1
    return "\n".join(f"{int(v) & mask:0{width}x}" for v in np.asarray(values).reshape(-1)) + "\n"


def emit_ulx3s_demo_wrapper(case_dir: Path, dims: tuple[int, int, int, int], result) -> None:
    d0, _, _, d3 = dims
    if d3 > 16:
        raise ValueError("ULX3S benchmark wrapper currently supports at most 16 output classes")

    iw = max(1, int(math.ceil(math.log2(d0))))
    ow = max(1, int(math.ceil(math.log2(d3))))
    (case_dir / "weights" / "demo_input.hex").write_text(_hex_lines(result.qinputs[0], 8))

    wrapper = f'''\`timescale 1ns/1ps
module kernellum_demo_top #(
    parameter integer ACCEL_LANES = {result.lanes}
)(
    input  logic clk,
    input  logic rst,
    input  logic start_btn,
    output logic [3:0] class_led,
    output logic done_led
);
    localparam int D0={d0}, D3={d3};
    localparam logic [2:0] T_IDLE=3'd0, T_LOAD=3'd1, T_START=3'd2, T_WAIT=3'd3, T_SCAN=3'd4, T_DONE=3'd5;

    logic [2:0] tstate;
    logic accel_start, in_we;
    logic [{iw-1}:0] in_addr;
    logic signed [7:0] in_data;
    logic [{ow-1}:0] out_addr;
    logic signed [7:0] out_data;
    logic busy, done;
    logic signed [7:0] demo_input [0:D0-1];
    logic signed [7:0] best_val;
    logic [3:0] best_idx;
    integer load_idx;
    integer scan_idx;

    initial $readmemh("weights/demo_input.hex", demo_input);

    kernellum_dense3_accel #(.LANES(ACCEL_LANES)) accel(
        .clk(clk), .rst(rst), .start(accel_start), .in_we(in_we), .in_addr(in_addr), .in_data(in_data),
        .out_addr(out_addr), .out_data(out_data), .busy(busy), .done(done)
    );

    always_comb begin
        in_we = (tstate == T_LOAD);
        accel_start = (tstate == T_START);
        in_addr = load_idx[{iw-1}:0];
        in_data = demo_input[load_idx];
        out_addr = scan_idx[{ow-1}:0];
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            tstate <= T_IDLE;
            load_idx <= 0;
            scan_idx <= 0;
            best_val <= -8'sd128;
            best_idx <= 0;
            class_led <= 0;
            done_led <= 1'b0;
        end else begin
            done_led <= 1'b0;
            case (tstate)
                T_IDLE: if (start_btn) begin load_idx <= 0; tstate <= T_LOAD; end
                T_LOAD: begin
                    if (load_idx == D0-1) tstate <= T_START;
                    else load_idx <= load_idx + 1;
                end
                T_START: tstate <= T_WAIT;
                T_WAIT: if (done) begin
                    scan_idx <= 0;
                    best_val <= -8'sd128;
                    best_idx <= 0;
                    tstate <= T_SCAN;
                end
                T_SCAN: begin
                    if ($signed(out_data) > $signed(best_val)) begin
                        best_val <= out_data;
                        best_idx <= scan_idx[3:0];
                    end
                    if (scan_idx == D3-1) tstate <= T_DONE;
                    else scan_idx <= scan_idx + 1;
                end
                T_DONE: begin
                    class_led <= best_idx;
                    done_led <= 1'b1;
                    tstate <= T_IDLE;
                end
                default: tstate <= T_IDLE;
            endcase
        end
    end
endmodule
'''
    (case_dir / "kernellum_demo_top.sv").write_text(wrapper)


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
        emit_ulx3s_demo_wrapper(case_dir, dims, result)
        rows.append(
            {
                "case": name,
                "dims": list(dims),
                "lanes": result.lanes,
                "cycles": result.cycles,
                "modeled_latency_us_at_100mhz": result.modeled_latency_us,
                "cycle_reference_exact": True,
                "rtl_emitted": (case_dir / "kernellum_dense3_accel.sv").exists(),
                "board_wrapper_emitted": (case_dir / "kernellum_demo_top.sv").exists(),
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
        "| Case | Dims | Selected lanes | Cycles | Modeled latency @100 MHz | Cycle/reference | RTL | Board wrapper |",
        "|---|---|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for row in rows:
        dims_text = " → ".join(str(x) for x in row["dims"])
        lines.append(
            f'| {row["case"]} | {dims_text} | {row["lanes"]} | {row["cycles"]} | '
            f'{row["modeled_latency_us_at_100mhz"]:.2f} µs | exact | emitted | emitted |'
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This matrix tests compiler shape generality with synthetic deterministic graphs. "
            "It does **not** establish application accuracy, post-route timing, measured FPGA performance, "
            "power/energy, or external design-partner validation. Board-targeted P&R is a separate evidence step.",
            "",
        ]
    )
    (root / "SUMMARY.md").write_text("\n".join(lines))
    print(f"KERNELLUM_BENCHMARK_MATRIX_PASS cases={len(rows)}")


if __name__ == "__main__":
    main()
