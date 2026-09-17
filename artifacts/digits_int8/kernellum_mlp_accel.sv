`timescale 1ns/1ps
module kernellum_mlp_accel #(
    parameter integer LANES = 4
)(
    input  logic clk,
    input  logic rst,
    input  logic start,
    input  logic in_we,
    input  logic [5:0] in_addr,
    input  logic signed [7:0] in_data,
    input  logic [3:0] out_addr,
    output logic signed [7:0] out_data,
    output logic busy,
    output logic done
);
    localparam integer IN0 = 64, H1 = 32, H2 = 16, OUT = 10;
    localparam integer SHIFT = 30;
    localparam integer M1 = 1441715, M2 = 2191310, M3 = 6953669;
    localparam logic [2:0] S_IDLE=3'd0, S_L1=3'd1, S_L2=3'd2, S_L3=3'd3, S_DONE=3'd4;

    logic [2:0] state;
    integer out_idx;
    integer in_base;
    integer lane;
    logic signed [31:0] acc;
    logic signed [31:0] mac_sum;
    logic signed [31:0] stage_total;

    logic signed [7:0] input_mem [0:IN0-1];
    logic signed [7:0] act1 [0:H1-1];
    logic signed [7:0] act2 [0:H2-1];
    logic signed [7:0] output_mem [0:OUT-1];

    logic signed [7:0] w1 [0:H1*IN0-1];
    logic signed [7:0] w2 [0:H2*H1-1];
    logic signed [7:0] w3 [0:OUT*H2-1];
    logic signed [31:0] b1 [0:H1-1];
    logic signed [31:0] b2 [0:H2-1];
    logic signed [31:0] b3 [0:OUT-1];

    initial begin
        $readmemh("weights/w1.hex", w1);
        $readmemh("weights/w2.hex", w2);
        $readmemh("weights/w3.hex", w3);
        $readmemh("weights/b1.hex", b1);
        $readmemh("weights/b2.hex", b2);
        $readmemh("weights/b3.hex", b3);
    end

    function automatic signed [7:0] requant8;
        input signed [31:0] a;
        input integer mult;
        input logic do_relu;
        logic signed [63:0] prod;
        logic signed [63:0] rounded;
        logic signed [63:0] shifted;
        begin
            prod = a * mult;
            if (prod >= 0)
                rounded = prod + (64'sd1 <<< (SHIFT-1));
            else
                rounded = prod - (64'sd1 <<< (SHIFT-1));
            shifted = rounded >>> SHIFT;
            if (do_relu && shifted < 0)
                requant8 = 8'sd0;
            else if (shifted > 127)
                requant8 = 8'sd127;
            else if (shifted < -128)
                requant8 = -8'sd128;
            else
                requant8 = shifted[7:0];
        end
    endfunction

    always_comb begin
        mac_sum = 32'sd0;
        case (state)
            S_L1: for (lane = 0; lane < LANES; lane = lane + 1)
                if ((in_base + lane) < IN0)
                    mac_sum = mac_sum + $signed(input_mem[in_base+lane]) * $signed(w1[out_idx*IN0 + in_base+lane]);
            S_L2: for (lane = 0; lane < LANES; lane = lane + 1)
                if ((in_base + lane) < H1)
                    mac_sum = mac_sum + $signed(act1[in_base+lane]) * $signed(w2[out_idx*H1 + in_base+lane]);
            S_L3: for (lane = 0; lane < LANES; lane = lane + 1)
                if ((in_base + lane) < H2)
                    mac_sum = mac_sum + $signed(act2[in_base+lane]) * $signed(w3[out_idx*H2 + in_base+lane]);
            default: mac_sum = 32'sd0;
        endcase
    end

    always_comb begin
        case (state)
            S_L1: stage_total = acc + mac_sum + b1[out_idx];
            S_L2: stage_total = acc + mac_sum + b2[out_idx];
            S_L3: stage_total = acc + mac_sum + b3[out_idx];
            default: stage_total = acc + mac_sum;
        endcase
    end

    always_comb out_data = output_mem[out_addr];

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE; busy <= 1'b0; done <= 1'b0;
            out_idx <= 0; in_base <= 0; acc <= 32'sd0;
        end else begin
            done <= 1'b0;
            if (in_we && !busy) input_mem[in_addr] <= in_data;
            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        busy <= 1'b1; out_idx <= 0; in_base <= 0; acc <= 32'sd0; state <= S_L1;
                    end
                end
                S_L1: begin
                    if ((in_base + LANES) >= IN0) begin
                        act1[out_idx] <= requant8(stage_total, M1, 1'b1);
                        acc <= 32'sd0; in_base <= 0;
                        if ((out_idx + 1) >= H1) begin out_idx <= 0; state <= S_L2; end
                        else out_idx <= out_idx + 1;
                    end else begin acc <= acc + mac_sum; in_base <= in_base + LANES; end
                end
                S_L2: begin
                    if ((in_base + LANES) >= H1) begin
                        act2[out_idx] <= requant8(stage_total, M2, 1'b1);
                        acc <= 32'sd0; in_base <= 0;
                        if ((out_idx + 1) >= H2) begin out_idx <= 0; state <= S_L3; end
                        else out_idx <= out_idx + 1;
                    end else begin acc <= acc + mac_sum; in_base <= in_base + LANES; end
                end
                S_L3: begin
                    if ((in_base + LANES) >= H2) begin
                        output_mem[out_idx] <= requant8(stage_total, M3, 1'b0);
                        acc <= 32'sd0; in_base <= 0;
                        if ((out_idx + 1) >= OUT) begin out_idx <= 0; state <= S_DONE; end
                        else out_idx <= out_idx + 1;
                    end else begin acc <= acc + mac_sum; in_base <= in_base + LANES; end
                end
                S_DONE: begin busy <= 1'b0; done <= 1'b1; state <= S_IDLE; end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
