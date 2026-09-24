`timescale 1ns/1ps

// Transport stride S trades operand-network registers for bounded local fanout.
// Row/column edge skew makes both operands for PE(r,c) arrive in the same cycle:
// floor(r/S) + floor(c/S) + one group-register stage.
module kernellum_strided_mac_array #(
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

    wire signed [PRECISION-1:0] a_group [0:ROWS-1][0:COL_GROUPS-1];
    wire signed [PRECISION-1:0] b_group [0:ROW_GROUPS-1][0:COLS-1];
    wire a_valid [0:ROWS-1][0:COL_GROUPS-1];
    wire b_valid [0:ROW_GROUPS-1][0:COLS-1];

    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_a
            for (g = 0; g < COL_GROUPS; g = g + 1) begin : g_seg
                reg signed [PRECISION-1:0] data_q;
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= a_edge[r];
                            valid_q <= a_edge_valid[r];
                        end
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= a_group[r][g-1];
                            valid_q <= a_valid[r][g-1];
                        end
                    end
                end
                assign a_group[r][g] = data_q;
                assign a_valid[r][g] = valid_q;
            end
        end
        for (c = 0; c < COLS; c = c + 1) begin : g_b
            for (g = 0; g < ROW_GROUPS; g = g + 1) begin : g_seg
                reg signed [PRECISION-1:0] data_q;
                reg valid_q;
                if (g == 0) begin : first
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= b_edge[c];
                            valid_q <= b_edge_valid[c];
                        end
                    end
                end else begin : next
                    always @(posedge clk) begin
                        if (rst || clear_acc) begin
                            data_q <= 0;
                            valid_q <= 0;
                        end else begin
                            data_q <= b_group[g-1][c];
                            valid_q <= b_valid[g-1][c];
                        end
                    end
                end
                assign b_group[g][c] = data_q;
                assign b_valid[g][c] = valid_q;
            end
        end
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            for (c = 0; c < COLS; c = c + 1) begin : g_col
                reg signed [ACC_WIDTH-1:0] accumulator;
                wire signed [2*PRECISION-1:0] product =
                    a_group[r][c/STRIDE] * b_group[r/STRIDE][c];
                wire signed [ACC_WIDTH-1:0] extended =
                    {{(ACC_WIDTH-2*PRECISION){product[2*PRECISION-1]}}, product};
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
