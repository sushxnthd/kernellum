from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier


@dataclass(frozen=True)
class QuantizedModel:
    dims: tuple[int, ...]
    qweights: tuple[np.ndarray, ...]
    qbiases: tuple[np.ndarray, ...]
    activation_scales: tuple[float, ...]
    weight_scales: tuple[float, ...]
    multipliers: tuple[int, ...]
    requant_shift: int


@dataclass(frozen=True)
class DemoBuild:
    model: QuantizedModel
    X_test: np.ndarray
    y_test: np.ndarray
    qinputs: np.ndarray
    qoutputs: np.ndarray
    float_predictions: np.ndarray
    int_predictions: np.ndarray
    float_accuracy: float
    int_accuracy: float
    prediction_agreement: float
    lanes: int
    cycles: int
    modeled_latency_us: float
    architecture_candidates: tuple[dict, ...]


def load_demo_data(random_state: int = 42):
    X, y = load_digits(return_X_y=True)
    X = X.astype(np.float64) / 16.0
    return train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=y,
    )


def train_demo_model(X_train: np.ndarray, y_train: np.ndarray, seed: int = 11) -> MLPClassifier:
    clf = MLPClassifier(
        hidden_layer_sizes=(32, 16),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        learning_rate_init=1e-3,
        max_iter=1000,
        random_state=seed,
        early_stopping=False,
    )
    clf.fit(X_train, y_train)
    return clf


def float_activations(clf: MLPClassifier, X: np.ndarray) -> list[np.ndarray]:
    acts = [X]
    a = X
    for idx, (w, b) in enumerate(zip(clf.coefs_, clf.intercepts_)):
        z = a @ w + b
        a = np.maximum(z, 0.0) if idx < len(clf.coefs_) - 1 else z
        acts.append(a)
    return acts


def quantize_model(clf: MLPClassifier, X_cal: np.ndarray, requant_shift: int = 30) -> QuantizedModel:
    acts = float_activations(clf, X_cal)
    activation_scales = [1.0 / 127.0]
    for a in acts[1:]:
        peak = float(np.max(np.abs(a)))
        activation_scales.append(peak / 127.0 if peak else 1.0)

    qweights: list[np.ndarray] = []
    qbiases: list[np.ndarray] = []
    weight_scales: list[float] = []
    multipliers: list[int] = []

    for layer, (w, b) in enumerate(zip(clf.coefs_, clf.intercepts_)):
        peak = float(np.max(np.abs(w)))
        w_scale = peak / 127.0 if peak else 1.0
        qw = np.clip(np.rint(w / w_scale), -128, 127).astype(np.int8)
        qb = np.rint(b / (activation_scales[layer] * w_scale)).astype(np.int32)
        ratio = activation_scales[layer] * w_scale / activation_scales[layer + 1]
        multiplier = int(round(ratio * (1 << requant_shift)))
        qweights.append(qw)
        qbiases.append(qb)
        weight_scales.append(w_scale)
        multipliers.append(multiplier)

    dims = (clf.coefs_[0].shape[0],) + tuple(w.shape[1] for w in clf.coefs_)
    return QuantizedModel(
        dims=tuple(int(x) for x in dims),
        qweights=tuple(qweights),
        qbiases=tuple(qbiases),
        activation_scales=tuple(float(x) for x in activation_scales),
        weight_scales=tuple(float(x) for x in weight_scales),
        multipliers=tuple(multipliers),
        requant_shift=requant_shift,
    )


def quantize_inputs(X: np.ndarray, scale: float) -> np.ndarray:
    return np.clip(np.rint(X / scale), -128, 127).astype(np.int8)


def requantize(values: np.ndarray, multiplier: int, shift: int, relu: bool) -> np.ndarray:
    values64 = values.astype(np.int64)
    prod = values64 * np.int64(multiplier)
    half = np.int64(1 << (shift - 1))
    rounded = np.where(prod >= 0, prod + half, prod - half)
    shifted = rounded >> shift
    if relu:
        shifted = np.maximum(shifted, 0)
    return np.clip(shifted, -128, 127).astype(np.int8)


def int_forward(qmodel: QuantizedModel, qinputs: np.ndarray) -> np.ndarray:
    a = qinputs.astype(np.int8, copy=False)
    for layer, (qw, qb, mult) in enumerate(zip(qmodel.qweights, qmodel.qbiases, qmodel.multipliers)):
        acc = a.astype(np.int32) @ qw.astype(np.int32) + qb.astype(np.int32)
        a = requantize(acc, mult, qmodel.requant_shift, relu=layer < len(qmodel.qweights) - 1)
    return a


def cycle_forward_one(qmodel: QuantizedModel, qinput: np.ndarray, lanes: int) -> np.ndarray:
    a = qinput.astype(np.int8, copy=True)
    for layer, (qw, qb, mult) in enumerate(zip(qmodel.qweights, qmodel.qbiases, qmodel.multipliers)):
        in_dim, out_dim = qw.shape
        out = np.empty(out_dim, dtype=np.int8)
        for out_idx in range(out_dim):
            acc = 0
            for base in range(0, in_dim, lanes):
                mac = 0
                for lane in range(lanes):
                    idx = base + lane
                    if idx < in_dim:
                        mac += int(a[idx]) * int(qw[idx, out_idx])
                acc += mac
            acc += int(qb[out_idx])
            out[out_idx] = requantize(
                np.array([acc], dtype=np.int64),
                mult,
                qmodel.requant_shift,
                relu=layer < len(qmodel.qweights) - 1,
            )[0]
        a = out
    return a


def cycle_forward(qmodel: QuantizedModel, qinputs: np.ndarray, lanes: int) -> np.ndarray:
    return np.stack([cycle_forward_one(qmodel, row, lanes) for row in qinputs], axis=0)


def compute_cycles(dims: Iterable[int], lanes: int) -> int:
    dims = list(dims)
    total = 0
    for in_dim, out_dim in zip(dims[:-1], dims[1:]):
        mac_cycles = (in_dim + lanes - 1) // lanes
        # Physical-feedback backend: final accumulation is followed by
        # registered requant multiply and registered round/saturate writeback.
        total += out_dim * (mac_cycles + 2)
    return int(total)


def search_architecture(
    dims: Iterable[int],
    lane_options: Iterable[int] = (1, 2, 4, 8, 16),
    clock_mhz_assumption: float = 100.0,
    latency_target_us: float = 10.0,
):
    candidates = []
    for lanes in lane_options:
        cycles = compute_cycles(dims, lanes)
        latency_us = cycles / clock_mhz_assumption
        candidates.append(
            {
                "lanes": int(lanes),
                "cycles": int(cycles),
                "latency_us": float(latency_us),
                "multipliers": int(lanes),
                "meets_latency": bool(latency_us <= latency_target_us),
            }
        )
    feasible = [c for c in candidates if c["meets_latency"]]
    selected = min(feasible, key=lambda c: (c["lanes"], c["latency_us"])) if feasible else min(
        candidates, key=lambda c: c["latency_us"]
    )
    return selected, tuple(candidates)


def build_demo() -> DemoBuild:
    X_train, X_test, y_train, y_test = load_demo_data()
    clf = train_demo_model(X_train, y_train)
    qmodel = quantize_model(clf, X_train)
    qinputs = quantize_inputs(X_test, qmodel.activation_scales[0])
    qoutputs = int_forward(qmodel, qinputs)
    float_predictions = clf.predict(X_test)
    int_predictions = np.argmax(qoutputs.astype(np.int16), axis=1)
    selected, candidates = search_architecture(qmodel.dims)
    cycle_outputs = cycle_forward(qmodel, qinputs, selected["lanes"])
    if not np.array_equal(cycle_outputs, qoutputs):
        raise AssertionError("cycle-accurate model does not match vector INT8 reference")
    return DemoBuild(
        model=qmodel,
        X_test=X_test,
        y_test=y_test,
        qinputs=qinputs,
        qoutputs=qoutputs,
        float_predictions=float_predictions,
        int_predictions=int_predictions,
        float_accuracy=float(accuracy_score(y_test, float_predictions)),
        int_accuracy=float(accuracy_score(y_test, int_predictions)),
        prediction_agreement=float(np.mean(float_predictions == int_predictions)),
        lanes=int(selected["lanes"]),
        cycles=int(selected["cycles"]),
        modeled_latency_us=float(selected["latency_us"]),
        architecture_candidates=candidates,
    )


def _hex_lines(values: np.ndarray, bits: int) -> str:
    width = bits // 4
    mask = (1 << bits) - 1
    flat = np.asarray(values).reshape(-1)
    return "\n".join(f"{int(v) & mask:0{width}x}" for v in flat) + "\n"


def write_weight_files(build: DemoBuild, weights_dir: Path, golden_samples: int = 32) -> None:
    weights_dir.mkdir(parents=True, exist_ok=True)
    for idx, qw in enumerate(build.model.qweights, start=1):
        # RTL indexes weights as output-major: w[out * IN + input]
        (weights_dir / f"w{idx}.hex").write_text(_hex_lines(qw.T, 8))
    for idx, qb in enumerate(build.model.qbiases, start=1):
        (weights_dir / f"b{idx}.hex").write_text(_hex_lines(qb, 32))
    (weights_dir / "golden_inputs.hex").write_text(_hex_lines(build.qinputs[:golden_samples], 8))
    (weights_dir / "golden_outputs.hex").write_text(_hex_lines(build.qoutputs[:golden_samples], 8))
    (weights_dir / "demo_input.hex").write_text(_hex_lines(build.qinputs[0], 8))


def emit_rtl(build: DemoBuild, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    qmodel = build.model
    d0, d1, d2, d3 = qmodel.dims
    m1, m2, m3 = qmodel.multipliers
    shift = qmodel.requant_shift
    lanes = build.lanes

    rtl = f'''`timescale 1ns/1ps
module kernellum_mlp_accel #(
    parameter int LANES = {lanes}
)(
    input  logic clk,
    input  logic rst,
    input  logic start,
    input  logic in_we,
    input  logic [$clog2({d0})-1:0] in_addr,
    input  logic signed [7:0] in_data,
    input  logic [$clog2({d3})-1:0] out_addr,
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
        logic signed [63:0] rounded;
        logic signed [63:0] shifted;
        begin
            if (prod >= 0)
                rounded = prod + (64'sd1 <<< (SHIFT-1));
            else
                rounded = prod - (64'sd1 <<< (SHIFT-1));
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
                    acc <= 0;
                    base_idx <= 0;
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
    (out_dir / "kernellum_mlp_accel.sv").write_text(rtl)

    tb = f'''`timescale 1ns/1ps
module tb_kernellum_mlp_accel;
    localparam int NS = 32;
    localparam int IN0 = {d0};
    localparam int OUT = {d3};
    logic clk = 0; always #5 clk = ~clk;
    logic rst, start, in_we;
    logic [5:0] in_addr;
    logic signed [7:0] in_data;
    logic [3:0] out_addr;
    logic signed [7:0] out_data;
    logic busy, done;
    logic signed [7:0] golden_inputs [0:NS*IN0-1];
    logic signed [7:0] golden_outputs [0:NS*OUT-1];
    integer s, i, j, errors = 0;

    kernellum_mlp_accel dut(.clk(clk), .rst(rst), .start(start), .in_we(in_we), .in_addr(in_addr), .in_data(in_data),
        .out_addr(out_addr), .out_data(out_data), .busy(busy), .done(done));

    initial begin
        $readmemh("weights/golden_inputs.hex", golden_inputs);
        $readmemh("weights/golden_outputs.hex", golden_outputs);
        rst = 1; start = 0; in_we = 0; in_addr = 0; in_data = 0; out_addr = 0;
        repeat (4) @(posedge clk); rst <= 0;
        for (s = 0; s < NS; s = s + 1) begin
            for (i = 0; i < IN0; i = i + 1) begin
                @(negedge clk);
                in_we <= 1; in_addr <= i[5:0]; in_data <= golden_inputs[s*IN0+i];
            end
            @(negedge clk); in_we <= 0; start <= 1;
            @(negedge clk); start <= 0;
            wait (done === 1'b1);
            for (j = 0; j < OUT; j = j + 1) begin
                out_addr = j[3:0]; #1;
                if ($signed(out_data) !== $signed(golden_outputs[s*OUT+j])) begin
                    $display("MISMATCH sample=%0d out=%0d got=%0d exp=%0d", s, j, $signed(out_data), $signed(golden_outputs[s*OUT+j]));
                    errors = errors + 1;
                end
            end
            @(posedge clk);
        end
        if (errors == 0) begin
            $display("KERNELLUM_RTL_PASS samples=%0d", NS); $finish;
        end else begin
            $display("KERNELLUM_RTL_FAIL errors=%0d", errors); $fatal(1);
        end
    end
endmodule
'''
    (out_dir / "tb_kernellum_mlp_accel.sv").write_text(tb)

    demo = f'''`timescale 1ns/1ps
module kernellum_demo_top #(
    parameter integer ACCEL_LANES = {lanes}
)(
    input  logic clk,
    input  logic rst,
    input  logic start_btn,
    output logic [3:0] class_led,
    output logic done_led
);
    localparam logic [2:0] T_IDLE=3'd0, T_LOAD=3'd1, T_START=3'd2, T_WAIT=3'd3, T_SCAN=3'd4, T_DONE=3'd5;
    logic [2:0] tstate;
    logic accel_start, in_we;
    logic [5:0] in_addr;
    logic signed [7:0] in_data;
    logic [3:0] out_addr;
    logic signed [7:0] out_data;
    logic busy, done;
    logic signed [7:0] demo_input [0:63];
    logic signed [7:0] best_val;
    logic [3:0] best_idx;
    integer load_idx;
    integer scan_idx;

    initial $readmemh("weights/demo_input.hex", demo_input);

    kernellum_mlp_accel #(.LANES(ACCEL_LANES)) accel(
        .clk(clk), .rst(rst), .start(accel_start), .in_we(in_we), .in_addr(in_addr), .in_data(in_data),
        .out_addr(out_addr), .out_data(out_data), .busy(busy), .done(done)
    );

    always_comb begin
        in_we = (tstate == T_LOAD);
        accel_start = (tstate == T_START);
        in_addr = load_idx[5:0];
        in_data = demo_input[load_idx];
        out_addr = scan_idx[3:0];
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            tstate <= T_IDLE; load_idx <= 0; scan_idx <= 0;
            best_val <= -8'sd128; best_idx <= 0; class_led <= 0; done_led <= 1'b0;
        end else begin
            done_led <= 1'b0;
            case (tstate)
                T_IDLE: if (start_btn) begin load_idx <= 0; tstate <= T_LOAD; end
                T_LOAD: begin if (load_idx == 63) tstate <= T_START; else load_idx <= load_idx + 1; end
                T_START: tstate <= T_WAIT;
                T_WAIT: if (done) begin scan_idx <= 0; best_val <= -8'sd128; best_idx <= 0; tstate <= T_SCAN; end
                T_SCAN: begin
                    if ($signed(out_data) > $signed(best_val)) begin best_val <= out_data; best_idx <= scan_idx[3:0]; end
                    if (scan_idx == 9) tstate <= T_DONE; else scan_idx <= scan_idx + 1;
                end
                T_DONE: begin class_led <= best_idx; done_led <= 1'b1; tstate <= T_IDLE; end
                default: tstate <= T_IDLE;
            endcase
        end
    end
endmodule
'''
    (out_dir / "kernellum_demo_top.sv").write_text(demo)


def write_manifest(build: DemoBuild, out_dir: Path) -> dict:
    manifest = {
        "name": "digits_mlp_int8",
        "dataset": "sklearn.datasets.load_digits",
        "dims": list(build.model.dims),
        "lanes": build.lanes,
        "clock_mhz_assumption": 100,
        "latency_target_us": 10,
        "requant_shift": build.model.requant_shift,
        "multipliers": list(build.model.multipliers),
        "activation_scales": list(build.model.activation_scales),
        "weight_scales": list(build.model.weight_scales),
        "test_samples": int(len(build.y_test)),
        "golden_rtl_samples": 32,
        "float_accuracy": build.float_accuracy,
        "int8_accuracy": build.int_accuracy,
        "prediction_agreement": build.prediction_agreement,
        "core_cycles_per_inference": build.cycles,
        "cycle_model_latency_us": build.modeled_latency_us,
        "architecture_candidates": list(build.architecture_candidates),
        "cycle_accurate_matches_vector_model": True,
        "cycle_accurate_samples": int(len(build.y_test)),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def write_report(manifest: dict, out_dir: Path) -> None:
    rows = "\n".join(
        f'| {c["lanes"]} | {c["cycles"]} | {c["latency_us"]:.1f} | {"yes" if c["meets_latency"] else "no"} |'
        for c in manifest["architecture_candidates"]
    )
    report = f'''# Kernellum Compiler v0.1 — Technical Evidence Report

## Demonstrated workload

- Dataset: **scikit-learn handwritten digits**
- Network: **64 → 32 → 16 → 10**, ReLU hidden layers
- Quantization: **signed INT8 weights and activations**, 32-bit accumulators
- Held-out samples: **{manifest["test_samples"]}**
- Floating-point accuracy: **{manifest["float_accuracy"]*100:.2f}%**
- Integer pipeline accuracy: **{manifest["int8_accuracy"]*100:.2f}%**
- Float/INT8 prediction agreement: **{manifest["prediction_agreement"]*100:.2f}%**

## Architecture search

Constraint: ≤10 µs modeled core latency at a 100 MHz clock assumption, minimizing MAC-lane count.

| MAC lanes | Core cycles | Modeled latency (µs) | Meets target |
|---:|---:|---:|:---:|
{rows}

Selected architecture: **{manifest["lanes"]} lanes**, **{manifest["core_cycles_per_inference"]} core cycles**, **{manifest["cycle_model_latency_us"]:.1f} µs** at the 100 MHz assumption.

## Hardware-semantics verification

A separate cycle-accurate software model follows the same lane grouping, output-neuron scheduling, integer accumulation, requantization, ReLU, saturation and layer transitions as the generated RTL.

- Compared against the vectorized INT8 reference on **{manifest["cycle_accurate_samples"]}** held-out samples.
- Exact output-tensor match: **PASS**.
- Generated HDL testbench contains **{manifest["golden_rtl_samples"]}** held-out golden samples for HDL simulation.

## Generated hardware

- `kernellum_mlp_accel.sv` — synthesizable inference engine
- `kernellum_demo_top.sv` — simple FPGA demo wrapper
- `weights/*.hex` — network weights, biases and golden vectors
- `tb_kernellum_mlp_accel.sv` — end-to-end RTL testbench
- `scripts/run_eda.sh` — Icarus simulation + Yosys synthesis
- `.github/workflows/verify.yml` — CI reproduction

## Claim boundary

The repository build environment used to prepare this release does not include Icarus Verilog or Yosys. Therefore **no FPGA timing closure, resource utilization, power, Fmax, or physical-silicon claim is made here**.

The modeled latency is a cycle-count calculation at an assumed 100 MHz clock; it is **not** a measured FPGA latency.
'''
    (out_dir / "REPORT.md").write_text(report)


def generate_demo_artifacts(out_dir: str | Path = "artifacts/digits_int8") -> DemoBuild:
    out_dir = Path(out_dir)
    build = build_demo()
    write_weight_files(build, out_dir / "weights")
    emit_rtl(build, out_dir)
    manifest = write_manifest(build, out_dir)
    write_report(manifest, out_dir)
    return build
