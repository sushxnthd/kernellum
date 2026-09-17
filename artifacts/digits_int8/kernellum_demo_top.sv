`timescale 1ns/1ps
module kernellum_demo_top(
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

    kernellum_mlp_accel accel(
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
