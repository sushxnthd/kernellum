`timescale 1ns/1ps

// Distinct synthesis-repair intervention: lane-diverse invalid reset states.
//
// The prior stride-two routes repeatedly put the signed A operand's sign bit
// and B operand low bits on maximum-delay paths.  Keep one stride-two
// pipeline stage per two PEs, but replicate only A[7] and B[2:0] within each
// two-PE group.  The remaining bits and valid signals stay shared.  The
// Lane-diverse reset values make the replicas sequentially non-equivalent;
// keep attributes remain supplemental rather than being trusted as the repair.
module kernellum_preserved_selective_mac_array #(
    parameter integer ROWS = 8,
    parameter integer COLS = 8,
    parameter integer STRIDE = 2,
    parameter integer PRECISION = 8,
    parameter integer ACC_WIDTH = 32,
    parameter integer ROW_GROUPS = (ROWS + STRIDE - 1) / STRIDE,
    parameter integer COL_GROUPS = (COLS + STRIDE - 1) / STRIDE
) (
    input  wire                           clk,
    input  wire                           rst,
    input  wire                           clear_acc,
    input  wire                           step,
    input  wire [ROWS*PRECISION-1:0]      a_vec,
    input  wire [COLS*PRECISION-1:0]      b_vec,
    output wire [ROWS*COLS*ACC_WIDTH-1:0] acc_flat
);
    localparam integer B_REP_BITS = 3;
    localparam integer A_COMMON_BITS = PRECISION - 1;
    localparam integer B_COMMON_BITS = PRECISION - B_REP_BITS;

    wire signed [PRECISION-1:0] a_edge [0:ROWS-1];
    wire signed [PRECISION-1:0] b_edge [0:COLS-1];
    wire a_edge_valid [0:ROWS-1];
    wire b_edge_valid [0:COLS-1];

    genvar r, c, g;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_a_edge
            kernellum_delay_line #(
                .WIDTH(PRECISION), .DELAY(r / STRIDE)
            ) delay (
                .clk(clk), .rst(rst), .clear_pipe(clear_acc),
                .valid_in(step), .data_in(a_vec[r*PRECISION +: PRECISION]),
                .valid_out(a_edge_valid[r]), .data_out(a_edge[r])
            );
        end
        for (c = 0; c < COLS; c = c + 1) begin : g_b_edge
            kernellum_delay_line #(
                .WIDTH(PRECISION), .DELAY(c / STRIDE)
            ) delay (
                .clk(clk), .rst(rst), .clear_pipe(clear_acc),
                .valid_in(step), .data_in(b_vec[c*PRECISION +: PRECISION]),
                .valid_out(b_edge_valid[c]), .data_out(b_edge[c])
            );
        end
    endgenerate

    wire signed [A_COMMON_BITS-1:0] a_common [0:ROWS-1][0:COL_GROUPS-1];
    wire signed [B_COMMON_BITS-1:0] b_common [0:ROW_GROUPS-1][0:COLS-1];
    wire a_valid [0:ROWS-1][0:COL_GROUPS-1];
    wire b_valid [0:ROW_GROUPS-1][0:COLS-1];
    wire a_sign_rep [0:ROWS-1][0:COLS-1];
    wire [B_REP_BITS-1:0] b_low_rep [0:ROWS-1][0:COLS-1];

    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_a_common
            for (g = 0; g < COL_GROUPS; g = g + 1) begin : g_seg
                reg signed [A_COMMON_BITS-1:0] data_q;
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= a_edge[r][A_COMMON_BITS-1:0];
                            valid_q <= a_edge_valid[r];
                        end
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= a_common[r][g-1];
                            valid_q <= a_valid[r][g-1];
                        end
                    end
                end
                assign a_common[r][g] = data_q;
                assign a_valid[r][g] = valid_q;
            end
        end

        for (c = 0; c < COLS; c = c + 1) begin : g_b_common
            for (g = 0; g < ROW_GROUPS; g = g + 1) begin : g_seg
                reg signed [B_COMMON_BITS-1:0] data_q;
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= b_edge[c][PRECISION-1:B_REP_BITS];
                            valid_q <= b_edge_valid[c];
                        end
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= b_common[g-1][c];
                            valid_q <= b_valid[g-1][c];
                        end
                    end
                end
                assign b_common[g][c] = data_q;
                assign b_valid[g][c] = valid_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_a_rep
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                (* keep *) reg sign_q;
                always @(posedge clk) begin
                    if (rst || clear_acc)
                        sign_q <= (c % STRIDE);
                    else if (c < STRIDE)
                        sign_q <= a_edge[r][PRECISION-1];
                    else
                        sign_q <= a_sign_rep[r][c-STRIDE];
                end
                assign a_sign_rep[r][c] = sign_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_b_rep
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                (* keep *) reg [B_REP_BITS-1:0] low_q;
                always @(posedge clk) begin
                    if (rst || clear_acc)
                        low_q <= (r % STRIDE) ? {B_REP_BITS{1'b1}} : {B_REP_BITS{1'b0}};
                    else if (r < STRIDE)
                        low_q <= b_edge[c][B_REP_BITS-1:0];
                    else
                        low_q <= b_low_rep[r-STRIDE][c];
                end
                assign b_low_rep[r][c] = low_q;
            end
        end

        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                wire signed [PRECISION-1:0] a_operand = {
                    a_sign_rep[r][c], a_common[r][c/STRIDE]
                };
                wire signed [PRECISION-1:0] b_operand = {
                    b_common[r/STRIDE][c], b_low_rep[r][c]
                };
                wire signed [2*PRECISION-1:0] product = a_operand * b_operand;
                wire signed [ACC_WIDTH-1:0] extended = {
                    {(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product
                };
                reg signed [ACC_WIDTH-1:0] accumulator;
                always @(posedge clk) begin
                    if (rst || clear_acc)
                        accumulator <= 0;
                    else if (a_valid[r][c/STRIDE] && b_valid[r/STRIDE][c])
                        accumulator <= accumulator + extended;
                end
                assign acc_flat[(r*COLS+c)*ACC_WIDTH +: ACC_WIDTH] = accumulator;
            end
        end
    endgenerate
endmodule
