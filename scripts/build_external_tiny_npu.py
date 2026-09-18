from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

import numpy as np

from kernellum.onnx_frontend import compile_onnx_dense


# Validation branch deliberately reuses the exact pinned upstream artifact.
UPSTREAM_REPO = "harishsg993010/tiny-NPU"
UPSTREAM_COMMIT = "8216c22b762011aa20c05fc2768423fd12dda59d"
UPSTREAM_PATH = "models/overlap_perf_test.onnx"
UPSTREAM_GIT_BLOB_SHA1 = "070fb6c8f35e6f3b1d91e92143442367a25dc41b"
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    f"{UPSTREAM_REPO}/{UPSTREAM_COMMIT}/{UPSTREAM_PATH}"
)


def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode() + bytes([0])
    return hashlib.sha1(header + data).hexdigest()


def download_upstream_model(path: Path) -> dict[str, str | int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        data = response.read()

    actual_blob_sha = git_blob_sha1(data)
    if actual_blob_sha != UPSTREAM_GIT_BLOB_SHA1:
        raise RuntimeError(
            "upstream model integrity mismatch: "
            f"expected git blob {UPSTREAM_GIT_BLOB_SHA1}, got {actual_blob_sha}"
        )

    path.write_bytes(data)
    return {
        "repository": UPSTREAM_REPO,
        "commit": UPSTREAM_COMMIT,
        "path": UPSTREAM_PATH,
        "git_blob_sha1": actual_blob_sha,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "source_url": SOURCE_URL,
    }


def _hex_lines(values: np.ndarray, bits: int = 8) -> str:
    width = bits // 4
    mask = (1 << bits) - 1
    flat = np.asarray(values).reshape(-1)
    return chr(10).join(f"{int(v) & mask:0{width}x}" for v in flat) + chr(10)


def emit_board_wrapper(out_dir: Path, result) -> None:
    d0, _, _, d3 = result.ir.dims
    iw = max(1, int(math.ceil(math.log2(d0))))
    ow = max(1, int(math.ceil(math.log2(d3))))
    bestw = max(1, ow)

    (out_dir / "weights" / "demo_input.hex").write_text(
        _hex_lines(result.qinputs[0], 8)
    )

    wrapper = f'''`timescale 1ns/1ps
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
    localparam logic [2:0] T_IDLE=3'd0, T_LOAD=3'd1, T_START=3'd2,
                           T_WAIT=3'd3, T_SCAN=3'd4, T_DONE=3'd5;

    logic [2:0] tstate;
    logic accel_start, in_we;
    logic [{iw-1}:0] in_addr;
    logic signed [7:0] in_data;
    logic [{ow-1}:0] out_addr;
    logic signed [7:0] out_data;
    logic busy, done;
    logic signed [7:0] demo_input [0:D0-1];
    logic signed [7:0] best_val;
    logic [{bestw-1}:0] best_idx;
    integer load_idx;
    integer scan_idx;

    initial $readmemh("weights/demo_input.hex", demo_input);

    kernellum_dense3_accel #(.LANES(ACCEL_LANES)) accel(
        .clk(clk), .rst(rst), .start(accel_start),
        .in_we(in_we), .in_addr(in_addr), .in_data(in_data),
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
                T_IDLE: if (start_btn) begin
                    load_idx <= 0;
                    tstate <= T_LOAD;
                end
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
                        best_idx <= scan_idx[{bestw-1}:0];
                    end
                    if (scan_idx == D3-1) tstate <= T_DONE;
                    else scan_idx <= scan_idx + 1;
                end
                T_DONE: begin
                    // ULX3S reference wrapper exposes only the low nibble
                    // of this 32-way external workload's winning index.
                    class_led <= best_idx[3:0];
                    done_led <= 1'b1;
                    tstate <= T_IDLE;
                end
                default: tstate <= T_IDLE;
            endcase
        end
    end
endmodule
'''
    (out_dir / "kernellum_demo_top.sv").write_text(wrapper)


def main() -> None:
    out = Path("artifacts/external_tiny_npu")
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "overlap_perf_test.onnx"

    provenance = download_upstream_model(model_path)

    # The upstream performance-test model publishes graph/weights but no task
    # dataset. These deterministic inputs are used only for quantization and
    # cycle/reference exactness checks.
    rng = np.random.default_rng(20260918)
    calibration = rng.normal(0.0, 0.35, size=(128, 64)).astype(np.float64)
    golden = rng.normal(0.0, 0.35, size=(16, 64)).astype(np.float64)

    result = compile_onnx_dense(
        model_path,
        calibration=calibration,
        golden_inputs=golden,
        out_dir=out,
        target="ecp5-85f",
        latency_target_us=100.0,
    )
    if result.ir.dims != (64, 64, 64, 32):
        raise RuntimeError(f"unexpected upstream workload shape: {result.ir.dims}")

    emit_board_wrapper(out, result)

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(
        {
            "evidence_id": "KRN-EXT-001",
            "workload_kind": "third-party public ONNX model",
            "upstream": provenance,
            "calibration_source": "Kernellum deterministic synthetic inputs; seed=20260918",
            "external_model_unmodified": True,
            "board_wrapper_note": (
                "ULX3S P&R wrapper exposes low 4 bits of the 32-way argmax on LEDs; "
                "full outputs remain available in accelerator/testbench evidence."
            ),
            "claim_boundary": (
                "Externality applies to the upstream model graph/weights. Calibration "
                "and golden inputs are synthetic because the upstream performance-test "
                "model does not publish a task dataset. No application accuracy or "
                "customer-validation claim is made."
            ),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + chr(10))

    print(
        "KERNELLUM_EXT001_BUILD_PASS "
        f"dims={result.ir.dims} upstream_blob={provenance['git_blob_sha1']} "
        f"lanes={result.lanes} cycles={result.cycles}"
    )


if __name__ == "__main__":
    main()
